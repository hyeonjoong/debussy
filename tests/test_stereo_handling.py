"""Stereo → mono downmix.

analyze_audio collapses multi-channel input to mono by averaging channels, so a
stereo file must yield the same level and spectral metrics as its explicit
per-sample L/R mean written out as a mono file.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio

SR = 48000
DUR = 4.0


@pytest.fixture
def stereo_and_mono(tmp_path):
    t = np.arange(int(SR * DUR)) / SR
    left = 0.40 * np.sin(2 * np.pi * 220 * t)
    right = 0.30 * np.sin(2 * np.pi * 330 * t + 0.5)
    stereo = np.column_stack([left, right])
    mono = stereo.mean(axis=1)
    ps = tmp_path / "stereo.wav"
    sf.write(ps, stereo.astype(np.float32), SR, subtype="PCM_16")
    pm = tmp_path / "mono.wav"
    sf.write(pm, mono.astype(np.float32), SR, subtype="PCM_16")
    return str(ps), str(pm)


def test_stereo_downmix_matches_explicit_mono(stereo_and_mono):
    ps, pm = stereo_and_mono
    rs = analyze_audio(ps)
    rm = analyze_audio(pm)
    # Only quantisation noise separates mean(quantise(L,R)) from
    # quantise(mean(L,R)); LAeq must agree tightly and the centroid to ~1 %.
    assert abs(rs.laeq_dbfs_a - rm.laeq_dbfs_a) < 0.1
    assert rs.spectral_centroid_hz == pytest.approx(rm.spectral_centroid_hz, rel=0.02)


def test_stereo_reports_scalar_metrics(stereo_and_mono):
    ps, _ = stereo_and_mono
    r = analyze_audio(ps)
    # Downmixed to a single channel → one scalar per metric, not per-channel.
    assert isinstance(r.laeq_dbfs_a, float)
    assert isinstance(r.spectral_centroid_hz, float)
