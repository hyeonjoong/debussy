# Validation

DEBUSSY's parameter set was validated on a 60-track benchmark spanning the
stimulus families used in the BELL-001 protocol (breath / ambient / musical
excerpts). The benchmark exists to check two things:

1. **Numerical stability** — every parameter is finite and reproducible across
   repeated runs and across the 44.1 kHz / 48 kHz sample rates commonly found in
   stimulus libraries (mosqito resamples internally to 48 kHz; see the
   [resample notes](#sample-rate-handling)).
2. **Discrimination** — the parameters separate acoustically different material
   in the directions predicted by the psychoacoustic literature (e.g. higher
   roughness and sharpness for harsher excerpts).

## The 60-track benchmark

Three categories, all standardised to 44.1 kHz mono 16-bit PCM WAV before
analysis:

| Category | Material | *n* |
|---|---|---|
| A — "relaxation" | DEAM static-annotation corpus, low-arousal subset | 10 |
| B — "frequently listened" | DEAM mid-to-high arousal + genre-stratified FMA-medium subset | 30 |
| C — clinical | BELL-001 SleepThera breath-paced biofeedback stimuli | 20 |

The pipeline produced a complete set of measured values for **58 of 60 tracks**.
The two exceptions are ~10 s breath clips with no autocorrelation peak above the
voicing gate, so HNR is undefined for them rather than wrong.

Two commercial reference lists are excluded pending separate licensing; adding
them would bring group A to *n*=30. Tracking issue:
[#9](https://github.com/hyeonjoong/debussy/issues/9).

## What the benchmark shows

The **A-vs-B contrast is exploratory and underpowered**. Three parameters reach
uncorrected *p* < 0.05, but none survive Benjamini–Hochberg correction across
the twelve tests (smallest *q* = .19), and group A is small.

!!! warning "Do not read the A-vs-B effect sizes as findings"

    At *n*=10 versus *n*=30 the δ values are unstable in **sign**, not merely
    in magnitude. Redrawn at 150 per group **within the same arousal bands** —
    so the only thing that changed is *n* — **eleven of twelve** parameters
    separate, and four reverse sign: LAeq, spectral centroid, sharpness and
    spectral flatness all move from positive to strongly negative. A second
    draw at the arousal extremes and an independent corpus (FMA) agree on the
    direction.

    Simulated power explains the discrepancy rather than excusing it: at the
    effect sizes actually present, the published design had **11–30 % power**,
    so its null was uninformative and its signs were close to coin flips.

    Run `python validation/sensitivity_power.py --power` for the full table.
    The 60-track benchmark itself is unchanged; this is an additional analysis,
    not a correction to the released data.

**Category C separates far more sharply**, with very large effect sizes
(|δ| ≥ 0.7) against *both* music categories on **seven of the twelve measured
quantities** — LAeq, dynamic range, attack-time median, roughness, sharpness,
spectral slope β and spectral flatness. Crest factor is close behind
(δ = +0.81 against A, +0.68 against B). This is the acoustic fingerprint
expected of quiet, dynamically wide, sharp-onset breath recordings, and it is
detected across all four family modules.

The point of the benchmark is *not* a substantive claim about music or breath
stimuli — that belongs to the companion review. It is evidence that every
parameter returns a sensible, bounded, finite-variance distribution on
acoustically very different material.

## Reference ranges

The per-parameter reference values used by the tier check are tabulated in
[reference_ranges.md](reference_ranges.md). They follow Zwicker & Fastl (2007)
for sharpness and roughness and the companion review for the level, spectral,
and temporal descriptors. They are **reference values the reviewed literature
reports**, not validated cut-offs — and only Tier 1 is graded pass/fail.

## Reproducing the benchmark

The benchmark tracks are analysed exactly as any short file — in full, byte for
byte — so the published values are reproducible from the public API:

```python
from debussy import analyze_audio, write_csv

results = [analyze_audio(p) for p in benchmark_paths]
write_csv(results, "benchmark.csv")
```

See `examples/batch_report.py` for a folder-level driver. The manifest, the raw
per-track parameter matrix and the scripts that regenerate both are released in
`validation/`; `paper/paper.md` carries the summary figure.

## Sample-rate handling

Level and spectral descriptors are computed at the file's native rate. The
psychoacoustic descriptors (roughness, sharpness) are computed by mosqito, which
requires 48 kHz and resamples other rates internally, printing a one-line notice.
Pass `suppress_warnings=True` to silence it in batch runs. The reported
`sample_rate` is always the file's native rate.
