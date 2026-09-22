"""MPEG-1 Psychoacoustic Model 1, checked against published psychoacoustics.

The standard's conformance vectors are not public, so none of this asserts
bit-exactness against the reference decoder. What it does assert is every
published quantity the model is built from, and every qualitative property
it must have to be a masking model at all. A model that passed only the
qualitative checks could still be miscalibrated; one that passed only the
numeric checks could still spread masking the wrong way. Together they
constrain it from both sides.

One of these caught a real error during development: the level normalisation
was 3 dB high, which matters because the spreading function is
level-dependent, so every masked threshold would have been wrong.
"""
import numpy as np
import pytest

from debussy.masking import (
    CRITICAL_BAND_EDGES_HZ,
    FULL_SCALE_SPL_DB,
    MODEL_NFFT,
    MODEL_SR,
    _maskers,
    _power_spectrum_db,
    absolute_threshold_db,
    global_masking_threshold_db,
    hz_to_bark,
    spreading_db,
)

BIN_HZ = MODEL_SR / MODEL_NFFT
T = np.arange(MODEL_NFFT) / MODEL_SR
FREQS = np.fft.rfftfreq(MODEL_NFFT, 1.0 / MODEL_SR)


def tone(bin_index, amplitude=0.7):
    """A sine centred on an FFT bin, so no scalloping loss enters."""
    return amplitude * np.sin(2 * np.pi * bin_index * BIN_HZ * T)


# ---------------------------------------------------------------- published

def test_absolute_threshold_matches_terhardt_at_1khz():
    """The Terhardt approximation evaluates to 3.37 dB SPL at 1 kHz."""
    assert float(absolute_threshold_db(np.array([1000.0]))[0]) == pytest.approx(
        3.37, abs=0.01)


def test_absolute_threshold_is_most_sensitive_near_3_to_4_khz():
    """Hearing is most sensitive around 3-4 kHz, and the threshold is negative there."""
    f = np.arange(100.0, 16000.0, 5.0)
    a = absolute_threshold_db(f)
    assert 3000.0 <= f[a.argmin()] <= 4000.0
    assert a.min() < 0.0
    # and rises at both ends
    assert absolute_threshold_db(np.array([100.0]))[0] > 15.0
    assert absolute_threshold_db(np.array([15000.0]))[0] > 15.0


def test_bark_scale_reproduces_zwickers_band_edges():
    """Each tabulated critical-band edge should land on a whole Bark.

    The analytic formula approximates the table, so a fifth of a Bark of
    disagreement is expected; more than that would mean the wrong formula.
    """
    edges = CRITICAL_BAND_EDGES_HZ[1:-1]
    err = np.abs(hz_to_bark(edges) - np.arange(1, len(edges) + 1))
    assert err.max() < 0.25
    assert np.median(err) < 0.15


def test_full_scale_sine_reads_the_reference_level():
    """A bin-centred full-scale sine defines the level reference."""
    assert _power_spectrum_db(tone(43, amplitude=1.0)).max() == pytest.approx(
        FULL_SCALE_SPL_DB, abs=0.01)


def test_off_bin_sine_loses_only_scalloping():
    """A sine between bins reads lower, by no more than the Hann scalloping loss."""
    peak = _power_spectrum_db(np.sin(2 * np.pi * 1000.0 * T)).max()
    assert FULL_SCALE_SPL_DB - 1.5 < peak < FULL_SCALE_SPL_DB


def test_level_scales_decibel_for_decibel():
    for db in (-40.0, -20.0, -6.0):
        peak = _power_spectrum_db(tone(43, amplitude=10 ** (db / 20))).max()
        assert peak == pytest.approx(FULL_SCALE_SPL_DB + db, abs=0.02)


# ------------------------------------------------------------- spreading fn

@pytest.mark.parametrize("breakpoint", [-1.0, 0.0, 1.0])
def test_spreading_function_is_continuous(breakpoint):
    """The four branches must meet, or thresholds jump at Bark boundaries."""
    lo = float(spreading_db(np.array([breakpoint - 1e-9]), 60.0)[0])
    hi = float(spreading_db(np.array([breakpoint + 1e-9]), 60.0)[0])
    assert lo == pytest.approx(hi, abs=1e-6)


def test_masking_spreads_further_upward_than_downward():
    """Upward spread of masking: the defining asymmetry of the phenomenon."""
    up = float(spreading_db(np.array([2.0]), 60.0)[0])
    down = float(spreading_db(np.array([-2.0]), 60.0)[0])
    assert up > down


def test_upward_spread_widens_with_masker_level():
    """Louder maskers reach further up in frequency."""
    at_4_bark = [float(spreading_db(np.array([4.0]), lvl)[0])
                 for lvl in (40.0, 60.0, 80.0)]
    assert at_4_bark[0] < at_4_bark[1] < at_4_bark[2]


def test_spreading_peaks_at_the_masker():
    dz = np.linspace(-2.9, 7.9, 400)
    s = spreading_db(dz, 60.0)
    assert dz[int(np.argmax(s))] == pytest.approx(0.0, abs=0.05)


# ------------------------------------------------------------------ maskers

def _tonal_power_share(y):
    spl = _power_spectrum_db(y)
    tonal, noise = _maskers(spl, FREQS)
    pt = sum(10 ** (x / 10) for _, x in tonal)
    pn = sum(10 ** (x / 10) for _, x in noise)
    return pt / (pt + pn + 1e-30)


def test_a_tone_is_classified_tonal():
    spl = _power_spectrum_db(tone(43))
    tonal, _ = _maskers(spl, FREQS)
    assert len(tonal) >= 1
    assert min(abs(f - 43 * BIN_HZ) for f, _ in tonal) < BIN_HZ
    assert _tonal_power_share(tone(43)) > 0.95


def test_noise_is_classified_non_tonal():
    """Counting maskers is the wrong test; noise throws up spurious peaks.

    What has to hold is that almost none of the masking power is tonal.
    """
    rng = np.random.default_rng(0)
    assert _tonal_power_share(0.3 * rng.standard_normal(MODEL_NFFT)) < 0.25


def test_a_chord_is_tonal():
    chord = 0.7 * sum(tone(k, 1.0) for k in (11, 22, 43)) / 3
    assert _tonal_power_share(chord) > 0.95


# ------------------------------------------------------------------ masking

def test_silence_gives_back_the_threshold_in_quiet():
    """With nothing to mask with, the global threshold is the absolute one."""
    g = global_masking_threshold_db(np.zeros(MODEL_NFFT))
    assert np.abs(g - absolute_threshold_db(FREQS)).max() < 1e-9


def test_a_masker_raises_the_threshold_beside_it():
    i_1200 = int(np.argmin(np.abs(FREQS - 1200.0)))
    quiet = float(absolute_threshold_db(np.array([FREQS[i_1200]]))[0])
    with_masker = float(global_masking_threshold_db(tone(11))[i_1200])
    assert with_masker > quiet + 30.0


def test_a_masker_leaves_distant_frequencies_alone():
    """Masking is local: a 1 kHz tone does not mask 10 kHz."""
    i_10k = int(np.argmin(np.abs(FREQS - 10000.0)))
    quiet = float(absolute_threshold_db(np.array([FREQS[i_10k]]))[0])
    with_masker = float(global_masking_threshold_db(tone(11))[i_10k])
    assert with_masker == pytest.approx(quiet, abs=1.0)


def test_masked_threshold_is_monotone_in_masker_level():
    i_1200 = int(np.argmin(np.abs(FREQS - 1200.0)))
    levels = [float(global_masking_threshold_db(
        tone(11, amplitude=10 ** (db / 20)))[i_1200])
        for db in (-40.0, -30.0, -20.0, -10.0, 0.0)]
    assert all(b > a for a, b in zip(levels, levels[1:]))
    # and tracks the masker roughly decibel for decibel
    steps = np.diff(levels)
    assert np.all((steps > 8.0) & (steps < 12.0))


def test_threshold_never_falls_below_the_threshold_in_quiet():
    """Adding maskers can only raise the threshold, never lower it."""
    rng = np.random.default_rng(3)
    for sig in (tone(43), 0.3 * rng.standard_normal(MODEL_NFFT),
                np.zeros(MODEL_NFFT)):
        assert np.all(global_masking_threshold_db(sig)
                      >= absolute_threshold_db(FREQS) - 1e-9)


def test_degenerate_input_is_handled():
    for sig in (np.zeros(MODEL_NFFT), np.full(MODEL_NFFT, 0.5)):
        g = global_masking_threshold_db(sig)
        assert g.shape == FREQS.shape
        assert np.all(np.isfinite(g))
