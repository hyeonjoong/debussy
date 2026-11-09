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


def _write_long(tmp_path, name, y, fs):
    p = tmp_path / name
    sf.write(p, y.astype(np.float32), fs, subtype="PCM_16")
    return str(p)


@pytest.fixture
def no_psychoacoustics(monkeypatch):
    """Skip mosqito: these tests are about tempo, and roughness on 60 s of
    broadband noise is what would make them slow."""
    from debussy import _core
    monkeypatch.setattr(_core, "psychoacoustics",
                        lambda y, fs, suppress_warnings=False: {
                            "roughness_asper": None, "sharpness_acum": None,
                            "roughness_coverage_pct": None})


@pytest.mark.parametrize("seed", [0, 1])
def test_long_noise_gets_no_tempo(tmp_path, no_psychoacoustics, seed):
    """Broadband noise has no pulse, at any length.

    Analysed in full, white noise is withheld on beat agreement. In probe mode
    it used to be given a tempo of about 123 BPM: on 3 s probes the committee
    sees too few beats to disagree, so most probes pass, and the median was
    taken over whichever probes reported one. Rain and other nature sounds
    longer than the full-analysis cap are exactly this case.
    """
    fs = 22050
    rng = np.random.default_rng(seed)
    y = 0.1 * rng.standard_normal(int(fs * 60.0))
    r = analyze_audio(_write_long(tmp_path, "noise.wav", y, fs),
                      suppress_warnings=True)
    assert r.analysis_mode == "probe"
    assert r.tempo_bpm is None, (
        f"tempo {r.tempo_bpm} reported; agreement={r.beat_agreement}, "
        f"flux={r.onset_flux}")


def test_long_click_train_keeps_its_tempo(tmp_path, no_psychoacoustics):
    fs = 22050
    y = np.zeros(int(fs * 60.0))
    for k in range(0, len(y) - 220, int(fs * 0.75)):     # 80 BPM
        y[k:k + 220] += 0.5 * np.hanning(220)
    r = analyze_audio(_write_long(tmp_path, "clicks.wav", y, fs),
                      suppress_warnings=True)
    assert r.analysis_mode == "probe"
    assert r.tempo_bpm is not None and abs(r.tempo_bpm - 80.0) < 3.0, r


def test_pooled_tempo_follows_the_pooled_statistics():
    """The withholding rule is applied to the statistics the Result reports.

    One window of six passing on its own must not put a tempo next to a pooled
    agreement that would have withheld it, which is what taking the median
    over the reporting windows alone did.
    """
    from debussy._core import BEAT_AGREEMENT_REFERENCE, _pool_tempo
    lo = BEAT_AGREEMENT_REFERENCE - 0.2
    windows = [(0.75, 0.87, 125.0)] + [(lo, 0.87, None)] * 5
    pooled = _pool_tempo(windows)
    assert pooled["beat_agreement"] < BEAT_AGREEMENT_REFERENCE
    assert pooled["tempo_bpm"] is None

    windows = [(0.95, 1.5, 80.0)] * 4 + [(lo, 1.5, None)] * 2
    pooled = _pool_tempo(windows)
    assert pooled["tempo_bpm"] == 80.0
