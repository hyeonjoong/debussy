"""The 44.1 kHz → 48 kHz resample path.

mosqito's psychoacoustic metrics require 48 kHz, so it resamples any other rate
internally and prints a one-line notice to stdout. Verify that notice appears at
44.1 kHz, is silenced by ``suppress_warnings=True``, is absent when the input is
already 48 kHz, and that resampling never changes the reported native sample rate.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf

from debussy import analyze_audio

_NOTICE = "resampled to 48"


def _am_tone(path, fs, dur=3.0, amp=0.4):
    # Amplitude-modulated tone so mosqito's roughness stage has real signal.
    t = np.arange(int(fs * dur)) / fs
    y = amp * (1 + 0.5 * np.sin(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 300 * t)
    sf.write(path, np.clip(y, -1, 1).astype(np.float32), fs, subtype="PCM_16")
    return str(path)


def test_resample_notice_shown_at_44100(capsys, tmp_path):
    analyze_audio(_am_tone(tmp_path / "a.wav", 44100))
    assert _NOTICE in capsys.readouterr().out


def test_resample_notice_suppressed(capsys, tmp_path):
    analyze_audio(_am_tone(tmp_path / "b.wav", 44100), suppress_warnings=True)
    assert _NOTICE not in capsys.readouterr().out


def test_no_resample_notice_at_48000(capsys, tmp_path):
    analyze_audio(_am_tone(tmp_path / "c.wav", 48000))
    assert _NOTICE not in capsys.readouterr().out


def test_reported_sample_rate_is_native(tmp_path):
    r = analyze_audio(_am_tone(tmp_path / "d.wav", 44100))
    assert r.sample_rate == 44100
