"""Tonal-structure descriptors: harmonics-to-noise ratio, spectral flatness.

HNR uses autocorrelation on voiced frames (Boersma 1993 method).
Spectral flatness is the geometric mean / arithmetic mean ratio in [0, 1].
"""
from ._core import (
    hnr_db,
    spectral_flatness,
)

__all__ = ["hnr_db", "spectral_flatness"]
