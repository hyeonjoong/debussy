"""Events cut off rather than faded leave a click, and the click is an onset.

From stimuli sent by Kyurim Kang. Each rendered drum and piano event ended in
a step straight to digital silence, at -32 and -20 dB relative to peak. The
step is broadband, so it was detected as a second onset per event: an
isochronous sequence returned twice the true event count and a coefficient of
variation of 0.52 where the constructed value was zero. The metronome events
in the same set were cut in the same way but had decayed to -62 dB first, so
there was no click and no spurious onset.

The stimuli here reproduce that construction, so the expected click count is
fixed by how the signal is built.
"""
import numpy as np
import pytest

from debussy._core import (
    TRUNCATION_FLOOR_DB,
    timing_regularity,
    truncation_clicks,
)

SR = 22050
IOI = 0.75
N_EVENTS = 20
F0 = 220.0


def _event(cut_level, fade_ms=0.0, dur_target=0.30, sr=SR):
    """A percussive event truncated while still at `cut_level` of its peak.

    The broadband attack matters: a pure tone cut at the same level does not
    reproduce the effect, because the detector needs the spectral flux of a
    real attack to lock onto the events in the first place. The duration is
    adjusted so the last sample sits on a crest of the carrier, otherwise the
    cut can land on a zero crossing and there is no step to detect.
    """
    k = round(dur_target * F0 - 0.25)
    dur = (k + 0.25) / F0
    n = int(round(dur * sr))
    t = np.arange(n) / sr
    tau = -dur / np.log(cut_level)
    rng = np.random.default_rng(3)
    attack = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.6
    y = (np.sin(2 * np.pi * F0 * t) + attack) * np.exp(-t / tau)
    if fade_ms > 0:
        m = min(int(fade_ms / 1000 * sr), n)
        y[n - m:] *= np.linspace(1.0, 0.0, m)
    return y


def _sequence(cut_level, fade_ms=0.0, sr=SR):
    ev = _event(cut_level, fade_ms=fade_ms, sr=sr)
    y = np.zeros(int(N_EVENTS * IOI * sr) + len(ev))
    for k in range(N_EVENTS):
        i = int(k * IOI * sr)
        y[i:i + len(ev)] += ev
    return (0.7 * y / (np.abs(y).max() + 1e-12)).astype(np.float32)


@pytest.fixture(scope="module")
def librosa_mod():
    return pytest.importorskip("librosa")


def test_audible_cut_is_counted_once_per_event():
    """One click per event, and the step is reported above the floor."""
    y = _sequence(cut_level=0.1)          # the piano case
    r = truncation_clicks(y, SR)

    assert r["n"] == N_EVENTS
    assert r["max_step_db"] > TRUNCATION_FLOOR_DB


def test_cut_below_the_floor_is_not_counted():
    """A cut that has already decayed to inaudibility is not an artefact.

    This is the metronome case, and it is why the test is on the level at the
    cut rather than on the presence of a cut.
    """
    y = _sequence(cut_level=10 ** (-62.0 / 20.0))
    assert truncation_clicks(y, SR)["n"] == 0


def test_fading_removes_it():
    """The fix, asserted rather than only recommended."""
    assert truncation_clicks(_sequence(cut_level=0.1, fade_ms=5.0), SR)["n"] == 0


@pytest.mark.parametrize("db", [-20.0, -30.0, -37.0])
def test_audible_cuts_across_levels_are_caught(db):
    y = _sequence(cut_level=10 ** (db / 20.0))
    assert truncation_clicks(y, SR)["n"] == N_EVENTS


@pytest.mark.parametrize("db", [-53.0, -62.0])
def test_inaudible_cuts_are_left_alone(db):
    y = _sequence(cut_level=10 ** (db / 20.0))
    assert truncation_clicks(y, SR)["n"] == 0


def test_clicks_corrupt_timing_regularity(librosa_mod):
    """Why this check exists next to the timing statistics.

    Both sequences are isochronous by construction. The truncated one reports
    an inflated coefficient of variation because each click is a real onset
    between two real onsets.
    """
    cut = _sequence(cut_level=0.1)
    faded = _sequence(cut_level=0.1, fade_ms=5.0)

    r_cut = timing_regularity(cut, SR, librosa_mod)
    r_faded = timing_regularity(faded, SR, librosa_mod)

    assert truncation_clicks(cut, SR)["n"] == N_EVENTS
    assert truncation_clicks(faded, SR)["n"] == 0
    assert r_faded["ioi_cv"] < 0.05
    assert r_faded["npvi"] < 5.0
    assert r_cut["ioi_cv"] > 5 * r_faded["ioi_cv"]
    assert r_cut["npvi"] > 5 * r_faded["npvi"]


def test_continuous_audio_is_not_flagged():
    """No false positive on material that never reaches digital silence."""
    rng = np.random.default_rng(0)
    y = (0.3 * rng.standard_normal(int(5 * SR))).astype(np.float32)
    assert truncation_clicks(y, SR)["n"] == 0

    assert truncation_clicks(np.zeros(int(SR), dtype=np.float32), SR)["n"] == 0
