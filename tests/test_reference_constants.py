"""The screening constants must be the only definition of their own numbers.

``_core`` states that the reference values are named constants "so that a
protocol needing different limits can state its own, and so that a future
revision of the review changes one line each". That promise only holds if every
metric derived from a reference value reads the constant instead of repeating
the literal. These tests re-point a constant and assert the derived quantity
follows; a duplicated literal fails them.
"""
from __future__ import annotations

import os

import numpy as np
import pytest
import soundfile as sf

from debussy import _core, coverage_items

FS = 48000  # mosqito-friendly, so roughness needs no resampling


@pytest.fixture(scope="module")
def rough_tone():
    """2 s of 70 Hz amplitude modulation — high Daniel-Weber roughness
    throughout, so coverage against the default reference value is non-zero."""
    t = np.arange(int(FS * 2)) / FS
    mod = 0.5 * (1 + np.sin(2 * np.pi * 70 * t))
    return (0.4 * np.sin(2 * np.pi * 300 * t) * mod).astype(np.float64)


@pytest.fixture(scope="module")
def click_signal(tmp_path_factory):
    """120 BPM click train — every onset rises within a few ms, so all of them
    sit below the 50 ms reference value and none below 0 ms."""
    n = int(FS * 4)
    y = np.zeros(n, dtype=np.float32)
    width = int(FS * 0.005)
    for i in range(0, n - width, int(FS * 0.5)):
        y[i:i + width] = 0.7
    path = os.path.join(tmp_path_factory.mktemp("refconst"), "clicks.wav")
    sf.write(path, y, FS, subtype="PCM_16")
    return y.astype(np.float64)


def test_sharp_onset_share_follows_the_attack_constant(monkeypatch, click_signal):
    """The sharp-onset share is counted against ATTACK_REFERENCE_MS."""
    import librosa

    att = _core.attack_times_ms(click_signal, FS, librosa)
    assert att["frac_below_reference_ms"] == 100.0, "clicks should all be sharp at 50 ms"

    # No attack time can be below zero, so the share must collapse to 0 %.
    monkeypatch.setattr(_core, "ATTACK_REFERENCE_MS", 0.0)
    att = _core.attack_times_ms(click_signal, FS, librosa)
    assert att["frac_below_reference_ms"] == 0.0
    assert att["n_below_reference_ms"] == 0


def test_roughness_coverage_follows_the_roughness_constant(monkeypatch, rough_tone):
    """Coverage is the share of time above ROUGHNESS_REFERENCE_ASPER."""
    psy = _core.psychoacoustics(rough_tone, FS, suppress_warnings=True)
    if psy["roughness_coverage_pct"] is None:
        pytest.skip(f"mosqito roughness unavailable: {psy.get('_roughness_err')}")
    assert psy["roughness_coverage_pct"] > 0.0, "70 Hz AM should read as rough"

    # Nothing is rougher than 1000 asper, so coverage must collapse to 0 %.
    monkeypatch.setattr(_core, "ROUGHNESS_REFERENCE_ASPER", 1000.0)
    psy = _core.psychoacoustics(rough_tone, FS, suppress_warnings=True)
    assert psy["roughness_coverage_pct"] == 0.0


def test_coverage_items_quote_the_constants(monkeypatch, sine_440):
    """The rendered reference column is built from the constants, not retyped."""
    from debussy import analyze_audio

    r = analyze_audio(sine_440)
    monkeypatch.setattr(_core, "ROUGHNESS_REFERENCE_ASPER", 0.42)
    monkeypatch.setattr(_core, "ATTACK_REFERENCE_MS", 17.0)

    rendered = {it["parameter"]: it["threshold"] for it in coverage_items(r)}
    assert "0.42" in rendered["Roughness coverage"]
    assert "17" in rendered["Sharp-onset share"]
