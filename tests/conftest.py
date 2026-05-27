"""Shared pytest fixtures — synthetic reference signals with known properties."""
from __future__ import annotations
import os
import tempfile
import numpy as np
import soundfile as sf
import pytest

SR = 44100
DUR = 5.0  # seconds — short fixtures keep CI fast


@pytest.fixture(scope="session")
def fixtures_dir():
    """Per-session temporary directory for generated WAV fixtures."""
    with tempfile.TemporaryDirectory(prefix="debussy_test_") as td:
        yield td


@pytest.fixture(scope="session")
def sine_440(fixtures_dir):
    """Pure 440 Hz sine wave, peak amplitude 0.5 (well below clipping)."""
    t = np.arange(int(SR * DUR)) / SR
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    path = os.path.join(fixtures_dir, "sine_440.wav")
    sf.write(path, y, SR, subtype="PCM_16")
    return path


@pytest.fixture(scope="session")
def pink_noise(fixtures_dir):
    """Pink (1/f) noise via FFT shaping. Peak normalised to 0.5."""
    rng = np.random.default_rng(42)
    n = int(SR * DUR)
    white = rng.standard_normal(n)
    # Shape spectrum: |X(f)|² ∝ 1/f → |X(f)| ∝ 1/√f
    spec = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    freqs[0] = freqs[1]  # avoid div-by-zero at DC
    spec = spec / np.sqrt(freqs)
    pink = np.fft.irfft(spec, n=n)
    pink = pink / np.max(np.abs(pink)) * 0.5
    path = os.path.join(fixtures_dir, "pink_noise.wav")
    sf.write(path, pink.astype(np.float32), SR, subtype="PCM_16")
    return path


@pytest.fixture(scope="session")
def click_train(fixtures_dir):
    """120 BPM impulse train — 2 clicks per second, each click 5 ms wide."""
    n = int(SR * DUR)
    y = np.zeros(n, dtype=np.float32)
    click_width = int(SR * 0.005)
    bpm = 120
    period = int(SR * 60 / bpm)
    for i in range(0, n - click_width, period):
        y[i:i + click_width] = 0.7
    path = os.path.join(fixtures_dir, "click_train_120bpm.wav")
    sf.write(path, y, SR, subtype="PCM_16")
    return path


@pytest.fixture(scope="session")
def silence(fixtures_dir):
    """Silent reference for boundary cases."""
    y = np.zeros(int(SR * DUR), dtype=np.float32)
    path = os.path.join(fixtures_dir, "silence.wav")
    sf.write(path, y, SR, subtype="PCM_16")
    return path
