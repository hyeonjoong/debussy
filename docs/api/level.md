# Level

**Reporting item 1 — LAeq + dynamic range.** Plus crest factor as a diagnostic.

```python
from debussy.level import laeq_dbfs, dynamic_range_db, a_weighting_filter
```

## `laeq_dbfs(y, fs) -> float`

A-weighted equivalent continuous level, in **dBFS-A** — full-scale relative, not
absolute SPL. The A-weighting filter follows IEC 61672-1, applied as a
second-order-section cascade.

Digital audio carries no absolute reference, so an uncalibrated LAeq is only
comparable *within* a set of files produced the same way. For true dB SPL,
measure a reference tone through your playback chain and pass the difference as
`calibration_offset_db` to `analyze_audio()`; it is added to LAeq and recorded in
`Result.notes`.

## `dynamic_range_db(y, fs, win_ms=50.0) -> float`

The 95th minus the 5th percentile of short-term RMS level, on 50 ms windows with
50 % overlap. Percentiles rather than peak-to-trough, so a single click does not
dominate. Returns `0.0` for signals shorter than one window.

Lower values mean a more even stimulus; the companion review treats a stable
mean level with minimal transients as part of the Tier-1 event-structure check.

## `a_weighting_filter(fs)`

Returns the SOS coefficients used above, if you want to apply the weighting
yourself.

## Crest factor

Not a separate function — `analyze_audio()` computes it as
`20·log₁₀(peak / RMS)` and reports it in `Result.crest_factor_db`. It is a
diagnostic rather than a guideline item: high crest with low dynamic range
indicates isolated transients on an otherwise even bed.

## Long files

For recordings past the full-analysis threshold, level metrics are **not**
estimated from probes — they are computed exactly over the whole file by
streaming it in blocks. A long ambient piece reports the same LAeq and dynamic
range it would if analysed in one pass.
