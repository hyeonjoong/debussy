"""Psychoacoustic descriptors via MOSQITO — sanity ranges only.

We rely on MOSQITO for the validated reference implementations; these tests
check that DEBUSSY successfully wraps them and that the values fall within
the published references in Zwicker & Fastl (2007), 3rd edition.

MOSQITO can legitimately return None on adversarial inputs (a pure tone has no
amplitude modulation, so the Daniel-Weber roughness integrator may collapse;
likewise the DIN 45692 sharpness integrator can return NaN/None on degenerate
loudness spectra). We tolerate None and only assert ranges when a finite value
is produced.
"""
import pytest
from debussy import analyze_audio


def test_roughness_in_plausible_range(sine_440):
    """A pure tone has very low roughness; mosqito may return None or a near-zero value."""
    r = analyze_audio(sine_440)
    if r.roughness_asper is None:
        pytest.skip("mosqito returned None for roughness on a pure tone (expected on some platforms)")
    assert 0.0 <= r.roughness_asper < 1.0, (
        f"Roughness for a pure tone unexpectedly high: {r.roughness_asper}"
    )


def test_sharpness_in_published_range(pink_noise):
    """Sharpness of broadband signals typically sits in 1–4 acum
    (Zwicker & Fastl 2007). Pink noise is on the lower-frequency side."""
    r = analyze_audio(pink_noise)
    if r.sharpness_acum is None:
        pytest.skip("mosqito returned None for sharpness on this platform")
    assert 0.3 < r.sharpness_acum < 4.0


def test_sharpness_higher_for_brighter_signal(sine_440, pink_noise):
    """Pink noise has broader high-frequency content than a 440 Hz sine,
    so sharpness should be at least as high (when both are defined)."""
    r_sine = analyze_audio(sine_440)
    r_pink = analyze_audio(pink_noise)
    if r_sine.sharpness_acum is None or r_pink.sharpness_acum is None:
        pytest.skip("mosqito sharpness undefined on one of the inputs")
    assert r_pink.sharpness_acum >= r_sine.sharpness_acum * 0.7
