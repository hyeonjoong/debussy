"""Level descriptors: LAeq (A-weighted), dynamic range, crest factor.

These follow the conventions of IEC 61672-1 (LAeq with A-weighting) and standard
sound-design reporting. LAeq is in dBFS-A unless a calibration offset is supplied
to :func:`debussy.analyze_audio` via ``calibration_offset_db``.
"""
from ._core import (
    a_weighting_filter,
    laeq_dbfs,
    dynamic_range_db,
)

__all__ = ["a_weighting_filter", "laeq_dbfs", "dynamic_range_db"]
