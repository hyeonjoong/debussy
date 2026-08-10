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
import numpy as np
import pytest
import soundfile as sf

from debussy import analyze_audio

FS = 48000  # mosqito's native rate, so no resampling is involved


@pytest.fixture(scope="module")
def am_tone(tmp_path_factory):
    """300 Hz carrier, 70 Hz amplitude modulation — unambiguously rough.

    Daniel-Weber roughness peaks near 70 Hz modulation, so this signal must
    produce a finite roughness value on any working installation.
    """
    t = np.arange(int(FS * 3.0)) / FS
    y = 0.4 * (1 + 0.5 * np.sin(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 300 * t)
    path = tmp_path_factory.mktemp("psy") / "am_tone.wav"
    sf.write(path, np.clip(y, -1, 1).astype(np.float32), FS, subtype="PCM_16")
    return str(path)


def test_psychoacoustic_backend_is_functional(am_tone):
    """Regression guard: both psychoacoustic parameters must actually compute.

    The other tests in this module skip when mosqito returns None, which is the
    right call for adversarial inputs — but it also meant a broken backend went
    unnoticed. mosqito imports matplotlib inside roughness_dw and
    sharpness_din_st without declaring it, so a clean install missing matplotlib
    returned None for both parameters with no error surfaced to the caller,
    silently dropping two of the eleven reporting items.

    On a strongly modulated tone at mosqito's native rate there is no legitimate
    reason for either value to be undefined, so None here means the backend is
    broken rather than the input being degenerate.
    """
    r = analyze_audio(am_tone)
    assert "err" not in (r.notes or ""), f"psychoacoustic backend reported: {r.notes}"
    assert r.roughness_asper is not None, (
        "roughness is None on a 70 Hz AM tone — the mosqito backend is not working "
        f"(notes: {r.notes!r})"
    )
    assert r.sharpness_acum is not None, (
        "sharpness is None on a 70 Hz AM tone — the mosqito backend is not working "
        f"(notes: {r.notes!r})"
    )
    assert r.roughness_asper > 0.0
    assert r.sharpness_acum > 0.0


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
