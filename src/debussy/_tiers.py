"""Parameter evidence scores and tier assignments from the companion review.

This module is the **single source of truth** for the three-tier framework.
Nothing else in DEBUSSY — not the graders in ``_core``, not the documentation —
may hard-code a score or a tier number. ``docs/reference_ranges.md`` is
generated from this table by ``tools/gen_reference_ranges.py`` and a test keeps
the two in sync.

The scores are the **audited** values from the companion review's score-audit
table (submitted as a supplementary data file), not the values in the original
submission. Four dimensions are scored per parameter:

===  ==========================  =====  =============================================
Key  Dimension                   Range  Question it answers
===  ==========================  =====  =============================================
EE   Effect Evidence             0–4    How directly has an autonomic outcome been
                                        measured with this parameter as the
                                        operative variable?
MC   Mechanistic Confirmation    0–3    Is there an identified physiological pathway?
AI   Appraisal Independence      0–3    Does the effect survive individual
                                        differences in training, culture, preference?
D    Designability               0–2    Can it be computed and controlled a priori?
===  ==========================  =====  =============================================

Composite = EE + MC + AI + D, in 0–12. Tier follows from the composite band,
with one boundary rule (see :func:`_assign_tier`). Because the tier is
*derived*, editing a score here is sufficient to move a parameter — and
:mod:`tests.test_tier_registry` asserts the derived tiers still match the
published ones, so a mis-typed score cannot pass silently.

**Evidence class** (``direct`` / ``indirect`` / ``theoretical``) is reported
*alongside* the composite score and is deliberately not folded into it: a high
composite carried by mechanism rather than by measured autonomic outcomes is a
weaker claim than the number alone suggests, and the reader is entitled to see
which is which. Roughness is the standing example — Tier 1 on a composite of
10, but ``evidence_class="indirect"`` because no study has manipulated
roughness parametrically while measuring an autonomic outcome.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ParameterEvidence",
    "PARAMETERS",
    "TIER_BANDS",
    "parameter",
    "parameters_in_tier",
    "held_parameters",
]

#: Composite-score bands. ``(low, high, tier)``, inclusive.
TIER_BANDS = ((9, 12, 1), (5, 8, 2), (0, 4, 3))

#: Appraisal Independence required for a Tier-1 placement. The boundary rule
#: below is the review's only mechanical override, added in revision so that
#: the hierarchy is reproducible from the scores rather than from prose.
_TIER1_MIN_AI = 3


def _band_tier(composite: int) -> int:
    for low, high, tier in TIER_BANDS:
        if low <= composite <= high:
            return tier
    raise ValueError(f"composite {composite} outside 0–12")


def _assign_tier(composite: int, appraisal_independence: int) -> int:
    """Tier from the composite band, with the review's boundary rule applied.

    A parameter scoring in the Tier-1 band is **held in Tier 2 if and only if
    ``AI < 3``**. The rationale is definitional rather than empirical: Tier 1
    means one fixed value serves every listener, so a parameter whose optimum
    has to be selected per listener cannot sit there however strong its
    evidence. Tempo is the only parameter the rule currently touches — a
    composite of 10 on directly measured autonomic outcomes, held in Tier 2
    because a BPM value must be chosen against the individual's resting heart
    rate.
    """
    tier = _band_tier(composite)
    if tier == 1 and appraisal_independence < _TIER1_MIN_AI:
        return 2
    return tier


@dataclass(frozen=True)
class ParameterEvidence:
    """One row of the companion review's parameter-evaluation table."""

    key: str
    label: str
    effect_evidence: int          # EE, 0–4
    mechanistic: int              # MC, 0–3
    appraisal_independence: int   # AI, 0–3
    designability: int            # D, 0–2
    evidence_class: str           # "direct" | "indirect" | "theoretical"
    design_implication: str       # how the AI score cashes out for a designer
    published_tier: int           # tier as printed in the review, for the drift test
    note: str = ""                # audit note, abridged from the score-audit table

    @property
    def composite(self) -> int:
        """EE + MC + AI + D, in 0–12."""
        return (self.effect_evidence + self.mechanistic
                + self.appraisal_independence + self.designability)

    @property
    def evidence_axis(self) -> int:
        """EE + MC + AI, in 0–10 — the composite with Designability removed.

        Reported because Designability measures how tractable a parameter is to
        *manipulate*, not how well evidenced it is, and a measurability
        asymmetry would otherwise inflate the parameters that are easiest to
        compute. Tier placement is verified against this axis as well.
        """
        return (self.effect_evidence + self.mechanistic
                + self.appraisal_independence)

    @property
    def tier(self) -> int:
        """Tier derived from the scores. Edit a score, and this follows."""
        return _assign_tier(self.composite, self.appraisal_independence)

    @property
    def held_in_tier2(self) -> bool:
        """True when the boundary rule demoted this out of the Tier-1 band."""
        return _band_tier(self.composite) == 1 and self.tier == 2


# ---------------------------------------------------------------------------
# The table. Ordered by tier, then by composite descending — the order the
# review prints them in, and the order the generated documentation follows.
#
# Scores are the audited column of the score-audit table. Do not "correct" a
# score here to match an older figure or an older draft of the review; the
# audit lowered five Effect Evidence scores and raised one Appraisal
# Independence score against the original submission, and this table is the
# post-audit state.
# ---------------------------------------------------------------------------

PARAMETERS: tuple[ParameterEvidence, ...] = (
    ParameterEvidence(
        key="event_structure",
        label="Event structure",
        effect_evidence=4, mechanistic=2, appraisal_independence=3, designability=2,
        evidence_class="direct",
        design_implication="Monotone — minimise transient Lmax and event rate.",
        published_tier=1,
        note="Three independent paradigms (polysomnography, simultaneous autonomic "
             "recording, epidemiology) with direct autonomic outcomes in more than "
             "one, plus an Lmax dose-response.",
    ),
    ParameterEvidence(
        key="onset_dynamics",
        label="Onset dynamics",
        effect_evidence=3, mechanistic=3, appraisal_independence=3, designability=2,
        evidence_class="direct",
        design_implication="Monotone — slower attack; no listener-specific value needed.",
        published_tier=1,
        note="EE lowered 4→3 (attack time has never been manipulated parametrically "
             "with an autonomic outcome) and AI raised 2→3 in the same audit. The AI "
             "raise is load-bearing: at AI=2 the boundary rule would place this in "
             "Tier 2, where it would be the best-evidenced directional parameter. No "
             "other assignment depends on it.",
    ),
    ParameterEvidence(
        key="roughness",
        label="Roughness",
        effect_evidence=2, mechanistic=3, appraisal_independence=3, designability=2,
        evidence_class="indirect",
        design_implication="Monotone — minimise.",
        published_tier=1,
        note="EE lowered 4→2: consistent across four paradigms, but none measures an "
             "autonomic outcome with roughness as the operative variable. The Tier-1 "
             "placement is carried by Mechanistic Confirmation and Appraisal "
             "Independence, not by autonomic effect data. Under a stricter scheme "
             "requiring EE≥3 for Tier 1, this parameter — and only this one — moves "
             "to Tier 2.",
    ),
    ParameterEvidence(
        key="predictability",
        label="Predictability",
        effect_evidence=3, mechanistic=2, appraisal_independence=3, designability=1,
        evidence_class="direct",
        design_implication="Monotone — maximise structural regularity.",
        published_tier=1,
        note="Two paradigms, one measuring autonomic outcomes with prediction error "
             "as the operative variable.",
    ),
    ParameterEvidence(
        key="tempo",
        label="Tempo / rhythm",
        effect_evidence=4, mechanistic=2, appraisal_independence=2, designability=2,
        evidence_class="direct",
        design_implication="Interior optimum — a BPM value must be selected per listener.",
        published_tier=2,
        note="The best-evidenced parameter in the framework on directly measured "
             "autonomic outcomes (five studies, including an explicit dose-response), "
             "and the only parameter the Tier-1 boundary rule touches: AI=2, because "
             "the optimum must be matched to individual resting heart rate.",
    ),
    ParameterEvidence(
        key="sharpness",
        label="Sharpness",
        effect_evidence=2, mechanistic=2, appraisal_independence=2, designability=1,
        evidence_class="indirect",
        design_implication="Monotone in direction, but the acceptable limit is context-dependent.",
        published_tier=2,
        note="EE lowered 3→2: the urgency literature manipulated fundamental "
             "frequency rather than sharpness, and the one autonomic study cannot "
             "isolate the parameter.",
    ),
    ParameterEvidence(
        key="pitch",
        label="Pitch",
        effect_evidence=2, mechanistic=2, appraisal_independence=1, designability=1,
        evidence_class="indirect",
        design_implication="Interior optimum — a register, varying with musical context.",
        published_tier=2,
        note="EE lowered 3→2: every reviewed study used subjective arousal ratings as "
             "the dependent variable; no autonomic measurement under parametric pitch "
             "manipulation has been reported.",
    ),
    ParameterEvidence(
        key="spectral_slope",
        label="Spectral slope β",
        effect_evidence=2, mechanistic=1, appraisal_independence=2, designability=1,
        evidence_class="indirect",
        design_implication="Interior optimum — a β value chosen to listener tolerance.",
        published_tier=2,
        note="Evidence class corrected direct→indirect: the studies with autonomic "
             "outcomes manipulate the presence of broadband masking rather than slope "
             "itself, and findings conflict across outcome measures.",
    ),
    ParameterEvidence(
        key="complexity",
        label="Complexity",
        effect_evidence=2, mechanistic=1, appraisal_independence=1, designability=1,
        evidence_class="indirect",
        design_implication="Interior optimum — inverted-U, shifting with listening expertise.",
        published_tier=2,
        note="Consistent direction across two rating-based paradigms; no parametric "
             "study with an autonomic outcome.",
    ),
    ParameterEvidence(
        key="semantic_content",
        label="Semantic content (lyrics)",
        effect_evidence=1, mechanistic=1, appraisal_independence=1, designability=1,
        evidence_class="theoretical",
        design_implication="Binary by convention; the effect depends on the listener's language.",
        published_tier=3,
        note="EE lowered 2→1 — the only audit change that moved a tier (2→3). No "
             "study manipulates lyric presence with an autonomic outcome; the basis "
             "is design convention plus corpus description. Under equal weighting of "
             "all four dimensions this parameter returns to the Tier-2 band, the one "
             "borderline case in the review's sensitivity analysis.",
    ),
    ParameterEvidence(
        key="harmonicity",
        label="Harmonicity / HNR",
        effect_evidence=1, mechanistic=1, appraisal_independence=0, designability=1,
        evidence_class="indirect",
        design_implication="Direction of preference reverses with musical enculturation.",
        published_tier=3,
        note="Pleasantness differences are well established, but arousal-specific "
             "effects are not isolated and the direction is enculturation-dependent.",
    ),
    ParameterEvidence(
        key="familiarity",
        label="Familiarity",
        effect_evidence=1, mechanistic=1, appraisal_independence=0, designability=0,
        evidence_class="indirect",
        design_implication="Direction depends entirely on individual listening history.",
        published_tier=3,
        note="Findings conflict on whether the effect is attributable to familiarity "
             "or to preference.",
    ),
)

_BY_KEY = {p.key: p for p in PARAMETERS}


def parameter(key: str) -> ParameterEvidence:
    """Look up one parameter by key. Raises ``KeyError`` if absent."""
    return _BY_KEY[key]


def parameters_in_tier(tier: int) -> tuple[ParameterEvidence, ...]:
    """Every parameter assigned to ``tier``, in table order."""
    return tuple(p for p in PARAMETERS if p.tier == tier)


def held_parameters() -> tuple[ParameterEvidence, ...]:
    """Parameters scoring in the Tier-1 band but held in Tier 2 by the rule."""
    return tuple(p for p in PARAMETERS if p.held_in_tier2)
