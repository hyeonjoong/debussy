#!/usr/bin/env python3
"""Analyse one or more files and export each Result as JSON.

Usage
-----
    python examples/json_export.py stim.wav -o out.json       # single object
    python examples/json_export.py a.wav b.wav -o out.json    # JSON array
    python examples/json_export.py stim.wav                   # print to stdout

Uses Result.to_dict(); the payload round-trips back to an equal Result via
``debussy.Result(**obj)``.
"""
from __future__ import annotations

import argparse
import json

from debussy import analyze_audio


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Export DEBUSSY analyses as JSON")
    ap.add_argument("files", nargs="+", help="Audio files to analyse")
    ap.add_argument("-o", "--out", help="Write JSON here instead of stdout")
    ap.add_argument("--indent", type=int, default=2, help="JSON indent (default 2)")
    args = ap.parse_args(argv)

    results = [analyze_audio(f, suppress_warnings=True).to_dict() for f in args.files]
    payload = results[0] if len(results) == 1 else results
    text = json.dumps(payload, indent=args.indent, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
