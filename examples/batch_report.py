#!/usr/bin/env python3
"""Batch-analyse every audio file in a folder and print a compact table.

Usage
-----
    python examples/batch_report.py path/to/folder [--csv out.csv]

Demonstrates the public API end to end: :func:`debussy.analyze_audio` per file
plus :func:`debussy.write_csv` for a tidy per-track export in the paper's schema.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

from debussy import analyze_audio, write_csv

AUDIO_EXTS = (".wav", ".flac", ".ogg", ".aiff", ".aif")


def _fmt(v, spec):
    return format(v, spec) if v is not None and not (isinstance(v, float) and math.isnan(v)) else "—"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Batch DEBUSSY analysis over a folder")
    ap.add_argument("folder", help="Folder containing audio files")
    ap.add_argument("--csv", help="Also write per-track rows to this CSV (paper schema)")
    ap.add_argument("--suppress-warnings", action="store_true",
                    help="Silence mosqito resample / clipping notices")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.folder):
        print(f"not a folder: {args.folder}", file=sys.stderr)
        return 2

    paths = sorted(
        os.path.join(args.folder, f)
        for f in os.listdir(args.folder)
        if f.lower().endswith(AUDIO_EXTS)
    )
    if not paths:
        print(f"no audio files ({', '.join(AUDIO_EXTS)}) in {args.folder}", file=sys.stderr)
        return 1

    results = []
    header = f"{'file':<28} {'LAeq':>8} {'crest':>7} {'centroid':>9} {'rough':>7}"
    print(header)
    print("-" * len(header))
    for p in paths:
        r = analyze_audio(p, suppress_warnings=args.suppress_warnings)
        results.append(r)
        print(f"{os.path.basename(p):<28} "
              f"{_fmt(r.laeq_dbfs_a, '>8.2f')} "
              f"{_fmt(r.crest_factor_db, '>7.2f')} "
              f"{_fmt(r.spectral_centroid_hz, '>9.1f')} "
              f"{_fmt(r.roughness_asper, '>7.3f')}")

    if args.csv:
        write_csv(results, args.csv)
        print(f"\nwrote {len(results)} row(s) to {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
