"""Tempo is reported only for material that has one.

The signals here are synthesised, so the answer is fixed by construction rather
than assumed from a genre tag. That matters: the public tempo-estimation
benchmarks annotate a wide range of tempi but contain almost no material with
no tempo at all, which is precisely the class a withholding rule has to get
right.

Two failure modes have to be caught, and they are not the same failure:

* sustained tones, chords and slow swells contain almost no spectral change,
  so there is nothing for a tempo to organise, yet their near-empty onset
  envelope still produces a well-formed tempogram peak;
* broadband noise contains abundant spectral change with no periodicity, so
  any rule based on onset activity alone admits it.

No single statistic computed from one onset envelope separates both from real
pulse while leaving annotated music alone. Onset density is actively
misleading, scoring noise above music; autocorrelation peak prominence,
tempogram contrast and onset flux each reject 87 per cent or more of the
annotated GTZAN tracks at any threshold that also rejects the signals below.
Committee agreement does separate them, which is why it is what ships.
"""
import numpy as np
import pytest

from debussy._core import (
    BEAT_AGREEMENT_REFERENCE,
    ONSET_FLUX_REFERENCE,
    beat_agreement,
    onset_flux,
    tempo_bpm,
)

SR = 22050
DUR = 30.0   # the validated range starts at 15 s; GTZAN excerpts are 30 s


def _t(dur=None):
    return np.arange(int(SR * (DUR if dur is None else dur))) / SR


def _clicks(bpm, jitter=0.0, seed=0, dur=None):
    dur = DUR if dur is None else dur
    rng = np.random.default_rng(seed)
    y = np.zeros(int(SR * dur))
    period = 60.0 / bpm
    pos = 0.0
    while pos < dur - 0.05:
        k = int(pos * SR)
        y[k:k + 220] += np.hanning(220)
        pos += period * (1.0 + rng.normal(0, jitter))
    return y.astype(np.float32)


def _noise(order, seed=0, dur=None):
    """order 0 = white, 1 = pink-ish, 2 = brown."""
    from scipy.signal import lfilter

    dur = DUR if dur is None else dur
    rng = np.random.default_rng(seed)
    y = rng.standard_normal(int(SR * dur))
    for _ in range(order):
        y = lfilter([1.0], [1.0, -0.99], y)
    return (0.3 * y / (np.abs(y).max() + 1e-12)).astype(np.float32)


BEATLESS = {
    "sustained tone": lambda: (0.3 * np.sin(2 * np.pi * 220 * _t())).astype(np.float32),
    "sustained chord": lambda: (0.1 * sum(
        np.sin(2 * np.pi * f * _t()) for f in (220, 277, 330))).astype(np.float32),
    "white noise": lambda: _noise(0),
    "pink noise": lambda: _noise(1, seed=1),
    "brown noise": lambda: _noise(2, seed=2),
    "breath-rate modulation": lambda: (
        0.3 * np.sin(2 * np.pi * 220 * _t()) * (1 + 0.9 * np.sin(2 * np.pi * 0.2 * _t()))
    ).astype(np.float32),
    "slow swell": lambda: (
        0.3 * np.sin(2 * np.pi * 220 * _t()) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * _t()))
    ).astype(np.float32),
    "silence": lambda: np.zeros(int(SR * DUR), dtype=np.float32),  # noqa: E501
}

BEATED = {
    "clicks 60 BPM": lambda: _clicks(60),
    "clicks 90 BPM": lambda: _clicks(90),
    "clicks 120 BPM": lambda: _clicks(120),
    "clicks 150 BPM": lambda: _clicks(150),
    "clicks 120 BPM, 8% jitter": lambda: _clicks(120, jitter=0.08, seed=4),
    "clicks 90 BPM, 15% jitter": lambda: _clicks(90, jitter=0.15, seed=5),
    "kick pattern 100 BPM": lambda: (
        _clicks(100, seed=7) * (1 + 0.5 * np.sin(2 * np.pi * 50 * _t()))
    ).astype(np.float32),
}


@pytest.fixture(scope="module")
def librosa_mod():
    return pytest.importorskip("librosa")


@pytest.mark.parametrize("name", sorted(BEATLESS))
def test_no_tempo_for_beatless_material(name, librosa_mod):
    y = BEATLESS[name]()
    agree = beat_agreement(y, SR, librosa_mod)
    flux = onset_flux(y, SR, librosa_mod)
    assert tempo_bpm(y, SR, librosa_mod, agreement=agree, flux=flux) is None, (
        f"{name}: reported a tempo; agreement={agree}, flux={flux}"
    )


@pytest.mark.parametrize("name", sorted(BEATED))
def test_tempo_survives_for_pulsed_material(name, librosa_mod):
    y = BEATED[name]()
    agree = beat_agreement(y, SR, librosa_mod)
    flux = onset_flux(y, SR, librosa_mod)
    bpm = tempo_bpm(y, SR, librosa_mod, agreement=agree, flux=flux)
    assert bpm is not None, (
        f"{name}: tempo withheld; agreement={agree}, flux={flux}"
    )
    assert 30.0 <= bpm <= 300.0


@pytest.mark.parametrize("gain_db", [-40, -20, 0, 12, 24])
def test_level_invariance(gain_db, librosa_mod):
    """Playback level must not decide whether a tempo is reported.

    The onset envelope is a difference of log-magnitude spectra and carries no
    level dependence of its own; normalising it by signal RMS would put one
    back, so that a loud click train would lose its tempo.
    """
    y = (BEATED["clicks 120 BPM"]() * 10 ** (gain_db / 20)).astype(np.float32)
    assert tempo_bpm(y, SR, librosa_mod,
                     agreement=beat_agreement(y, SR, librosa_mod),
                     flux=onset_flux(y, SR, librosa_mod)) is not None

    q = (BEATLESS["white noise"]() * 10 ** (gain_db / 20)).astype(np.float32)
    assert tempo_bpm(q, SR, librosa_mod,
                     agreement=beat_agreement(q, SR, librosa_mod),
                     flux=onset_flux(q, SR, librosa_mod)) is None


@pytest.mark.parametrize("fs", [16000, 22050, 44100, 48000])
def test_sample_rate_invariance(fs, librosa_mod):
    """The same signal must give the same verdict at any input rate.

    librosa's onset envelope uses a hop length fixed in samples, so the
    statistics are computed after resampling to a fixed internal rate.
    """
    dur = 30.0
    t = np.arange(int(fs * dur)) / fs
    width = int(0.01 * fs)
    y = np.zeros_like(t)
    for k in range(0, len(t), int(fs * 0.5)):      # 120 BPM
        y[k:k + width] = np.hanning(width)
    y = y.astype(np.float32)
    assert tempo_bpm(y, fs, librosa_mod,
                     agreement=beat_agreement(y, fs, librosa_mod),
                     flux=onset_flux(y, fs, librosa_mod)) is not None


def test_degenerate_input_is_withheld(librosa_mod):
    """Silence and DC carry no tempo and must not be given one."""
    for y in (np.zeros(int(SR * 30), dtype=np.float32),
              np.full(int(SR * 30), 0.5, dtype=np.float32)):
        assert tempo_bpm(y, SR, librosa_mod,
                         agreement=beat_agreement(y, SR, librosa_mod),
                         flux=onset_flux(y, SR, librosa_mod)) is None


def test_both_conditions_are_load_bearing(librosa_mod):
    """Neither condition alone rejects the whole beatless class.

    Broadband noise has ample onset flux and fails only on agreement. A tone
    under slow amplitude modulation has the opposite profile: every committee
    member locks onto the same swell, so they agree with each other while
    agreeing about nothing in the signal, and only the flux condition catches
    it. A rule using either alone admits one of the two.
    """
    noise = BEATLESS["white noise"]()
    swell = BEATLESS["slow swell"]()

    assert onset_flux(noise, SR, librosa_mod) >= ONSET_FLUX_REFERENCE
    assert beat_agreement(noise, SR, librosa_mod) < BEAT_AGREEMENT_REFERENCE

    assert onset_flux(swell, SR, librosa_mod) < ONSET_FLUX_REFERENCE
    assert beat_agreement(swell, SR, librosa_mod) >= BEAT_AGREEMENT_REFERENCE


@pytest.mark.parametrize("dur", [15.0, 30.0, 45.0, 60.0])
def test_rule_holds_across_excerpt_lengths(dur, librosa_mod):
    """Both classes stay on the correct side from 15 s upward.

    Agreement on its own is not length-stable: the slow swell crosses the
    agreement reference at some lengths and not others. The flux condition is
    what makes the pair stable, which is the reason it is there.
    """
    global DUR
    prev, DUR = DUR, dur
    try:
        for name, make in BEATLESS.items():
            y = make()
            assert tempo_bpm(y, SR, librosa_mod,
                             agreement=beat_agreement(y, SR, librosa_mod),
                             flux=onset_flux(y, SR, librosa_mod)) is None, \
                f"{name} at {dur}s"
        for name, make in BEATED.items():
            y = make()
            assert tempo_bpm(y, SR, librosa_mod,
                             agreement=beat_agreement(y, SR, librosa_mod),
                             flux=onset_flux(y, SR, librosa_mod)) is not None, \
                f"{name} at {dur}s"
    finally:
        DUR = prev


def test_raw_estimate_still_available(librosa_mod):
    """Passing agreement=None returns the unchecked estimate.

    The beat tracker does return a number for a sustained tone. The point of the
    check is that the number is an artefact, not that it cannot be obtained.
    """
    y = BEATLESS["sustained tone"]()
    assert tempo_bpm(y, SR, librosa_mod, agreement=None, flux=None) is not None
