"""End-to-end: analyze_audio() returns a complete Result on a clean sine."""
from debussy import analyze_audio, Result


def test_analyze_returns_result(sine_440):
    r = analyze_audio(sine_440)
    assert isinstance(r, Result)


def test_analyze_all_parameters_present(sine_440):
    r = analyze_audio(sine_440)
    # The 11 paper-aligned parameters must all be present
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
        value = getattr(r, attr)
        assert value is not None or attr in ("modulation_peak_hz", "tempo_bpm"), \
            f"Parameter {attr} should not be None for a non-silent sine"


def test_analyze_runtime_metadata(sine_440):
    r = analyze_audio(sine_440)
    assert r.duration_s > 0
    assert r.sample_rate in (44100, 48000)
    assert r.file.endswith("sine_440.wav")
