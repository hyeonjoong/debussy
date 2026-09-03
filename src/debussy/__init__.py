"""DEBUSSY — the eleven-item minimum acoustic reporting guideline for autonomic-arousal stimuli.

Public API:

    >>> from debussy import analyze_audio
    >>> result = analyze_audio("stimulus.wav")
    >>> result.laeq_dbfs_a
    -17.89

The :class:`Result` dataclass exposes all eleven reporting items plus run
metadata, and additive temporal-coverage descriptors
(``roughness_coverage_pct``, ``sharp_onset_pct``) reporting the proportion of
the stimulus that crosses each Tier-1 reference value — so a long clip that is
calm on average no longer hides brief harsh passages.
See the :mod:`debussy.level`, :mod:`debussy.envelope`, :mod:`debussy.spectral`,
:mod:`debussy.tonal`, and :mod:`debussy.psychoacoustic` submodules for the
parameter-family groupings.
"""
from ._core import (
    analyze_audio,
    analyse,  # legacy alias retained for backward compatibility
    Result,
    print_report,
    write_csv,
    # Tier framework
    tier1_items,
    tier2_items,
    tier3_items,
    tier1_compliance,
    format_compliance,
    # Temporal coverage (length-aware, additive)
    coverage_items,
    # Plots (optional, require matplotlib)
    plot_spectrogram,
    plot_parameter_radar,
    plot_tier_compliance,
    plot_coverage,
)
from ._tiers import (
    # Evidence scores and tier assignments from the companion review
    ParameterEvidence,
    PARAMETERS,
    parameter,
    parameters_in_tier,
)

__version__ = "0.3.0"
__all__ = [
    "analyze_audio",
    "analyse",
    "Result",
    "print_report",
    "write_csv",
    "tier1_items",
    "tier2_items",
    "tier3_items",
    "tier1_compliance",
    "format_compliance",
    "coverage_items",
    "plot_spectrogram",
    "plot_parameter_radar",
    "plot_tier_compliance",
    "plot_coverage",
    "ParameterEvidence",
    "PARAMETERS",
    "parameter",
    "parameters_in_tier",
    "__version__",
]
