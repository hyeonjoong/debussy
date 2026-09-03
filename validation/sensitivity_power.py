#!/usr/bin/env python3
"""Power-sensitivity analysis for the A-vs-B contrast.

The 60-track benchmark reports that no A-vs-B contrast survives
Benjamini-Hochberg correction. That is true, but on its own it is ambiguous: a
null at *n*=10 versus *n*=30 could mean the parameters do not separate the
categories, or simply that the benchmark cannot see effects of the size present.

This distinguishes the two. It reads the two 300-track draws released alongside
it and reports, per parameter, Cliff's delta and a Benjamini-Hochberg q across
the same twelve tests, so all three can be read side by side.

* `data/parameters_sensitivity_n150.csv` — DEAM, 150 per group by annotated
  arousal (A lowest, B highest), 45 s excerpts as in the published benchmark.
* `data/parameters_sensitivity_fma150.csv` — an independent corpus. FMA tracks
  tagged ambient / drone / minimal against everything else, 150 each, 30 s FMA
  clips. Compared only within FMA, never pooled with the DEAM draw, since the
  clip lengths differ.

The second exists because agreement between corpora that share no annotators,
artists or recording conditions is evidence about acoustics rather than about
one dataset's idiosyncrasies. Its grouping variable is a genre tag rather than a
rated arousal, which is a noisier proxy, so its effects are expected to be
smaller — the question it answers is direction, not magnitude.

    python validation/sensitivity_power.py
    python validation/sensitivity_power.py --power   # also print the power curve

The draw itself: 150 tracks per group from the 1802 annotated DEAM tracks by a
stated rule — group A the lowest annotated arousal, group B the highest —
standardised identically to the published benchmark (44.1 kHz mono 16-bit,
centred 45 s) and analysed with the same `analyze_audio()` entry point.

Regenerating the matrix needs the DEAM audio, which is not redistributable here;
`benchmark/10_power_analysis/deam_scale.py` in the working repository does that
step. This script runs on the released matrix with no audio required, exactly as
`analyze_results.py` does.
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


def benjamini_hochberg(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    ok = ~np.isnan(p)
    out = np.full(p.shape, np.nan)
    pv = p[ok]
    n = pv.size
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / np.arange(1, n + 1)
    q = np.empty(n)
    q[order] = np.minimum.accumulate(ranked[::-1])[::-1]
    out[ok] = np.minimum(q, 1.0)
    return out


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """P(a > b) - P(a < b). Positive means group A tends to be larger."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if a.size == 0 or b.size == 0:
        return float("nan")
    gt = int((a[:, None] > b[None, :]).sum())
    lt = int((a[:, None] < b[None, :]).sum())
    return (gt - lt) / (a.size * b.size)


def contrast(df: pd.DataFrame, group_col: str = "group"):
    deltas, pvals = [], []
    for key, _ in PARAMS:
        a = df.loc[df[group_col] == "A", key].astype(float)
        b = df.loc[df[group_col] == "B", key].astype(float)
        a, b = a.dropna(), b.dropna()
        if len(a) < 3 or len(b) < 3:
            deltas.append(np.nan)
            pvals.append(np.nan)
            continue
        deltas.append(cliffs_delta(a.values, b.values))
        pvals.append(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
    return np.array(deltas), np.array(pvals), benjamini_hochberg(np.array(pvals))


def power_curve(deltas, ns=(10, 30, 60, 100, 150), alpha=0.05 / 12, iters=1500,
                seed=20260901):
    """Simulated Mann-Whitney power at the observed effect sizes.

    Two normals are separated to reproduce each observed Cliff's delta as an
    AUC, which is what makes "the benchmark could not have seen this" a
    quantitative statement rather than an assertion.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for (key, label), d in zip(PARAMS, deltas):
        if np.isnan(d) or abs(d) < 1e-9:
            continue
        auc = (abs(d) + 1) / 2
        sep = stats.norm.ppf(min(auc, 0.999)) * np.sqrt(2)
        row = {"parameter": label, "delta": d}
        for n in ns:
            hits = 0
            for _ in range(iters):
                x = rng.normal(0, 1, n)
                y = rng.normal(sep, 1, n)
                if stats.mannwhitneyu(x, y, alternative="two-sided").pvalue < alpha:
                    hits += 1
            row[f"n={n}"] = hits / iters
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrix", default=str(HERE / "data/parameters_sensitivity_n150.csv"))
    ap.add_argument("--fma", default=str(HERE / "data/parameters_sensitivity_fma150.csv"),
                    help="independent-corpus draw; pass '' to skip it")
    ap.add_argument("--power", action="store_true",
                    help="also simulate power at the observed effect sizes")
    args = ap.parse_args()

    df = pd.read_csv(args.matrix)
    n_a = int((df["group"] == "A").sum())
    n_b = int((df["group"] == "B").sum())
    print(f"{len(df)} tracks — group A n={n_a}, group B n={n_b}")
    if "arousal" in df.columns:
        for g in ("A", "B"):
            s = df.loc[df["group"] == g, "arousal"]
            print(f"  group {g}: annotated arousal {s.min():.2f}-{s.max():.2f}")
    print()

    deltas, pvals, qvals = contrast(df)
    print(f"{'parameter':24} {'delta':>7} {'p':>10} {'q (BH)':>10}")
    print("-" * 54)
    order = np.argsort([abs(d) if not np.isnan(d) else -1 for d in deltas])[::-1]
    for i in order:
        _, label = PARAMS[i]
        star = " *" if qvals[i] < 0.05 else "  "
        print(f"{label:24} {deltas[i]:>+7.2f} {pvals[i]:>10.2e} {qvals[i]:>10.3f}{star}")

    surviving = int(np.nansum(qvals < 0.05))
    print(f"\n{surviving}/12 survive Benjamini-Hochberg at 0.05"
          f"  (the 60-track benchmark: 0/12, smallest q = 0.19)")
    print("* = survives correction")

    fma_path = Path(args.fma) if args.fma else None
    if fma_path is not None and fma_path.exists():
        fma = pd.read_csv(fma_path)
        f_d, _, f_q = contrast(fma)
        print(f"\nIndependent corpus (FMA, ambient/drone/minimal vs the rest, "
              f"n={int((fma['group']=='A').sum())} each):")
        print(f"{'parameter':24} {'delta':>7} {'q (BH)':>10}   agrees on sign")
        print("-" * 62)
        for i, (_, label) in enumerate(PARAMS):
            agree = ""
            if not (np.isnan(f_d[i]) or np.isnan(deltas[i])):
                agree = "yes" if np.sign(f_d[i]) == np.sign(deltas[i]) else "NO"
            star = " *" if f_q[i] < 0.05 else "  "
            print(f"{label:24} {f_d[i]:>+7.2f} {f_q[i]:>10.3f}{star}   {agree}")
        both = sum(1 for i in range(len(PARAMS))
                   if not (np.isnan(f_d[i]) or np.isnan(deltas[i]))
                   and np.sign(f_d[i]) == np.sign(deltas[i]))
        print(f"\n{int(np.nansum(f_q < 0.05))}/12 survive BH here; "
              f"{both}/12 agree on sign with the DEAM draw")

    if args.power:
        print("\nSimulated power at these effect sizes "
              "(alpha = 0.05/12, two-sided Mann-Whitney):")
        pc = power_curve(deltas)
        print(pc.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
