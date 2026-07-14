"""Crest factor at the noise floor.

Crest factor is 20*log10(peak / rms). Near the −60 dBFS floor a naive ratio can
blow up to inf/NaN; the implementation must keep it finite and physically
plausible.
"""
from __future__ import annotations

import math

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


@pytest.fixture
def quiet_noise(tmp_path):
    fs = 48000
    rng = np.random.default_rng(7)
    y = rng.standard_normal(int(fs * 4))
    y = y / np.max(np.abs(y)) * (10 ** (-60 / 20))  # peak ≈ −60 dBFS
    p = tmp_path / "quiet.wav"
    sf.write(p, y.astype(np.float32), fs, subtype="FLOAT")  # FLOAT preserves tiny values
    return str(p)


def test_crest_factor_finite_at_noise_floor(quiet_noise):
    r = analyze_audio(quiet_noise)
    assert r.crest_factor_db is not None
    assert math.isfinite(r.crest_factor_db)
    # Gaussian noise sits around a 10–15 dB crest; allow a wide, sane window.
    assert 0.0 < r.crest_factor_db < 40.0
