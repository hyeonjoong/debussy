#!/usr/bin/env python3
"""Summarise the benchmark parameter matrix and reproduce the distribution figure.

For each of the twelve measured quantities this computes, across the three
benchmark categories:

* medians and group sizes,
* Cliff's delta and a two-sided Mann-Whitney U test for the A-vs-B contrast,
* Benjamini-Hochberg q-values across the twelve A-vs-B tests (the paper reports
  that no contrast survives this correction),
* Cliff's delta for C-vs-A and C-vs-B.

It writes ``summary_statistics.csv`` and the twelve-panel violin/box/strip figure.

Usage
-----
    python validation/analyze_results.py
    python validation/analyze_results.py --parameters results/parameters.csv --out-dir results/
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent

PARAMS = [
    ("laeq_dbfs_a", "LAeq (dBFS-A)"),
    ("dynamic_range_db", "Dynamic range (dB)"),
    ("crest_factor_db", "Crest factor (dB)"),
    ("attack_median_ms", "Attack median (ms)"),
    ("roughness_asper", "Roughness (asper)"),
    ("tempo_bpm", "Tempo (BPM)"),
    ("modulation_peak_hz", "Modulation peak (Hz)"),
    ("spectral_centroid_hz", "Spectral centroid (Hz)"),
    ("sharpness_acum", "Sharpness (acum)"),
    ("spectral_slope_beta", "Spectral slope beta"),
    ("hnr_db", "HNR (dB)"),
    ("spectral_flatness", "Spectral flatness"),
]

COLOR_A, COLOR_B, COLOR_C = "#4575b4", "#d73027", "#1a9850"
JITTER_SEED = 20260527  # fixed so the figure is byte-reproducible


def category_of(subcategory: str) -> str:
    """Map a manifest subcategory label onto the A / B / C benchmark groups."""
    if "DEAM low" in subcategory:
        return "A"
    if "mid-high" in subcategory or "FMA" in subcategory:
        return "B"
    if "BELL" in subcategory:
        return "C"
    return "Other"


def cliffs_delta(x, y) -> float:
    """Cliff's delta: P(x > y) - P(x < y). Positive means x tends to be larger."""
    x, y = np.asarray(x), np.asarray(y)
    if x.size == 0 or y.size == 0:
        return float("nan")
    greater = (x[:, None] > y[None, :]).sum()
    less = (x[:, None] < y[None, :]).sum()
    return float((greater - less) / (x.size * y.size))


def benjamini_hochberg(pvals) -> np.ndarray:
    """BH step-up adjusted p-values (q-values), order preserved, monotone."""
    p = np.asarray(pvals, dtype=float)
    ok = ~np.isnan(p)
    q = np.full(p.shape, np.nan)
    if not ok.any():
        return q
    sub = p[ok]
    n = sub.size
    order = np.argsort(sub)
    ranked = sub[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]  # enforce monotonicity
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def make_figure(groups, out_base: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "figure.dpi": 150})
    rng = np.random.default_rng(JITTER_SEED)
    A, B, C = groups

    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    for ax, (key, label) in zip(axes.flatten(), PARAMS):
        a, b, c = (g[key].dropna().values for g in (A, B, C))

        parts = ax.violinplot([a, b], positions=[1, 2], widths=0.7,
                              showmeans=False, showmedians=False, showextrema=False)
        for body, color in zip(parts["bodies"], [COLOR_A, COLOR_B]):
            body.set_facecolor(color)
            body.set_alpha(0.45)
            body.set_edgecolor("k")
            body.set_linewidth(0.5)

        box = ax.boxplot([a, b], positions=[1, 2], widths=0.22, patch_artist=True,
                         showfliers=False, medianprops={"color": "k", "linewidth": 1.3})
        for patch in box["boxes"]:
            patch.set_facecolor("white")
            patch.set_edgecolor("k")
            patch.set_linewidth(0.6)

        for j, vals in enumerate([a, b]):
            ax.scatter(rng.normal(j + 1, 0.045, size=vals.size), vals,
                       s=12, color="k", alpha=0.5, zorder=4, linewidths=0)
        ax.scatter(rng.normal(3, 0.06, size=c.size), c, s=26, color=COLOR_C, alpha=0.85,
                   zorder=6, edgecolors="k", linewidths=0.5, marker="D")
        if c.size:
            ax.hlines(np.median(c), 2.78, 3.22, colors="k", linewidth=1.6, zorder=7)

        delta = cliffs_delta(a, b)
        try:
            pval = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
        except ValueError:
            pval = float("nan")
        ax.set_title(f"{label}{' *' if pval < 0.05 else ''}\n"
                     f"A vs B: d={delta:+.2f}, p={pval:.3f}", fontsize=9)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels([f"A\nn={a.size}", f"B\nn={b.size}", f"C\nn={c.size}"], fontsize=8)
        ax.tick_params(axis="y", labelsize=7.5)
        ax.grid(axis="y", alpha=0.3, linestyle=":")

    fig.suptitle(
        "DEBUSSY reporting-parameter distributions on the 60-track benchmark\n"
        "A - Relaxation (DEAM low-arousal) | B - Frequently listened (DEAM mid-high + FMA-medium) "
        "| C - BELL-001 SleepThera (green diamonds)",
        fontsize=10.5, y=0.997)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".pdf"), bbox_inches="tight")
    print(f"  figure       -> {out_base.with_suffix('.png')}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parameters", type=Path,
                    default=HERE / "data" / "parameters_60tracks.csv",
                    help="Per-track parameter matrix (default: data/parameters_60tracks.csv)")
    ap.add_argument("--out-dir", type=Path, default=HERE / "results",
                    help="Where to write outputs (default: validation/results)")
    ap.add_argument("--no-figure", action="store_true",
                    help="Skip the figure (avoids the matplotlib dependency)")
    args = ap.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.parameters)
    df["CategoryGroup"] = df["Subcategory"].map(category_of)
    groups = tuple(df[df["CategoryGroup"] == g] for g in ("A", "B", "C"))
    A, B, C = groups
    print(f"Loaded {len(df)} tracks from {args.parameters}  "
          f"(A={len(A)}, B={len(B)}, C={len(C)})")

    rows = []
    for key, label in PARAMS:
        a, b, c = (g[key].dropna().values for g in groups)
        try:
            pval = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
        except ValueError:
            pval = float("nan")
        rows.append({
            "parameter": label,
            "A_n": a.size, "A_median": round(float(np.median(a)), 3) if a.size else None,
            "B_n": b.size, "B_median": round(float(np.median(b)), 3) if b.size else None,
            "C_n": c.size, "C_median": round(float(np.median(c)), 3) if c.size else None,
            "cliff_delta_A_vs_B": round(cliffs_delta(a, b), 3),
            "MWU_p_A_vs_B": round(pval, 4) if not np.isnan(pval) else None,
            "cliff_delta_C_vs_A": round(cliffs_delta(c, a), 3),
            "cliff_delta_C_vs_B": round(cliffs_delta(c, b), 3),
        })

    summary = pd.DataFrame(rows)
    summary["BH_q_A_vs_B"] = np.round(benjamini_hochberg(summary["MWU_p_A_vs_B"]), 4)
    out_csv = args.out_dir / "summary_statistics.csv"
    summary.to_csv(out_csv, index=False)
    print(f"  statistics   -> {out_csv}")

    if not args.no_figure:
        make_figure(groups, args.out_dir / "Fig1_60tracks_with_C_overlay")

    sig = summary[summary["MWU_p_A_vs_B"] < 0.05]
    print(f"\nA vs B: {len(sig)}/{len(summary)} parameters at uncorrected p < 0.05; "
          f"smallest BH q = {summary['BH_q_A_vs_B'].min():.3f} "
          f"({'none survive' if summary['BH_q_A_vs_B'].min() >= 0.05 else 'some survive'} "
          f"correction across the twelve tests)")
    print("\nC vs A / C vs B (Cliff's delta; positive = C larger):")
    for r in rows:
        print(f"  {r['parameter']:<24} d(C,A)={r['cliff_delta_C_vs_A']:+.2f}  "
              f"d(C,B)={r['cliff_delta_C_vs_B']:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
