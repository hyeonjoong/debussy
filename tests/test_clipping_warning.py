"""Full-scale clipping warning.

Samples pinned at digital full scale mean the source clipped on capture, which
distorts every level and spectral metric. analyze_audio must raise a UserWarning
(and annotate Result.notes) on such input, stay silent on clean input, and honour
suppress_warnings=True while still recording the note.
"""
from __future__ import annotations

import warnings

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


def _write(path, y, fs=48000):
    sf.write(path, np.clip(y, -1, 1).astype(np.float32), fs, subtype="PCM_16")
    return str(path)


@pytest.fixture
def clipped(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 3)) / fs
    return _write(tmp_path / "clip.wav", 1.5 * np.sin(2 * np.pi * 300 * t), fs)


@pytest.fixture
def clean(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 3)) / fs
    return _write(tmp_path / "clean.wav", 0.4 * np.sin(2 * np.pi * 300 * t), fs)


def test_clipping_input_warns(clipped):
    with pytest.warns(UserWarning, match="clip"):
        r = analyze_audio(clipped)
    assert "clipping" in r.notes


def test_clean_input_does_not_warn_about_clipping(clean):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        analyze_audio(clean)
    assert not [w for w in caught if "clip" in str(w.message).lower()]


def test_suppress_warnings_silences_clip_warning(clipped):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = analyze_audio(clipped, suppress_warnings=True)
    assert not [w for w in caught if "clip" in str(w.message).lower()]
    # The note is still recorded even when the warning is suppressed.
    assert "clipping" in r.notes
