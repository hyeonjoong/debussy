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


def _probe(truncation_clicks, abrupt_endings, max_step_db, n_onsets=4):
    """A per-probe Result carrying only what the pooling under test reads."""
    from debussy._core import Result
    return Result(
        file="probe", duration_s=3.0, sample_rate=48000, laeq_dbfs_a=-20.0,
        dynamic_range_db=5.0, attack_n_onsets=n_onsets, attack_mean_ms=None,
        attack_median_ms=None, attack_sd_ms=None, roughness_asper=0.1,
        tempo_bpm=None, modulation_peak_hz=None, spectral_centroid_hz=500.0,
        sharpness_acum=1.0, spectral_slope_beta=-1.5, hnr_db=None,
        lyrics="unknown", delivery="unknown", spectral_flatness=0.1,
        truncation_clicks=truncation_clicks, abrupt_endings=abrupt_endings,
        truncation_max_step_db=max_step_db,
    )


def _pool(probes):
    from debussy._core import _aggregate_probes
    return _aggregate_probes(probes, "long.wav", 600.0, 48000, "unknown",
                             "unknown", "probe-based", {})


def test_probe_ending_counts_are_summed_not_medianed():
    # Clicks confined to two of six probes. A median over probes reported 0,
    # which reads as a clean file, while the onset count from the same probes
    # was already summed.
    probes = [_probe(0, 0, None)] * 4 + [_probe(2, 1, -30.0),
                                          _probe(3, 1, -20.0)]
    r = _pool(probes)
    assert r.truncation_clicks == 5
    assert r.abrupt_endings == 2
    assert r.attack_n_onsets == 24


def test_probe_ending_counts_stay_integers():
    # With an even number of probes a median could land between two counts.
    probes = [_probe(0, 0, None)] * 3 + [_probe(1, 1, -30.0)] * 3
    r = _pool(probes)
    assert isinstance(r.truncation_clicks, int)
    assert isinstance(r.abrupt_endings, int)
    assert (r.truncation_clicks, r.abrupt_endings) == (3, 3)


def test_probe_largest_step_is_the_largest():
    # truncation_max_step_db is the most audible cut; pooling must not average
    # it down towards the quieter ones.
    probes = [_probe(0, 0, None)] * 3 + [_probe(1, 0, -35.0),
                                          _probe(1, 0, -30.0),
                                          _probe(1, 0, -20.0)]
    assert _pool(probes).truncation_max_step_db == -20.0


def test_probe_clean_endings_stay_zero():
    r = _pool([_probe(0, 0, None)] * 6)
    assert (r.truncation_clicks, r.abrupt_endings) == (0, 0)
    assert r.truncation_max_step_db is None
