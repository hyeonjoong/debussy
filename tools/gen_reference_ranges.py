#!/usr/bin/env python3
"""Render the evidence table in ``docs/reference_ranges.md`` from ``debussy._tiers``.

The generated block sits between the BEGIN/END markers; everything outside them
is hand-written and is left untouched. ``tests/test_tier_registry.py`` runs this
in check mode, so documentation cannot drift from the scores in code.

    python tools/gen_reference_ranges.py           # rewrite the file
    python tools/gen_reference_ranges.py --check   # exit 1 if out of date
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from debussy import _tiers  # noqa: E402

DOC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "reference_ranges.md"
BEGIN = "<!-- BEGIN GENERATED: evidence-table (tools/gen_reference_ranges.py) -->"
END = "<!-- END GENERATED: evidence-table -->"

_CLASS_LABEL = {
    "direct": "Direct",
    "indirect": "Indirect",
    "theoretical": "Theoretical",
}

_TIER_HEADING = {
    1: ("Tier 1 — fixed design constraints",
        "One value serves every listener. These are the only parameters DEBUSSY "
        "grades pass/fail."),
    2: ("Tier 2 — directional, optimum set per listener",
        "The direction is established but the optimum is individual, so these are "
        "reported in-range vs out-of-range against the exemplar values rather than "
        "passed or failed."),
    3: ("Tier 3 — exploratory adjuncts",
        "Reported without a design target. Not primary design targets at the "
        "current level of evidence."),
}


def render() -> str:
    out: list[str] = [BEGIN, ""]
    out.append(
        "*This section is generated from `src/debussy/_tiers.py`. Edit the scores "
        "there, then run `python tools/gen_reference_ranges.py`.*"
    )
    out.append("")
    out.append(
        "Scores are the audited values from the companion review's score-audit "
        "table. **EE** Effect Evidence (0–4), **MC** Mechanistic Confirmation "
        "(0–3), **AI** Appraisal Independence (0–3), **D** Designability (0–2); "
        "composite = their sum, in 0–12. The **evidence axis** (EE+MC+AI) drops "
        "Designability, which measures tractability rather than evidence."
    )
    out.append("")
    out.append("| Composite | Tier | Meaning |")
    out.append("|---|---|---|")
    for low, high, tier in _tiers.TIER_BANDS:
        out.append(f"| {low}–{high} | **Tier {tier}** | {_TIER_HEADING[tier][0].split('—')[1].strip()} |")
    out.append("")
    out.append(
        "**Boundary rule.** A parameter scoring in the Tier-1 band is held in "
        "Tier 2 if and only if **AI < 3**. Tier 1 means one fixed value serves "
        "every listener, so a parameter whose optimum must be chosen per listener "
        "cannot sit there however strong its evidence."
    )
    held = _tiers.held_parameters()
    if held:
        names = ", ".join(f"**{p.label}**" for p in held)
        out.append("")
        out.append(
            f"The rule currently touches {names} — "
            + ("; ".join(f"composite {p.composite}, AI {p.appraisal_independence}"
                         for p in held))
            + "."
        )
    out.append("")

    for tier in (1, 2, 3):
        params = _tiers.parameters_in_tier(tier)
        if not params:
            continue
        heading, blurb = _TIER_HEADING[tier]
        out.append(f"## {heading}")
        out.append("")
        out.append(blurb)
        out.append("")
        out.append("| Parameter | EE | MC | AI | D | Composite | Axis | Evidence class | Design implication |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
        for p in params:
            label = f"**{p.label}**" + (" ‡" if p.held_in_tier2 else "")
            out.append(
                f"| {label} | {p.effect_evidence} | {p.mechanistic} | "
                f"{p.appraisal_independence} | {p.designability} | {p.composite} | "
                f"{p.evidence_axis} | {_CLASS_LABEL[p.evidence_class]} | "
                f"{p.design_implication} |"
            )
        out.append("")
        for p in params:
            if p.note:
                marker = " ‡" if p.held_in_tier2 else ""
                out.append(f"- **{p.label}**{marker} — {p.note}")
        out.append("")

    out.append(END)
    return "\n".join(out)


def splice(existing: str, block: str) -> str:
    if BEGIN not in existing or END not in existing:
        raise SystemExit(
            f"{DOC} is missing the generated-block markers; add them back before "
            "running this script."
        )
    head = existing.split(BEGIN)[0]
    tail = existing.split(END)[1]
    return head + block + tail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the file is out of date instead of rewriting it")
    args = ap.parse_args()

    existing = DOC.read_text(encoding="utf-8")
    updated = splice(existing, render())

    if args.check:
        if existing != updated:
            print(f"{DOC} is out of date — run: python tools/gen_reference_ranges.py",
                  file=sys.stderr)
            return 1
        return 0

    if existing != updated:
        DOC.write_text(updated, encoding="utf-8")
        print(f"rewrote {DOC}")
    else:
        print(f"{DOC} already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
