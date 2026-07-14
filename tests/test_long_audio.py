"""Long-input handling.

Files longer than the full-analysis cap (MAX_ANALYZE_S, default 50 s) are
characterised from evenly spaced probes spanning the whole recording. The true
duration must be preserved and the headline metrics must still be produced.
Marked slow because it runs the psychoacoustic pipeline several times.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


@pytest.fixture(scope="module")
def long_wav(tmp_path_factory):
    fs = 48000
    dur = 60.0  # > 50 s default cap → probe path
    t = np.arange(int(fs * dur)) / fs
    y = 0.3 * np.sin(2 * np.pi * 220 * t)
    p = tmp_path_factory.mktemp("long") / "long.wav"
    sf.write(p, y.astype(np.float32), fs, subtype="PCM_16")
    return str(p)


@pytest.mark.slow
def test_long_input_uses_probe_mode(long_wav):
    r = analyze_audio(long_wav)
    assert r.analysis_mode == "probe"
    assert abs(r.duration_s - 60.0) < 1.0
    assert r.laeq_dbfs_a is not None
    assert r.spectral_centroid_hz is not None


@pytest.mark.slow
def test_long_input_probe_note_records_coverage(long_wav):
    r = analyze_audio(long_wav)
    assert "probe-based" in (r.notes or "")
