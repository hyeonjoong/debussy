"""Spectral-shape descriptors: spectral centroid, spectral slope β.

Spectral centroid is the standard ``librosa.feature.spectral_centroid`` mean.
Spectral slope β is the linear-regression slope of the log-power spectral density
on a log-frequency axis over 50 Hz to ``fs/2``.
"""
from ._core import (
    spectral_centroid_hz,
    spectral_slope,
)

__all__ = ["spectral_centroid_hz", "spectral_slope"]
