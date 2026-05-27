"""Temporal-envelope descriptors: attack time, tempo, modulation peak.

Attack time is computed per detected onset over a 10–90 % rise window;
tempo uses ``librosa.beat.beat_track``; modulation peak finds the envelope-spectrum
peak in the 0.5–20 Hz band.
"""
from ._core import (
    attack_times_ms,
    tempo_bpm,
    modulation_peak_hz,
)

__all__ = ["attack_times_ms", "tempo_bpm", "modulation_peak_hz"]
