# API overview

Almost all use goes through one function.

```python
from debussy import analyze_audio

result = analyze_audio("stimulus.wav")
```

## `analyze_audio()`

```python
analyze_audio(
    audio_file: str,
    delivery_method: str = "unknown",
    lyrics_presence: str | None = None,
    calibration_offset_db: float = 0.0,
    suppress_warnings: bool = False,
) -> Result
```

| Argument | Meaning |
|---|---|
| `audio_file` | Path to a WAV/FLAC/OGG file readable by `soundfile`. |
| `delivery_method` | Reporting item 10 — free text, e.g. `headphones`, `free-field`, `binaural`. Recorded, not measured. |
| `lyrics_presence` | Reporting item 9 — `"yes"`, `"no"`, or `None`/anything else → `"unknown"`. |
| `calibration_offset_db` | dB added to LAeq for SPL calibration. Default `0` leaves LAeq in dBFS-A. |
| `suppress_warnings` | Silences the 48 kHz resample notice and the full-scale clipping warning. |

`analyse()` is a backward-compatible alias with the same behaviour.

## The `Result` dataclass

Every field, keyed to the eleven-item guideline:

| Item | Fields |
|---|---|
| 1 · LAeq + dynamic range | `laeq_dbfs_a`, `dynamic_range_db` |
| 2 · Attack time | `attack_mean_ms`, `attack_median_ms`, `attack_sd_ms`, `attack_n_onsets` |
| 3 · Roughness | `roughness_asper` |
| 4 · Tempo / modulation | `tempo_bpm`, `modulation_peak_hz` |
| 5 · Spectral centroid | `spectral_centroid_hz` |
| 6 · Sharpness | `sharpness_acum` |
| 7 · Spectral slope | `spectral_slope_beta` |
| 8 · Harmonicity | `hnr_db` |
| 9 · Lyrics presence | `lyrics` |
| 10 · Delivery method | `delivery` |
| 11 · Spectral flatness | `spectral_flatness` |

Beyond the guideline: `crest_factor_db`, the temporal-coverage descriptors
(`roughness_coverage_pct`, `sharp_onset_pct`, `sharp_onset_count`), and run
metadata (`file`, `duration_s`, `sample_rate`, `analysis_mode`, `notes`).

**Any measured field may be `None`** when the input cannot support it — a pure
tone has no amplitude modulation, a clip too short for the voicing gate has no
HNR. Check before arithmetic. `notes` records why.

### Serialisation

```python
result.to_dict()            # plain dict of every field
result.to_json(indent=2)    # JSON string; indent=None for one line
```

`json.loads(r.to_json()) == r.to_dict()`, and `Result(**r.to_dict())`
reconstructs an equal `Result`.

## Tier framework

```python
from debussy import tier1_items, tier2_items, tier3_items, format_compliance
```

Each returns a list of dicts with `parameter`, `value`, `unit`, `target`,
`status` and `note`. `format_compliance(result)` renders a printable summary,
`tier1_compliance(result)` gives the machine-readable verdict.

Tier membership follows the companion review: **Tier 1** is the universal design
check (roughness, onset dynamics, event structure, predictability), **Tier 2**
directional guidelines, **Tier 3** exploratory. See
[Reference ranges](../reference_ranges.md) for the thresholds.

## Batch output

```python
from debussy import write_csv
write_csv([r1, r2, r3], "report.csv")   # appends; header written once
```

## Family submodules

The per-family functions below are the building blocks `analyze_audio()`
orchestrates. Reach for them when you want one quantity without running the
whole pipeline.

- [Level](level.md) — LAeq, dynamic range
- [Envelope](envelope.md) — attack time, tempo, modulation rate
- [Spectral](spectral.md) — centroid, slope β
- [Tonal](tonal.md) — HNR, spectral flatness
- [Psychoacoustic](psychoacoustic.md) — roughness, sharpness

## Plotting

`plot_spectrogram`, `plot_parameter_radar`, `plot_tier_compliance` and
`plot_coverage` return matplotlib figures.
