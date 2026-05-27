"""Level descriptors on reference signals with known properties."""
from debussy import analyze_audio
from debussy.level import laeq_dbfs


def test_laeq_silence_is_very_low(silence):
    """A silent signal should yield a very low LAeq (well below the audible range)."""
    r = analyze_audio(silence)
    # silence ≈ −infinity dBFS in theory; the implementation should return
    # a very negative number, definitely lower than −100 dBFS-A
    assert r.laeq_dbfs_a < -90.0, f"LAeq for silence too high: {r.laeq_dbfs_a}"


def test_laeq_sine_is_in_plausible_range(sine_440):
    """A 440 Hz sine at 0.5 amplitude should sit around −9 to −5 dBFS-A
    (peak 0.5 → −6 dBFS, A-weighting near 0 dB at 1 kHz, slight attenuation at 440 Hz)."""
    r = analyze_audio(sine_440)
    assert -20.0 < r.laeq_dbfs_a < 0.0, f"LAeq for sine out of plausible range: {r.laeq_dbfs_a}"


def test_dynamic_range_is_nonnegative(pink_noise):
    """Dynamic range is p95 − p5 of short-term RMS, so it must be ≥ 0."""
    r = analyze_audio(pink_noise)
    assert r.dynamic_range_db >= 0


def test_crest_factor_pink_noise(pink_noise):
    """Crest factor of pink noise typically 10–14 dB. Allow a wide window."""
    r = analyze_audio(pink_noise)
    assert 6 < r.crest_factor_db < 25, f"Pink-noise crest factor out of range: {r.crest_factor_db}"
