"""Tonal-structure descriptors: harmonics-to-noise ratio, spectral flatness.

The spectral flatness here is the unweighted geometric-to-arithmetic mean
ratio, which measures tonality. The reporting set recommends the perceptual
variant, weighting the energy at each frequency by the masking energy at that
frequency (Bosi & Goldberg, 2003, p. 218); it requires a masking model and is
not implemented yet.

HNR uses autocorrelation on voiced frames (Boersma 1993 method).
Spectral flatness is the geometric mean / arithmetic mean ratio in [0, 1].
"""
from ._core import (
    hnr_db,
    spectral_flatness,
)

__all__ = ["hnr_db", "spectral_flatness"]
