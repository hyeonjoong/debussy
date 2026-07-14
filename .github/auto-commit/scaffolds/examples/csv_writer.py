#!/usr/bin/env python3
"""Minimal example: analyse one or more files and append them to a CSV.

Usage
-----
    python examples/csv_writer.py stim1.wav stim2.wav -o report.csv

The CSV columns are exactly the fields of :class:`debussy.Result`, matching the
per-track schema used in the paper's validation table.
"""
from __future__ import annotations

import argparse

from debussy import analyze_audio, write_csv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Analyse files and write a CSV report")
    ap.add_argument("files", nargs="+", help="Audio files to analyse")
    ap.add_argument("-o", "--out", default="debussy_report.csv", help="Output CSV path")
    args = ap.parse_args(argv)

    results = [analyze_audio(f, suppress_warnings=True) for f in args.files]
    write_csv(results, args.out)
    print(f"wrote {len(results)} row(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
