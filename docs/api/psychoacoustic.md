# Psychoacoustic

**Reporting item 3 — roughness** and **item 6 — sharpness.** Both delegate to
[MOSQITO](https://mosqito.readthedocs.io/) for the validated reference
implementations.

```python
from debussy.psychoacoustic import psychoacoustics
```

## `psychoacoustics(y, fs, suppress_warnings=False) -> dict`

One call returns both metrics:

| Key | Metric | Model |
|---|---|---|
| `roughness_asper` | Roughness, asper | Daniel & Weber (1997), `mosqito.roughness_dw` |
| `sharpness_acum` | Sharpness, acum | DIN 45692, `mosqito.sharpness_din_st` |
| `roughness_coverage_pct` | % of duration above 0.3 asper | derived from the roughness time series |

Either value may be `None` on inputs where the model degenerates — a pure tone
has no amplitude modulation for the roughness integrator to work on. The failure
reason is recorded in `Result.notes` rather than raised.

## Roughness is the Tier-1 gate

Roughness scored highest of all twelve reviewed parameters (12/12) and is the
strongest single Tier-1 constraint: 30–150 Hz amplitude modulation drives
amygdala threat-detection responses. The target is **mean < 0.3 asper**.

`roughness_coverage_pct` exists because a mean can hide things. A stimulus that
is calm for four minutes and harsh for ten seconds can average below threshold
while still containing the passage that matters. The Tier-1 verdict therefore
takes the **more severe** of the whole-file mean and the proportion of time
above 0.3 asper — coverage can only make a verdict more conservative, never
rescue a high mean.

The 2 % / 10 % coverage bands are **provisional screening heuristics**, not
validated cut-offs.

## Sample rate

MOSQITO's models require 48 kHz and resample internally when given anything
else. DEBUSSY emits a `UserWarning` when that happens — `suppress_warnings=True`
silences it. `Result.sample_rate` always reports the file's native rate.

## Dependency note

MOSQITO imports `matplotlib` inside both of these calls without declaring it, so
`matplotlib` is a **required** dependency of DEBUSSY. Without it both metrics
silently returned `None` before v0.2.1.
