"""Short-clip edge cases (<3 s).

BELL-001 breath stimuli are frequently only a second or two long, so the
pipeline must stay robust on very short inputs rather than crash or return
non-finite level metrics. Onset-derived attack fields may legitimately be None
when there are too few onsets to estimate a rise time.
"""
from __future__ import annotations

import math

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio, Result

SR = 44100


@pytest.fixture
def short_wav(tmp_path):
    def _make(dur_s, freq=440.0, amp=0.4):
        t = np.arange(int(SR * dur_s)) / SR
        y = amp * np.sin(2 * np.pi * freq * t)
        p = tmp_path / f"clip_{dur_s}.wav"
        sf.write(p, y.astype(np.float32), SR, subtype="PCM_16")
        return str(p)
    return _make


@pytest.mark.parametrize("dur", [0.5, 1.0, 2.0])
def test_short_clip_returns_result(short_wav, dur):
    r = analyze_audio(short_wav(dur))
    assert isinstance(r, Result)
    assert abs(r.duration_s - dur) < 0.05


@pytest.mark.parametrize("dur", [0.5, 1.0, 2.0])
def test_short_clip_level_metrics_finite(short_wav, dur):
    r = analyze_audio(short_wav(dur))
    assert r.laeq_dbfs_a is not None and math.isfinite(r.laeq_dbfs_a)
    assert r.dynamic_range_db is not None and r.dynamic_range_db >= 0.0


def test_subsecond_clip_attack_degrades_gracefully(short_wav):
    # A 0.5 s pure tone rarely yields two onsets, so the attack estimate is
    # undefined — the fields must be None, never a crash or a bogus number.
    r = analyze_audio(short_wav(0.5))
    if r.attack_n_onsets < 2:
        assert r.attack_mean_ms is None
        assert r.attack_median_ms is None
        assert r.attack_sd_ms is None


# --- Clips of exactly one dynamic-range window -------------------------------
# dynamic_range_db() frames the signal into 50 ms windows and reports the p95-p5
# span of their RMS levels. A clip of exactly one window long left the frame
# loop empty, so np.percentile raised a bare IndexError out of analyze_audio —
# one sample shorter or longer was fine. A single window has one RMS value, so
# the span is 0 dB, which is what the streaming long-file path already returns
# when it collects no full window.

WIN_MS = 50.0  # dynamic_range_db's default window


@pytest.mark.parametrize("sr", [44100, 48000])
def test_dynamic_range_at_exactly_one_window(sr):
    from debussy._core import dynamic_range_db

    win = int(sr * WIN_MS / 1000)
    y = 0.4 * np.sin(2 * np.pi * 440 * np.arange(win) / sr)
    assert dynamic_range_db(y, sr) == 0.0
    # The samples either side of the boundary must stay finite too.
    assert math.isfinite(dynamic_range_db(y[:-1], sr))
    assert math.isfinite(dynamic_range_db(np.concatenate([y, y[:1]]), sr))


@pytest.mark.parametrize("sr", [44100, 48000])
def test_one_window_clip_analyses_without_crashing(tmp_path, sr):
    n = int(sr * WIN_MS / 1000)  # exactly one window, as dynamic_range_db frames it
    y = 0.4 * np.sin(2 * np.pi * 440 * np.arange(n) / sr)
    p = tmp_path / f"one_window_{sr}.wav"
    sf.write(p, y.astype(np.float32), sr, subtype="PCM_16")
    r = analyze_audio(str(p))
    assert isinstance(r, Result)
    assert r.dynamic_range_db == 0.0
