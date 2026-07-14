"""The 44.1 kHz → 48 kHz resample path.

mosqito's psychoacoustic metrics require 48 kHz, so DEBUSSY warns (a library-owned
UserWarning, independent of mosqito's version-dependent stdout) whenever a non-48
kHz signal will be resampled for roughness/sharpness. Verify the warning fires at
44.1 kHz, is silenced by suppress_warnings=True, is absent at 48 kHz, and that the
reported sample_rate stays the file's native rate.
"""
from __future__ import annotations

import warnings

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


def _am_tone(path, fs, dur=3.0, amp=0.4):
    # Amplitude-modulated tone so mosqito's roughness stage has real signal.
    t = np.arange(int(fs * dur)) / fs
    y = amp * (1 + 0.5 * np.sin(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 300 * t)
    sf.write(path, np.clip(y, -1, 1).astype(np.float32), fs, subtype="PCM_16")
    return str(path)


def _resample_warnings(caught):
    return [w for w in caught if "resample" in str(w.message).lower()]


def test_resample_warns_at_44100(tmp_path):
    with pytest.warns(UserWarning, match="resampled to 48 kHz"):
        analyze_audio(_am_tone(tmp_path / "a.wav", 44100))


def test_resample_warning_suppressed(tmp_path):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        analyze_audio(_am_tone(tmp_path / "b.wav", 44100), suppress_warnings=True)
    assert not _resample_warnings(caught)


def test_no_resample_warning_at_48000(tmp_path):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        analyze_audio(_am_tone(tmp_path / "c.wav", 48000))
    assert not _resample_warnings(caught)


def test_reported_sample_rate_is_native(tmp_path):
    r = analyze_audio(_am_tone(tmp_path / "d.wav", 44100))
    assert r.sample_rate == 44100
