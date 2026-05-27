"""Psychoacoustic descriptors via MOSQITO: roughness (asper), sharpness (acum).

Roughness follows Daniel & Weber 1997; sharpness follows DIN 45692.
Both delegate to :pypi:`mosqito` (the MOSQITO toolbox) for the validated
reference implementations; DEBUSSY exposes them through a single function that
returns both values in one call.
"""
from ._core import psychoacoustics

__all__ = ["psychoacoustics"]
