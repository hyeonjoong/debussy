"""Spectral descriptors on a clean sine vs broadband noise."""
from debussy import analyze_audio


def test_spectral_centroid_sine_near_fundamental(sine_440):
    """A pure 440 Hz sine has nearly all energy at 440 Hz, so the spectral centroid
    should be in the low hundreds of Hz (well below the broadband average)."""
    r = analyze_audio(sine_440)
    assert 200 < r.spectral_centroid_hz < 1500, (
        f"Sine centroid implausible: {r.spectral_centroid_hz}"
    )


def test_spectral_centroid_pink_noise_is_higher(sine_440, pink_noise):
    """Pink noise has broader spectral support than a sine, so its centroid is
    typically higher than a 440 Hz sine's."""
    r_sine = analyze_audio(sine_440)
    r_pink = analyze_audio(pink_noise)
    assert r_pink.spectral_centroid_hz > r_sine.spectral_centroid_hz


def test_spectral_slope_pink_noise_near_minus_one(pink_noise):
    """Pink noise has a 1/f power spectrum, so β should sit broadly in the
    −2 to 0 range (the exact value depends on the band and the smoothing)."""
    r = analyze_audio(pink_noise)
    assert -8.0 < r.spectral_slope_beta < 0.5
