"""calibration_offset_db propagation.

Digital audio carries no absolute SPL, so LAeq is reported in dBFS-A. A
calibration offset must add *directly* to LAeq and leave every other metric
untouched.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


@pytest.fixture
def tone(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 4)) / fs
    y = 0.4 * np.sin(2 * np.pi * 300 * t)
    p = tmp_path / "tone.wav"
    sf.write(p, y.astype(np.float32), fs, subtype="PCM_16")
    return str(p)


def test_offset_adds_to_laeq(tone):
    base = analyze_audio(tone)
    cal = analyze_audio(tone, calibration_offset_db=12.5)
    assert abs((cal.laeq_dbfs_a - base.laeq_dbfs_a) - 12.5) < 0.05


def test_offset_leaves_other_metrics_unchanged(tone):
    base = analyze_audio(tone)
    cal = analyze_audio(tone, calibration_offset_db=12.5)
    assert cal.spectral_centroid_hz == base.spectral_centroid_hz
    assert cal.dynamic_range_db == base.dynamic_range_db
    assert cal.crest_factor_db == base.crest_factor_db


def test_zero_offset_is_noop(tone):
    assert analyze_audio(tone, calibration_offset_db=0.0).laeq_dbfs_a == \
        analyze_audio(tone).laeq_dbfs_a
