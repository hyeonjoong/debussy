# Reference ranges

DEBUSSY grades each analysis against the three-tier framework of the companion
review. This page has two halves, and the distinction between them is the most
important thing on it:

- **The evidence table** below is the review's. It says which parameters have
  which kind of support, and how strong a design claim each one licenses.
- **The screening values** further down are DEBUSSY's own. The review labels
  every number it quotes as a *reference value* or *exemplar* drawn from the
  cited studies, and states explicitly that what the evidence supports is the
  direction of each principle, not its cut-point. DEBUSSY still has to answer a
  yes/no admissibility question, so it adopts those reference values as the
  defaults of its own screening rubric.

So a `FAIL` from DEBUSSY means *"outside the range the cited literature
reports"*. It does not mean *"shown to raise autonomic arousal"*. No study in
the reviewed literature has manipulated attack time or roughness parametrically
while measuring an autonomic outcome, and the review says so.

The reporting guideline that DEBUSSY implements is independent of this
hierarchy: its eleven items were selected for measurability and tool
availability, not for their tier scores, and two of them correspond to a Tier-3
parameter or to a descriptor the review does not score at all. A reader who
rejects the tier assignments entirely has no reason to reject the guideline.

<!-- BEGIN GENERATED: evidence-table (tools/gen_reference_ranges.py) -->

*This section is generated from `src/debussy/_tiers.py`. Edit the scores there, then run `python tools/gen_reference_ranges.py`.*

Scores are the audited values from the companion review's score-audit table. **EE** Effect Evidence (0–4), **MC** Mechanistic Confirmation (0–3), **AI** Appraisal Independence (0–3), **D** Designability (0–2); composite = their sum, in 0–12. The **evidence axis** (EE+MC+AI) drops Designability, which measures tractability rather than evidence.

| Composite | Tier | Meaning |
|---|---|---|
| 9–12 | **Tier 1** | fixed design constraints |
| 5–8 | **Tier 2** | directional, optimum set per listener |
| 0–4 | **Tier 3** | exploratory adjuncts |

**Boundary rule.** A parameter scoring in the Tier-1 band is held in Tier 2 if and only if **AI < 3**. Tier 1 means one fixed value serves every listener, so a parameter whose optimum must be chosen per listener cannot sit there however strong its evidence.

The rule currently touches **Tempo / rhythm** — composite 10, AI 2.

## Tier 1 — fixed design constraints

One value serves every listener. These are the only parameters DEBUSSY grades pass/fail.

| Parameter | EE | MC | AI | D | Composite | Axis | Evidence class | Design implication |
|---|---:|---:|---:|---:|---:|---:|---|---|
| **Event structure** | 4 | 2 | 3 | 2 | 11 | 9 | Direct | Monotone — minimise transient Lmax and event rate. |
| **Onset dynamics** | 3 | 3 | 3 | 2 | 11 | 9 | Direct | Monotone — slower attack; no listener-specific value needed. |
| **Roughness** | 2 | 3 | 3 | 2 | 10 | 8 | Indirect | Monotone — minimise. |
| **Predictability** | 3 | 2 | 3 | 1 | 9 | 8 | Direct | Monotone — maximise structural regularity. |

- **Event structure** — Three independent paradigms (polysomnography, simultaneous autonomic recording, epidemiology) with direct autonomic outcomes in more than one, plus an Lmax dose-response.
- **Onset dynamics** — EE lowered 4→3 (attack time has never been manipulated parametrically with an autonomic outcome) and AI raised 2→3 in the same audit. The AI raise is load-bearing: at AI=2 the boundary rule would place this in Tier 2, where it would be the best-evidenced directional parameter. No other assignment depends on it.
- **Roughness** — EE lowered 4→2: consistent across four paradigms, but none measures an autonomic outcome with roughness as the operative variable. The Tier-1 placement is carried by Mechanistic Confirmation and Appraisal Independence, not by autonomic effect data. Under a stricter scheme requiring EE≥3 for Tier 1, this parameter — and only this one — moves to Tier 2.
- **Predictability** — Two paradigms, one measuring autonomic outcomes with prediction error as the operative variable.

## Tier 2 — directional, optimum set per listener

The direction is established but the optimum is individual, so these are reported in-range vs out-of-range against the exemplar values rather than passed or failed.

| Parameter | EE | MC | AI | D | Composite | Axis | Evidence class | Design implication |
|---|---:|---:|---:|---:|---:|---:|---|---|
| **Tempo / rhythm** ‡ | 4 | 2 | 2 | 2 | 10 | 8 | Direct | Interior optimum — a BPM value must be selected per listener. |
| **Sharpness** | 2 | 2 | 2 | 1 | 7 | 6 | Indirect | Monotone in direction, but the acceptable limit is context-dependent. |
| **Pitch** | 2 | 2 | 1 | 1 | 6 | 5 | Indirect | Interior optimum — a register, varying with musical context. |
| **Spectral slope β** | 2 | 1 | 2 | 1 | 6 | 5 | Indirect | Interior optimum — a β value chosen to listener tolerance. |
| **Complexity** | 2 | 1 | 1 | 1 | 5 | 4 | Indirect | Interior optimum — inverted-U, shifting with listening expertise. |

- **Tempo / rhythm** ‡ — The best-evidenced parameter in the framework on directly measured autonomic outcomes (five studies, including an explicit dose-response), and the only parameter the Tier-1 boundary rule touches: AI=2, because the optimum must be matched to individual resting heart rate.
- **Sharpness** — EE lowered 3→2: the urgency literature manipulated fundamental frequency rather than sharpness, and the one autonomic study cannot isolate the parameter.
- **Pitch** — EE lowered 3→2: every reviewed study used subjective arousal ratings as the dependent variable; no autonomic measurement under parametric pitch manipulation has been reported.
- **Spectral slope β** — Evidence class corrected direct→indirect: the studies with autonomic outcomes manipulate the presence of broadband masking rather than slope itself, and findings conflict across outcome measures.
- **Complexity** — Consistent direction across two rating-based paradigms; no parametric study with an autonomic outcome.

## Tier 3 — exploratory adjuncts

Reported without a design target. Not primary design targets at the current level of evidence.

| Parameter | EE | MC | AI | D | Composite | Axis | Evidence class | Design implication |
|---|---:|---:|---:|---:|---:|---:|---|---|
| **Semantic content (lyrics)** | 1 | 1 | 1 | 1 | 4 | 3 | Theoretical | Binary by convention; the effect depends on the listener's language. |
| **Harmonicity / HNR** | 1 | 1 | 0 | 1 | 3 | 2 | Indirect | Direction of preference reverses with musical enculturation. |
| **Familiarity** | 1 | 1 | 0 | 0 | 2 | 2 | Indirect | Direction depends entirely on individual listening history. |

- **Semantic content (lyrics)** — EE lowered 2→1 — the only audit change that moved a tier (2→3). No study manipulates lyric presence with an autonomic outcome; the basis is design convention plus corpus description. Under equal weighting of all four dimensions this parameter returns to the Tier-2 band, the one borderline case in the review's sensitivity analysis.
- **Harmonicity / HNR** — Pleasantness differences are well established, but arousal-specific effects are not isolated and the direction is enculturation-dependent.
- **Familiarity** — Findings conflict on whether the effect is attributable to familiarity or to preference.

<!-- END GENERATED: evidence-table -->

## Screening values used by DEBUSSY

These are the defaults of DEBUSSY's own rubric, seeded from the reference
values above. They are exposed as module constants so a protocol needing
different limits can state its own:

| Constant | Default | Provenance |
|---|---|---|
| `ROUGHNESS_REFERENCE_ASPER` | 0.3 asper | Reference value in the cited roughness literature |
| `ROUGHNESS_COVERAGE_CAUTION_PCT` | 2 % | DEBUSSY's own — the review reports no coverage figure |
| `ROUGHNESS_COVERAGE_FAIL_PCT` | 10 % | DEBUSSY's own |
| `ATTACK_REFERENCE_MS` | 50 ms | Exemplar onset duration from the alarm-design literature |
| `SHARP_ONSET_SHARE_PCT` / `SHARP_ONSET_MIN_COUNT` | 25 % / 5 | DEBUSSY's own |
| `TEMPO_EXEMPLAR_BPM` | 60–80 BPM | Exemplar range; adapt to resting heart rate |
| `SHARPNESS_EXEMPLAR_ACUM` | 1.5 acum | Quoted as provisional in the review |
| `SPECTRAL_SLOPE_PREFERRED_BETA` | −2 to −1 | DEBUSSY's own pink-to-brown band |

Only Tier 1 can produce a failing status. Tiers 2 and 3 are reported.

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

The 0.3 asper figure follows the amygdala-activation roughness literature, in
which the selectivity is for the 30–150 Hz amplitude-modulation band; the
whole-file aggregate is a proxy for it. The 2 % / 10 % coverage bands are
DEBUSSY's own screening heuristics and appear nowhere in the review.

### Attack status logic

The verdict is the median-onset rule (> 50 ms). A high share of sub-50 ms onsets
can downgrade a PASS to CAUTION, but only when the pattern is both substantial
(> 25 % of onsets) and non-incidental (n ≥ 5). It never fails on its own:
envelope rise time ignores absolute level, so it describes onset shape rather
than measuring startle.

## Sensitivity

The review reports that the tier assignments are robust across four weighting
schemes, with two cases worth knowing about because they bear on how much to
trust a DEBUSSY verdict:

- **Roughness** sits in Tier 1 on a composite of 10 while its Effect Evidence is
  2. The composite is *compensatory*: a high Mechanistic Confirmation and
  Appraisal Independence can carry a parameter to the top tier without direct
  autonomic effect data. Under a stricter scheme requiring EE ≥ 3 for Tier 1,
  roughness — and only roughness — moves to Tier 2.
- **Semantic content** returns to the Tier-2 band under equal weighting of all
  four dimensions. It is the framework's one borderline case.

## Programmatic access

```python
from debussy import tier1_items, tier2_items, tier3_items, format_compliance

for item in tier1_items(result):
    print(item["parameter"], item["status"], item["note"])

print(format_compliance(result))   # printable summary
```

Each item carries `parameter`, `value`, `unit`, `target`, `status` and `note`.
Tier-1 statuses are `PASS`, `CAUTION`, `FAIL`, `INFO`, `MANUAL` or `N/A`.

The scores themselves are available as data, so you can apply your own
weighting rather than accepting the published tiers:

```python
from debussy import PARAMETERS, parameters_in_tier

for p in PARAMETERS:
    print(p.label, p.composite, p.evidence_class, p.tier)

# Apply the stricter scheme: require direct-ish effect evidence for Tier 1
strict = [p for p in parameters_in_tier(1) if p.effect_evidence >= 3]
```
