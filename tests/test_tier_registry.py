"""The evidence table is the single source of truth — these tests keep it that way.

Three kinds of drift are possible once tier data lives in one place and is used
in three: the scores can stop adding up, the graders in ``_core`` can render a
parameter under a tier it no longer belongs to, and the documentation can fall
behind the code. One test each.
"""

import pathlib
import subprocess
import sys

import pytest

from debussy import PARAMETERS, parameter, parameters_in_tier
from debussy import _tiers
from debussy._core import tier1_items, tier2_items, tier3_items

REPO = pathlib.Path(__file__).resolve().parents[1]

# Maximum per dimension, from the review's scoring rubric.
_LIMITS = {
    "effect_evidence": 4,
    "mechanistic": 3,
    "appraisal_independence": 3,
    "designability": 2,
}


@pytest.mark.parametrize("p", PARAMETERS, ids=lambda p: p.key)
def test_scores_are_within_their_dimension_range(p):
    for field, top in _LIMITS.items():
        v = getattr(p, field)
        assert 0 <= v <= top, f"{p.key}.{field} = {v}, outside 0–{top}"


@pytest.mark.parametrize("p", PARAMETERS, ids=lambda p: p.key)
def test_composite_is_the_sum_of_the_four_dimensions(p):
    assert p.composite == sum(getattr(p, f) for f in _LIMITS)
    assert p.evidence_axis == p.composite - p.designability


@pytest.mark.parametrize("p", PARAMETERS, ids=lambda p: p.key)
def test_derived_tier_matches_the_published_tier(p):
    """The tier is computed from the scores; this pins it to the printed table.

    A mistyped score changes the derived tier and fails here rather than
    silently shipping a parameter under the wrong heading.
    """
    assert p.tier == p.published_tier, (
        f"{p.key}: composite {p.composite} with AI {p.appraisal_independence} "
        f"derives Tier {p.tier}, but the review prints Tier {p.published_tier}"
    )


@pytest.mark.parametrize("p", PARAMETERS, ids=lambda p: p.key)
def test_evidence_class_is_one_of_the_three_labels(p):
    assert p.evidence_class in ("direct", "indirect", "theoretical")


def test_every_tier1_parameter_clears_the_appraisal_independence_floor():
    """Tier 1 means one fixed value serves every listener."""
    for p in parameters_in_tier(1):
        assert p.appraisal_independence >= _tiers._TIER1_MIN_AI, (
            f"{p.key} is Tier 1 with AI {p.appraisal_independence}"
        )


def test_the_boundary_rule_touches_only_tempo():
    """Tempo is the framework's only held parameter — worth pinning explicitly."""
    assert [p.key for p in _tiers.held_parameters()] == ["tempo"]


def test_the_twelve_parameters_are_all_present_and_distinct():
    assert len(PARAMETERS) == 12
    assert len({p.key for p in PARAMETERS}) == 12


def test_roughness_is_tier1_on_indirect_evidence():
    """Guards the review's most contestable placement against a quiet 'fix'.

    Roughness reaches Tier 1 on mechanism and appraisal independence, not on
    autonomic effect data. If someone raises its Effect Evidence back to the
    pre-audit 4, this fails — the number should only move when the literature
    does.
    """
    r = parameter("roughness")
    assert r.tier == 1
    assert r.evidence_class == "indirect"
    assert r.effect_evidence == 2
    # ...and under the stricter EE>=3 scheme it is the only one that moves.
    demoted = [p.key for p in parameters_in_tier(1) if p.effect_evidence < 3]
    assert demoted == ["roughness"]


# ---------------------------------------------------------------------------
# The graders must render each parameter under the tier the table assigns it.
# ---------------------------------------------------------------------------

def test_graders_agree_with_the_table(sine_440):
    """`_check_tier` fires inside each grader; this exercises all three."""
    from debussy import analyze_audio
    r = analyze_audio(sine_440)
    for fn in (tier1_items, tier2_items, tier3_items):
        assert fn(r), f"{fn.__name__} returned nothing"


def test_semantic_content_is_reported_in_tier3_not_tier2(sine_440):
    """The audit moved lyrics from Tier 2 to Tier 3; the output must follow."""
    from debussy import analyze_audio
    r = analyze_audio(sine_440, lyrics_presence="no")

    assert parameter("semantic_content").tier == 3
    assert not [it for it in tier2_items(r) if "lyric" in it["parameter"].lower()]

    lyrics = [it for it in tier3_items(r) if "lyric" in it["parameter"].lower()]
    assert len(lyrics) == 1
    assert lyrics[0]["value"] == "no"
    # Tier-3 items carry an interpretation rather than a pass/fail status.
    assert "interpretation" in lyrics[0]
    assert "status" not in lyrics[0]


def test_grader_rejects_a_tier_it_no_longer_owns(monkeypatch):
    """The drift guard must actually fire, not just sit there."""
    original = _tiers.parameter

    def moved(key):
        p = original(key)
        if key == "roughness":
            return type(p)(**{**p.__dict__, "mechanistic": 0, "published_tier": 2})
        return p

    monkeypatch.setattr(_tiers, "parameter", moved)
    with pytest.raises(RuntimeError, match="tier1_items"):
        tier1_items(None)


# ---------------------------------------------------------------------------
# Documentation is generated, so it cannot drift.
# ---------------------------------------------------------------------------

def test_reference_ranges_doc_is_up_to_date():
    proc = subprocess.run(
        [sys.executable, str(REPO / "tools" / "gen_reference_ranges.py"), "--check"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        "docs/reference_ranges.md is stale — run "
        "`python tools/gen_reference_ranges.py`\n" + proc.stderr
    )
