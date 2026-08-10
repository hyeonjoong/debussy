#!/usr/bin/env python3
"""Run DEBUSSY over the validation benchmark and write the per-track parameter matrix.

Reads an audio manifest (``Track_ID``, ``Output_file``, and descriptive columns),
calls :func:`debussy.analyze_audio` on each standardised WAV, and writes one row
per track with all reporting parameters plus run metadata.

This reproduces ``data/parameters_60tracks.csv``. The audio itself is not
redistributable — see README.md for how to obtain and standardise it.

Usage
-----
    python validation/run_validation.py --audio-dir path/to/audio_standardized
    python validation/run_validation.py --audio-dir AUDIO --out-dir results/
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from debussy import analyze_audio

HERE = Path(__file__).resolve().parent

# Identifiers first, then the reporting parameters in paper-table order, then meta.
COLUMN_ORDER = [
    "Track_ID", "Subcategory", "Source_ID", "Artist", "Title", "Genre",
    "file", "duration_s", "sample_rate",
    "laeq_dbfs_a", "dynamic_range_db", "crest_factor_db",
    "attack_mean_ms", "attack_median_ms", "attack_sd_ms", "attack_n_onsets",
    "roughness_asper",
    "tempo_bpm", "modulation_peak_hz",
    "spectral_centroid_hz", "sharpness_acum", "spectral_slope_beta",
    "hnr_db", "spectral_flatness",
    "lyrics", "delivery", "notes", "_process_seconds",
]

CARRY_OVER = ["Track_ID", "Subcategory", "Source_ID", "Artist", "Title", "Genre"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--audio-dir", required=True, type=Path,
                    help="Directory holding the standardised WAV files named in the manifest")
    ap.add_argument("--manifest", type=Path, default=HERE / "data" / "audio_manifest.csv",
                    help="Audio manifest CSV (default: data/audio_manifest.csv)")
    ap.add_argument("--out-dir", type=Path, default=HERE / "results",
                    help="Where to write the parameter matrix (default: validation/results)")
    args = ap.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(args.manifest)
    print(f"Manifest: {args.manifest}  ({len(manifest)} tracks)")
    print(f"Audio:    {args.audio_dir}")

    rows, errors = [], []
    started = time.time()
    for i, row in manifest.iterrows():
        wav = args.audio_dir / row["Output_file"]
        if not wav.exists():
            print(f"[{i + 1}/{len(manifest)}] MISSING {row['Track_ID']}: {wav.name}")
            errors.append({"Track_ID": row["Track_ID"], "error": "audio file not found"})
            continue
        t0 = time.time()
        try:
            # suppress_warnings keeps the batch log readable; the resample notice
            # and any clipping warning are recorded per row in `notes` regardless.
            result = analyze_audio(str(wav), delivery_method="instrumental_or_unknown",
                                   suppress_warnings=True)
        except Exception as exc:  # noqa: BLE001 - report and continue the batch
            print(f"[{i + 1}/{len(manifest)}] FAILED  {row['Track_ID']}: "
                  f"{type(exc).__name__}: {exc}")
            errors.append({"Track_ID": row["Track_ID"],
                           "error": f"{type(exc).__name__}: {exc}"})
            continue
        record = asdict(result)
        record.update({k: row[k] for k in CARRY_OVER if k in manifest.columns})
        record["_process_seconds"] = round(time.time() - t0, 2)
        rows.append(record)
        print(f"[{i + 1}/{len(manifest)}] ok      {row['Track_ID']}: "
              f"LAeq={result.laeq_dbfs_a:.1f} dBFS-A, "
              f"centroid={result.spectral_centroid_hz:.0f} Hz "
              f"({record['_process_seconds']:.1f}s)")

    elapsed = time.time() - started
    if not rows:
        print("No tracks analysed — check --audio-dir.")
        return 1

    frame = pd.DataFrame(rows)
    frame = frame[[c for c in COLUMN_ORDER if c in frame.columns]]
    out_csv = args.out_dir / "parameters.csv"
    frame.to_csv(out_csv, index=False)

    metadata = {
        "n_input": int(len(manifest)),
        "n_success": int(len(rows)),
        "n_failed": int(len(errors)),
        "elapsed_minutes": round(elapsed / 60, 2),
        "mean_seconds_per_track": round(elapsed / len(manifest), 2),
    }
    (args.out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"\n{len(rows)}/{len(manifest)} analysed in {elapsed / 60:.1f} min")
    print(f"  parameters   -> {out_csv}")
    print(f"  run metadata -> {args.out_dir / 'run_metadata.json'}")
    if errors:
        err_csv = args.out_dir / "errors.csv"
        pd.DataFrame(errors).to_csv(err_csv, index=False)
        print(f"  errors       -> {err_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
