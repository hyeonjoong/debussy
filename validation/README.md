# Validation benchmark

This directory holds the artefacts behind the validation section of the DEBUSSY
paper: the audio manifest, the raw per-track parameter matrix, the summary
statistics, and the two scripts that regenerate them.

The point of the benchmark is **not** to make a substantive claim about music or
breath stimuli — that is the role of the parent review. It is to show that every
one of the twelve reporting parameters returns a sensible, bounded,
finite-variance value across acoustically very different material, and that the
parameters together separate categories when real acoustic differences exist.

## The 60-track benchmark

| Group | Subcategory | *n* | Source |
|---|---|---|---|
| **A** | Relaxation | 10 | DEAM low-arousal subset |
| **B** | Frequently listened | 15 + 15 | DEAM mid-to-high arousal; FMA-medium (genre-stratified) |
| **C** | Clinical stimuli | 20 | BELL-001 SleepThera breath-paced biofeedback set |

All audio was standardised to 44.1 kHz mono 16-bit PCM WAV before analysis.

## Files

| File | Contents |
|---|---|
| `data/audio_manifest.csv` | One row per track: ID, subcategory, source ID, durations, output filename, artist/title/genre |
| `data/parameters_60tracks.csv` | Raw per-track output of `analyze_audio()` — every reporting parameter plus run metadata |
| `data/summary_statistics.csv` | Per-parameter medians, Cliff's δ and Mann–Whitney *p* for A-vs-B, and δ for C-vs-A / C-vs-B |
| `data/run_metadata.json` | Category counts and timing for the published run (2026-05-27) |
| `run_validation.py` | Manifest + audio → parameter matrix |
| `analyze_results.py` | Parameter matrix → summary statistics + distribution figure |

## Reproducing

`analyze_results.py` runs directly on the published matrix — no audio needed:

```bash
pip install -e ".[plot]" pandas
python validation/analyze_results.py            # writes validation/results/
python validation/analyze_results.py --no-figure  # statistics only, no matplotlib
```

This reproduces the summary statistics and the twelve-panel distribution figure,
including the Benjamini–Hochberg correction across the twelve A-vs-B tests.

To regenerate the parameter matrix from audio you need the standardised WAVs:

```bash
python validation/run_validation.py --audio-dir path/to/audio_standardized
```

## Audio availability

The audio is **not redistributed here**, for licensing reasons:

- **DEAM** (groups A, B) — available from the [DEAM dataset page](https://cvml.unige.ch/databases/DEAM/)
  under its own terms. `Source_ID` in the manifest is the DEAM track ID.
- **FMA-medium** (group B) — available from the
  [FMA repository](https://github.com/mdeff/fma); `Source_ID` is the FMA track ID.
- **BELL-001 SleepThera** (group C) — proprietary clinical-trial stimuli owned by
  Bell Therapeutics; not publicly redistributable. The manifest and the resulting
  parameter rows are published so the analysis remains fully checkable even
  though the source audio is not open.

Given the source files, `standardize_audio` conversion is a plain resample to
44.1 kHz mono 16-bit PCM; the manifest records the original and output durations
for every track so the standardisation step can be verified.

## Known limitations

- Two of the sixty tracks (`C017`, `C020`) return `hnr_db = None`: they are
  ~10 s breath clips with no autocorrelation peak above the voicing gate. All
  other parameters are present for every track (58/60 complete on all twelve).
- Group A is small (*n* = 10) and the A-vs-B contrast is underpowered — three
  parameters reach uncorrected *p* < 0.05 but none survive BH correction
  (smallest *q* = 0.19). Treat A-vs-B as exploratory.
- Two commercial reference lists (Mindlab Top 10 and a clinical/research-cited
  relaxation set) are excluded pending separate licensing; adding them would
  bring group A to *n* = 30.
