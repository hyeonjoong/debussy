"""Graceful degradation when no onsets are detected.

The attack descriptors are 10–90 % envelope rise times measured per onset. On a
steady tone or on silence there are too few onsets to estimate them, so the
attack_* fields must be None and the pipeline must not raise.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio


def _write(path, y, fs=48000):
    sf.write(path, np.asarray(y, dtype=np.float32), fs, subtype="PCM_16")
    return str(path)


def test_steady_tone_attack_is_none_when_no_onsets(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 4)) / fs
    r = analyze_audio(_write(tmp_path / "tone.wav", 0.4 * np.sin(2 * np.pi * 440 * t), fs))
    if r.attack_n_onsets < 2:
        assert r.attack_mean_ms is None
        assert r.attack_median_ms is None
        assert r.attack_sd_ms is None


def test_silence_degrades_gracefully(tmp_path):
    fs = 48000
    r = analyze_audio(_write(tmp_path / "silence.wav", np.zeros(int(fs * 3)), fs))
    assert r.attack_mean_ms is None
    assert r.attack_n_onsets < 2
    assert r.sharp_onset_pct is None or r.sharp_onset_pct == 0.0
