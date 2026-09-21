"""Timing regularity separates stimuli that tempo and modulation rate cannot.

The case comes from Kyurim Kang's review of the tool: drum, metronome and
piano events laid out at 80 BPM, once isochronously and once with bounded
jitter around the same mean interval. Tempo and modulation peak frequency
return near-identical values for both, because both describe how fast events
recur rather than how evenly. The stimuli here are the same construction, so
the true interval variability is known and the measured value can be checked
against it rather than assumed.
"""
import numpy as np
import pytest

from debussy._core import modulation_peak, timing_regularity

SR = 22050
DUR = 30.0
BPM = 80.0
IOI = 60.0 / BPM                    # 0.75 s, rhythmic rate 1.333 Hz
JITTER = 0.35                       # uniform, as a fraction of the interval


def _click(sr=SR, dur_s=0.06, f=4000.0):
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    env = np.exp(-t * 120.0)
    return (np.sin(2 * np.pi * f * t) * env).astype(np.float64)


def _sequence(periodic, seed=0, sr=SR, dur=DUR):
    """Events at a mean interval of IOI; jittered when not periodic."""
    rng = np.random.default_rng(seed)
    hit = _click(sr)
    y = np.zeros(int(dur * sr) + len(hit))
    times, t = [], 0.0
    while t < dur - 0.3:
        k = int(t * sr)
        y[k:k + len(hit)] += hit
        times.append(t)
        t += IOI if periodic else IOI * (1 + rng.uniform(-JITTER, JITTER))
    y = y[:int(dur * sr)]
    iois = np.diff(times)
    true_cv = float(iois.std() / iois.mean())
    return (0.7 * y / (np.abs(y).max() + 1e-12)).astype(np.float32), true_cv


@pytest.fixture(scope="module")
def librosa_mod():
    return pytest.importorskip("librosa")


def test_isochronous_sequence_is_near_the_measurement_floor(librosa_mod):
    """A perfectly even sequence returns the floor, not exactly zero.

    Onsets are detected on frames, so intervals are quantised to the analysis
    hop. The floor is a property of the measurement and is documented as such.
    """
    y, _ = _sequence(periodic=True)
    r = timing_regularity(y, SR, librosa_mod)

    assert r["ioi_cv"] is not None
    assert r["ioi_cv"] < 0.05
    assert r["npvi"] < 5.0
    assert r["ioi_median_s"] == pytest.approx(IOI, abs=0.03)


@pytest.mark.parametrize("seed", [101, 202, 303])
def test_jitter_is_recovered_not_merely_detected(seed, librosa_mod):
    """The measured coefficient of variation matches the constructed one.

    Detecting that something is irregular is weaker than measuring how
    irregular it is; the second is what makes the number usable for comparing
    conditions, so that is what is asserted.
    """
    y, true_cv = _sequence(periodic=False, seed=seed)
    r = timing_regularity(y, SR, librosa_mod)

    assert r["ioi_cv"] == pytest.approx(true_cv, abs=0.04)
    assert r["npvi"] > 10.0


def test_separates_what_tempo_and_modulation_rate_cannot(librosa_mod):
    """The reason these descriptors were added.

    Both sequences are built to the same mean tempo, so the modulation peak
    lands at a similar rate for both. Regularity has to come from the
    intervals themselves.
    """
    per, _ = _sequence(periodic=True)
    ape, _ = _sequence(periodic=False, seed=202)

    r_per = timing_regularity(per, SR, librosa_mod)
    r_ape = timing_regularity(ape, SR, librosa_mod)
    assert r_ape["ioi_cv"] > 5 * r_per["ioi_cv"]
    assert r_ape["npvi"] > 5 * r_per["npvi"]

    m_per = modulation_peak(per, SR)
    m_ape = modulation_peak(ape, SR)
    assert abs(m_per["peak_hz"] - m_ape["peak_hz"]) < 0.5
    assert m_per["prominence_db"] > m_ape["prominence_db"] + 10.0


def test_too_few_events_returns_none(librosa_mod):
    """Two events give one interval, which is not a variability."""
    sr, hit = SR, _click()
    y = np.zeros(int(3.0 * sr))
    for t in (0.5, 1.5):
        k = int(t * sr)
        y[k:k + len(hit)] += hit
    r = timing_regularity(y.astype(np.float32), sr, librosa_mod)
    assert r["ioi_cv"] is None and r["npvi"] is None


def test_silence_reports_no_modulation_rate(librosa_mod):
    """An all-zero band has an argmax, and it is not a modulation rate.

    Before prominence was reported this returned the frequency of the first
    bin for silence, which looked like a measurement.
    """
    silence = np.zeros(int(SR * 5), dtype=np.float32)

    assert timing_regularity(silence, SR, librosa_mod)["ioi_cv"] is None

    m = modulation_peak(silence, SR)
    assert m["peak_hz"] is None and m["prominence_db"] is None

    # A constant signal is not silence: the analytic envelope has edge
    # artefacts, so a peak frequency still comes out. Prominence is what says
    # it means nothing, and it is the reason the number is reported.
    dc = modulation_peak(np.full(int(SR * 5), 0.5, dtype=np.float32), SR)
    assert dc["prominence_db"] < 3.0
