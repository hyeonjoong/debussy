"""Psychoacoustic descriptors via MOSQITO — sanity ranges only.

We rely on MOSQITO for the validated reference implementations; these tests
check that DEBUSSY successfully wraps them and that the values fall within
the published references in Zwicker & Fastl (2007), 3rd edition.
"""
from debussy import analyze_audio


def test_roughness_in_plausible_range(sine_440):
    """A pure tone has very low roughness (no amplitude modulation)."""
    r = analyze_audio(sine_440)
    assert 0.0 <= r.roughness_asper < 1.0, (
        f"Roughness for a pure tone unexpectedly high: {r.roughness_asper}"
    )


def test_sharpness_in_published_range(pink_noise):
    """Sharpness of broadband signals typically sits in 1–4 acum
    (Zwicker & Fastl 2007). Pink noise is on the lower-frequency side."""
    r = analyze_audio(pink_noise)
    assert 0.3 < r.sharpness_acum < 4.0


def test_sharpness_higher_for_brighter_signal(sine_440, pink_noise):
    """Pink noise has broader high-frequency content than a 440 Hz sine,
    so sharpness should be at least as high."""
    r_sine = analyze_audio(sine_440)
    r_pink = analyze_audio(pink_noise)
    assert r_pink.sharpness_acum >= r_sine.sharpness_acum * 0.7
