"""Result serialisation.

Result.to_json() must round-trip through to_dict() and the json module, and the
decoded dict must reconstruct an equal Result — so downstream tools can persist
and reload analyses losslessly.
"""
from __future__ import annotations

import json

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio, Result


@pytest.fixture
def result(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 4)) / fs
    p = tmp_path / "t.wav"
    sf.write(p, (0.4 * np.sin(2 * np.pi * 300 * t)).astype(np.float32), fs, subtype="PCM_16")
    return analyze_audio(str(p))


def test_to_dict_contains_headline_fields(result):
    d = result.to_dict()
    for key in ("file", "duration_s", "sample_rate", "laeq_dbfs_a",
                "roughness_asper", "spectral_centroid_hz", "notes"):
        assert key in d


def test_to_json_matches_to_dict(result):
    assert json.loads(result.to_json()) == result.to_dict()


def test_json_reconstructs_equal_result(result):
    assert Result(**json.loads(result.to_json())) == result


def test_compact_json_is_single_line(result):
    assert "\n" not in result.to_json(indent=None)
