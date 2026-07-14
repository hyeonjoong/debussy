"""Command-line interface (`python -m debussy._core`).

Exercises the real entry point in a subprocess: it prints a per-parameter report,
can append a CSV, and exits non-zero when no file could be analysed.
"""
from __future__ import annotations

import subprocess
import sys

import numpy as np
import soundfile as sf
import pytest


@pytest.fixture
def wav(tmp_path):
    fs = 48000
    t = np.arange(int(fs * 2.5)) / fs
    p = tmp_path / "cli.wav"
    sf.write(p, (0.4 * np.sin(2 * np.pi * 300 * t)).astype(np.float32), fs, subtype="PCM_16")
    return str(p)


def _run(*args):
    return subprocess.run([sys.executable, "-m", "debussy._core", *args],
                          capture_output=True, text=True, timeout=180)


def test_cli_reports_on_a_file(wav):
    r = _run(wav, "--suppress-warnings")
    assert r.returncode == 0, r.stderr
    assert "LAeq" in r.stdout


def test_cli_writes_csv(wav, tmp_path):
    out = tmp_path / "cli.csv"
    r = _run(wav, "--suppress-warnings", "--csv", str(out))
    assert r.returncode == 0, r.stderr
    assert out.exists()
    assert out.read_text().count("\n") >= 2  # header + at least one row


def test_cli_missing_file_exits_nonzero(tmp_path):
    r = _run(str(tmp_path / "does_not_exist.wav"))
    assert r.returncode == 1
