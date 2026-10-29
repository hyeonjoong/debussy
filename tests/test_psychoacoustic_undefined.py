"""Undefined psychoacoustic values must surface as None, never NaN.

On digital silence mosqito's DIN 45692 sharpness divides by zero loudness and
returns an all-NaN series. NaN is not None, so it slipped past every
``is None`` guard: the Tier 2 report flagged silence as "Above the provisional
exemplar", ``to_json()`` emitted a bare ``NaN`` that strict JSON parsers reject,
and the documented ``Result(**json.loads(r.to_json())) == r`` round-trip broke
because NaN never equals itself.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pytest
import soundfile as sf

from debussy import Result, analyze_audio
from debussy import _core
from debussy._core import tier2_items

FS = 48000


@pytest.fixture(scope="module")
def silence(tmp_path_factory):
    path = tmp_path_factory.mktemp("psy_undefined") / "silence.wav"
    sf.write(path, np.zeros(FS * 3, dtype=np.float32), FS, subtype="PCM_16")
    return analyze_audio(str(path), suppress_warnings=True)


def _reject_constant(name):
    raise ValueError(f"non-standard JSON constant {name}")


def test_psychoacoustics_returns_none_not_nan_on_silence():
    psy = _core.psychoacoustics(np.zeros(FS * 3), FS, suppress_warnings=True)
    for key in ("roughness_asper", "sharpness_acum", "roughness_coverage_pct"):
        v = psy[key]
        assert v is None or math.isfinite(v), f"{key} = {v!r}"


def test_silence_sharpness_is_none_with_reason_in_notes(silence):
    assert silence.sharpness_acum is None
    assert "sharpness_err" in silence.notes


def test_silence_has_no_nan_fields(silence):
    nan_fields = [k for k, v in silence.to_dict().items()
                  if isinstance(v, float) and not math.isfinite(v)]
    assert nan_fields == []


def test_silence_sharpness_is_not_reported_out_of_range(silence):
    (item,) = [i for i in tier2_items(silence) if i["parameter"] == "Sharpness"]
    assert item["status"] == "N/A"


def test_silence_json_is_strict_and_round_trips(silence):
    decoded = json.loads(silence.to_json(), parse_constant=_reject_constant)
    assert Result(**decoded) == silence
