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
