"""Temporal-coverage descriptors, coverage-gated Tier-1, and long-file probing.

These features are additive: they do not change the 12 headline parameters
(verified by the other test modules), but report the PROPORTION of a stimulus
that crosses each Tier-1 threshold so a long clip that is calm on average no
longer hides brief harsh passages.
"""
from __future__ import annotations

import os

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio, coverage_items, tier1_items

FS = 48000  # mosqito-friendly sample rate

_T1_STATUSES = {"PASS", "FAIL", "CAUTION", "INFO", "MANUAL", "N/A"}


@pytest.fixture(scope="session")
def rough_burst(tmp_path_factory):
    """6 s: 3 s clean tone followed by 3 s of 70 Hz amplitude modulation
    (high Daniel-Weber roughness) — so roughly half the file is 'rough'."""
    t = np.arange(int(FS * 6)) / FS
    tone = 0.4 * np.sin(2 * np.pi * 300 * t)
    mod = 0.5 * (1 + np.sin(2 * np.pi * 70 * t))  # 70 Hz AM → rough
    half = len(t) // 2
    y = tone.copy()
    y[half:] = tone[half:] * mod[half:]
    path = os.path.join(tmp_path_factory.mktemp("cov"), "rough_burst.wav")
    sf.write(path, np.clip(y, -1, 1), FS, subtype="PCM_16")
    return path


@pytest.fixture(scope="session")
def long_file(tmp_path_factory):
    """95 s tone — just over the full-analysis cap, forcing the probe path."""
    t = np.arange(int(FS * 95)) / FS
    y = 0.2 * np.sin(2 * np.pi * 220 * t)
    path = os.path.join(tmp_path_factory.mktemp("long"), "long_tone.wav")
    sf.write(path, y, FS, subtype="PCM_16")
    return path


def test_result_exposes_coverage_fields(sine_440):
    r = analyze_audio(sine_440)
    assert hasattr(r, "roughness_coverage_pct")
    assert hasattr(r, "sharp_onset_pct")


def test_coverage_items_shape(sine_440):
    items = coverage_items(analyze_audio(sine_440))
    assert len(items) == 2
    for it in items:
        for key in ("parameter", "value", "threshold", "interpretation", "note"):
            assert key in it


def test_coverage_is_a_percentage_or_none(rough_burst):
    r = analyze_audio(rough_burst)
    cov = r.roughness_coverage_pct
    assert cov is None or (0.0 <= cov <= 100.0)


def test_rough_passages_register_as_coverage(rough_burst):
    """A file that is rough for ~half its length must not read as clean."""
    r = analyze_audio(rough_burst)
    if r.roughness_coverage_pct is not None:
        assert r.roughness_coverage_pct > 0.0
        rough = [it for it in tier1_items(r) if it["parameter"] == "Roughness"][0]
        assert rough["status"] in {"CAUTION", "FAIL"}  # never a clean PASS


def test_tier1_statuses_are_valid(sine_440, rough_burst):
    for path in (sine_440, rough_burst):
        for it in tier1_items(analyze_audio(path)):
            assert it["status"] in _T1_STATUSES


@pytest.mark.slow
def test_long_file_uses_probe_based_analysis(long_file):
    r = analyze_audio(long_file)
    assert "probe-based" in (r.notes or "")
    assert abs(r.duration_s - 95.0) < 1.0          # true full duration preserved
    assert r.laeq_dbfs_a is not None                # headline params still produced
    assert r.spectral_centroid_hz is not None
