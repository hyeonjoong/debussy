# Validation

DEBUSSY's parameter set was validated on a 60-track benchmark spanning the
stimulus families used in the BELL-001 protocol (breath / ambient / musical
excerpts). The benchmark exists to check two things:

1. **Numerical stability** — every parameter is finite and reproducible across
   repeated runs and across the 44.1 kHz / 48 kHz sample rates commonly found in
   stimulus libraries (mosqito resamples internally to 48 kHz; see the
   [resample notes](#sample-rate-handling)).
2. **Discrimination** — the parameters separate calm from arousing material in
   the directions predicted by the psychoacoustic literature (e.g. higher
   roughness and sharpness for harsher excerpts).

## Reference ranges

The per-parameter reference ranges used by the three-tier compliance check are
tabulated in [reference_ranges.md](reference_ranges.md). They follow Zwicker &
Fastl (2007) for sharpness and roughness and the paper's own analysis for the
level, spectral, and temporal descriptors. The ranges are **directional
guidance**, not hard cut-offs — Tier 1 is the only pass/fail gate.

## Reproducing the benchmark

The benchmark tracks are analysed exactly as any short file — in full, byte for
byte — so the published values are reproducible from the public API:

```python
from debussy import analyze_audio, write_csv

results = [analyze_audio(p) for p in benchmark_paths]
write_csv(results, "benchmark.csv")
```

See `examples/batch_report.py` for a folder-level driver. The numeric summary
and figures are maintained in `paper/paper.md`; this page is updated as the
licensed A1 (Mindlab) and A3 (commercial-reference) sets are processed.

## Sample-rate handling

Level and spectral descriptors are computed at the file's native rate. The
psychoacoustic descriptors (roughness, sharpness) are computed by mosqito, which
requires 48 kHz and resamples other rates internally, printing a one-line notice.
Pass `suppress_warnings=True` to silence it in batch runs. The reported
`sample_rate` is always the file's native rate.
