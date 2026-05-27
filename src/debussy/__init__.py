"""DEBUSSY — 11-parameter acoustic reporting for autonomic-arousal stimulus preparation.

Public API:

    >>> from debussy import analyze_audio
    >>> result = analyze_audio("stimulus.wav")
    >>> result.laeq_dbfs_a
    -17.89

The :class:`Result` dataclass exposes all 11 reporting parameters plus run metadata.
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
    # Plots (optional, require matplotlib)
    plot_spectrogram,
    plot_parameter_radar,
    plot_tier_compliance,
)

__version__ = "0.1.0"
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
    "plot_spectrogram",
    "plot_parameter_radar",
    "plot_tier_compliance",
    "__version__",
]
