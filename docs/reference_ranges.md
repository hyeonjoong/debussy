# Reference ranges

DEBUSSY grades each analysis against the three-tier framework of the companion
review. The tiers come from a four-dimension evidence score — Effect Evidence,
Mechanistic Confirmation, Appraisal Independence, Designability — summed to
0–12 per parameter:

| Composite score | Tier | Meaning |
|---|---|---|
| 9–12 | **Tier 1** | Universal fixed design principles |
| 5–8 | **Tier 2** | Established direction, but optimise per individual |
| 0–4 | **Tier 3** | Exploratory adjuncts; further validation needed |

Tier 1 is the only gate that can fail. Tiers 2 and 3 are reported.

## Tier 1 — universal design checks

| Parameter | Score | Design strategy | How DEBUSSY grades it |
|---|---|---|---|
| **Roughness** | 12 | Minimise; target < 0.3 asper | mean < 0.3 asper **and** ≤ 2 % of duration above it |
| **Event structure** | 11 | Stable mean level; minimise transients | `INFO` — dynamic range + crest reported, not gated |
| **Onset dynamics** | 11 | Gradual attack; onset-to-peak > ~50 ms | attack **median** > 50 ms |
| **Predictability** † | 9 | Regular patterns; avoid abrupt structural change | `MANUAL` — structural, not auto-detectable |

† Predictability sits at the Tier-1 lower boundary. It is placed in Tier 1
because predictive-coding mechanisms are appraisal-independent — they operate
automatically regardless of musical background.

### Roughness status logic

| Time above 0.3 asper | Status |
|---|---|
| ≤ 2 % | PASS |
| 2–10 % | CAUTION (intermittent) |
| > 10 % | FAIL (frequent) |

A high whole-file mean fails regardless of coverage — the verdict is the *more
severe* of the two, so coverage can only make it more conservative, never
rescue a high mean. On long files coverage is sampled from probes, so a clean
reading is never certified: the status is capped at CAUTION.

The 0.3 asper threshold follows the amygdala-activation roughness literature.
The 2 % / 10 % coverage bands are **provisional screening heuristics, not
validated cut-offs**.

### Attack status logic

The verdict is the median-onset rule (> 50 ms). A high share of sub-50 ms onsets
can downgrade a PASS to CAUTION, but only when the pattern is both substantial
(> 25 % of onsets) and non-incidental (n ≥ 5). It never fails on its own:
envelope rise time ignores absolute level, so it describes onset shape rather
than measuring startle.

## Tier 2 — directional guidelines

Direction is established; the optimum is person- and context-specific, so these
are reported in-range vs out-of-range rather than passed or failed.

| Parameter | Score | Design strategy |
|---|---|---|
| **Tempo / rhythm** ‡ | 10 | Default 60–80 BPM; adapt toward individual resting heart rate |
| **Sharpness** | 8 | Limit energy above 3–4 kHz (provisional target) |
| **Pitch** | 7 | Low-mid frequency centre; descending contours |
| **Spectral slope** | 6 | Negative slope; avoid flat-spectrum noise |
| **Complexity** | 5 | Low-complexity instrumental textures |
| **Semantic content** | 5 | Instrumental by default; lyrics only if controlled |

‡ Tempo scores 10, inside the Tier-1 band, but is assigned to Tier 2 because
musical training and cultural rhythmic conventions modulate the tempo–arousal
relationship, which rules out a universal fixed value.

DEBUSSY reports spectral centroid as the measured stand-in for pitch height, and
lyrics presence for semantic content.

## Tier 3 — exploratory

| Parameter | Score | Why not prescribable |
|---|---|---|
| **Harmonicity / HNR** | 3 | Tonal clarity raises pleasantness, but large cross-cultural variation |
| **Familiarity** | 2 | Reward activation observed; direction depends on the individual |

Spectral flatness is reported here too: it earns a slot in the reporting
guideline as the tonal-to-noise continuum measure, without a design threshold.

## Programmatic access

```python
from debussy import tier1_items, tier2_items, tier3_items, format_compliance

for item in tier1_items(result):
    print(item["parameter"], item["status"], item["note"])

print(format_compliance(result))   # printable summary
```

Each item carries `parameter`, `value`, `unit`, `target`, `status` and `note`.
Tier-1 statuses are `PASS`, `CAUTION`, `FAIL`, `INFO`, `MANUAL` or `N/A`.
