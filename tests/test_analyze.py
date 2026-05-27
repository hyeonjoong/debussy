"""End-to-end: analyze_audio() returns a complete Result on a clean sine."""
from debussy import analyze_audio, Result


def test_analyze_returns_result(sine_440):
    r = analyze_audio(sine_440)
    assert isinstance(r, Result)


def test_analyze_all_parameters_present(sine_440):
    r = analyze_audio(sine_440)
    # The 11 paper-aligned parameters must all be present as attributes
    for attr in (
        "laeq_dbfs_a", "dynamic_range_db", "crest_factor_db",
        "attack_mean_ms", "attack_median_ms", "attack_sd_ms",
        "roughness_asper",
        "tempo_bpm", "modulation_peak_hz",
        "spectral_centroid_hz", "sharpness_acum",
        "spectral_slope_beta",
        "hnr_db", "spectral_flatness",
    ):
        assert hasattr(r, attr), f"Result missing attribute: {attr}"
    # Level/spectral/tonal metrics are well-defined on any non-silent signal
    for attr in ("laeq_dbfs_a", "dynamic_range_db", "crest_factor_db",
                 "spectral_centroid_hz", "spectral_slope_beta",
                 "hnr_db", "spectral_flatness"):
        assert getattr(r, attr) is not None, f"{attr} should be finite for a non-silent sine"
    # Psychoacoustic and beat-tracking metrics may legitimately be None on
    # adversarial inputs (a pure tone has no amplitude modulation so mosqito's
    # roughness can return None; sharpness can be None when loudness integration
    # collapses; modulation peak / tempo are not well-defined on pure tones).
    # We tolerate None here and assert numeric ranges only in the family-specific tests.


def test_analyze_runtime_metadata(sine_440):
    r = analyze_audio(sine_440)
    assert r.duration_s > 0
    assert r.sample_rate in (44100, 48000)
    assert r.file.endswith("sine_440.wav")
