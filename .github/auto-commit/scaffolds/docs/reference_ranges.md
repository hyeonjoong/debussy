# Reference ranges

The three-tier framework grades each analysis against published or provisional
ranges. Tier 1 is the only hard pass/fail gate; Tiers 2–3 are directional.

## Tier 1 — universal design checks

| Parameter | Target | Status logic |
|---|---|---|
| Roughness | mean `< 0.3` asper **and** `≤ 2 %` of time above 0.3 asper | ≤ 2 % → PASS, 2–10 % → CAUTION, > 10 % → FAIL; a high whole-file mean fails regardless |
| Attack time (median) | median `> 50` ms | ≤ 50 ms → FAIL; a high share of sub-50 ms onsets (> 25 %, n ≥ 5) downgrades PASS → CAUTION |
| Event structure | lower dynamic range / crest = calmer | INFO (reported, not gated) |
| Predictability | structural | MANUAL (human assessment) |

The 0.3 asper threshold follows the amygdala-activation roughness literature; the
per-frame coverage bands (2 % / 10 %) are provisional screening heuristics, not
validated cut-offs. On long files the coverage figure is sampled from probes, so
a "clean" verdict is never certified automatically (the roughness status is
capped at CAUTION).

## Tier 2 — directional guidelines

Sharpness (acum) and spectral centroid follow Zwicker & Fastl (2007): lower values
are generally calmer, but the optimum is person- and context-specific, so Tier 2
reports in-range vs out-of-range rather than pass/fail. See `paper/paper.md` for
the ranges used and their sources.

## Tier 3 — exploratory

HNR, spectral slope, spectral flatness, tempo and modulation rate are reported
without a threshold — they characterise the stimulus for later per-participant
tuning. Use `tier1_items(r)`, `tier2_items(r)` and `tier3_items(r)` to obtain the
graded items programmatically, or `format_compliance(r)` for a printable summary.
