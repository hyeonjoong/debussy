"""The hand-rolled statistics in ``validation/`` are checked against references.

``sensitivity_power.py`` is the evidence that the A-vs-B contrast is real, and
``analyze_results.py`` produces the published summary table, but both implement
Benjamini-Hochberg, Cliff's delta and the sign-agreement count by hand in a few
lines each. A sign flip or an off-by-one there changes a published number
without changing anything a reader can see, so each is pinned here against an
independent reference: SciPy for BH, hand-computed cases for Cliff's delta, and
the released matrices end-to-end for the reported counts.

Neither script is importable as a module — they are run as ``python
validation/<name>.py`` — so they are loaded from their paths.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

VALIDATION = Path(__file__).resolve().parents[1] / "validation"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, VALIDATION / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sensitivity_power = _load("sensitivity_power")
analyze_results = _load("analyze_results")

# Both scripts define their own copy of each statistic. Every property below is
# asserted of both, so the copies cannot drift apart unnoticed.
BOTH = pytest.mark.parametrize(
    "mod", [sensitivity_power, analyze_results], ids=["sensitivity_power", "analyze_results"]
)


def _bh_by_definition(p):
    """BH adjusted p-values straight from the definition, written for clarity.

    q_(i) = min over j >= i of  n * p_(j) / j , capped at 1. Quadratic and
    without the reversed-cumulative-minimum trick the scripts use, so a mistake
    in that trick cannot be reproduced here.
    """
    p = np.asarray(p, dtype=float)
    n = p.size
    order = np.argsort(p, kind="stable")
    out = np.empty(n)
    for rank, idx in enumerate(order, start=1):
        out[idx] = min(1.0, min(n * p[order[j - 1]] / j for j in range(rank, n + 1)))
    return out


# Deliberately includes a run of ties (0.04, 0.04 and 0.2, 0.2, 0.2), a p of
# exactly 1.0, and a p small enough that the cap at 1.0 has to bite for the
# larger ranks.
P_WITH_TIES = np.array([0.001, 0.04, 0.04, 0.2, 0.2, 0.2, 0.5, 0.9, 1.0])
P_WITH_NAN = np.array([0.001, np.nan, 0.04, 0.2, np.nan, 0.9])


@BOTH
def test_benjamini_hochberg_matches_scipy(mod):
    """Ties and all: the same q-vector SciPy's implementation returns."""
    expected = stats.false_discovery_control(P_WITH_TIES, method="bh")
    np.testing.assert_allclose(mod.benjamini_hochberg(P_WITH_TIES), expected)


@BOTH
def test_benjamini_hochberg_matches_the_definition(mod):
    np.testing.assert_allclose(
        mod.benjamini_hochberg(P_WITH_TIES), _bh_by_definition(P_WITH_TIES)
    )


@BOTH
def test_benjamini_hochberg_excludes_nan_from_the_correction(mod):
    """A parameter with too few values must not inflate *n* for the rest.

    ``contrast()`` emits NaN for a parameter it could not test. Those positions
    stay NaN, and the surviving p-values are corrected across their own count,
    not across twelve.
    """
    got = mod.benjamini_hochberg(P_WITH_NAN)
    ok = ~np.isnan(P_WITH_NAN)
    assert np.isnan(got[~ok]).all()
    expected = stats.false_discovery_control(P_WITH_NAN[ok], method="bh")
    np.testing.assert_allclose(got[ok], expected)


@BOTH
def test_benjamini_hochberg_is_monotone_and_never_below_p(mod):
    rng = np.random.default_rng(20260909)
    p = rng.random(40)
    q = mod.benjamini_hochberg(p)
    assert (q >= p - 1e-12).all(), "an adjusted p-value cannot be smaller than its raw p"
    assert (q <= 1.0).all()
    order = np.argsort(p)
    assert (np.diff(q[order]) >= -1e-12).all(), "q must be monotone in p"


@BOTH
def test_benjamini_hochberg_all_nan(mod):
    assert np.isnan(mod.benjamini_hochberg(np.array([np.nan, np.nan]))).all()


@BOTH
def test_cliffs_delta_identical_groups_is_zero(mod):
    assert mod.cliffs_delta([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0


@BOTH
def test_cliffs_delta_full_separation_is_plus_or_minus_one(mod):
    assert mod.cliffs_delta([5.0, 6.0, 7.0], [1.0, 2.0]) == 1.0
    assert mod.cliffs_delta([1.0, 2.0], [5.0, 6.0, 7.0]) == -1.0


@BOTH
def test_cliffs_delta_hand_computed(mod):
    """a=[1,3], b=[2,4]: of the four pairs one is greater and three are less."""
    assert mod.cliffs_delta([1.0, 3.0], [2.0, 4.0]) == pytest.approx((1 - 3) / 4)


@BOTH
def test_cliffs_delta_ties_count_towards_neither_side(mod):
    """a=[1,2], b=[2,3]: the 2-vs-2 pair is a tie, so delta is (0-3)/4."""
    assert mod.cliffs_delta([1.0, 2.0], [2.0, 3.0]) == pytest.approx(-0.75)


@BOTH
def test_cliffs_delta_drops_nan_rather_than_diluting(mod):
    """A NaN must leave the denominator, not sit in it comparing False both ways.

    Keeping it would count the pair in ``a.size * b.size`` while adding to
    neither the greater nor the less count, pulling every delta towards zero in
    proportion to how much data is missing.
    """
    assert mod.cliffs_delta([1.0, 2.0, np.nan, 4.0], [0.0, 0.5]) == 1.0
    assert np.isnan(mod.cliffs_delta([np.nan, np.nan], [1.0, 2.0]))


@BOTH
def test_cliffs_delta_empty_group_is_nan(mod):
    assert np.isnan(mod.cliffs_delta([], [1.0, 2.0]))


def _synthetic_arm():
    """Twelve parameters with known signs, plus one that cannot be tested.

    Groups are perfectly separated, so every testable delta is exactly +1 or -1
    and the sign-agreement count is fully determined. The last parameter is
    all-NaN in group A, which is what ``contrast()`` refuses to test.
    """
    n = 6
    # Eleven signs for twelve parameters: nine agree with an all-positive
    # primary, two do not, and the twelfth is left to the untestable column.
    signs = [+1] * 9 + [-1] * 2
    frame = {"group": ["A"] * n + ["B"] * n}
    for (key, _), sign in zip(sensitivity_power.PARAMS, signs):
        frame[key] = list(np.arange(n) + 10.0 * sign) + list(np.arange(n, dtype=float))
    untestable = sensitivity_power.PARAMS[11][0]
    frame[untestable] = [np.nan] * n + list(np.arange(n, dtype=float))
    return pd.DataFrame(frame)


def test_contrast_skips_a_parameter_it_cannot_test():
    deltas, pvals, qvals = sensitivity_power.contrast(_synthetic_arm())
    assert np.isnan(deltas[11]) and np.isnan(pvals[11]) and np.isnan(qvals[11])
    np.testing.assert_allclose(deltas[:9], 1.0)
    np.testing.assert_allclose(deltas[9:11], -1.0)


def test_report_arm_counts_survivors_and_sign_agreement(capsys):
    """The two summary counts are the script's headline numbers; pin them.

    Eleven of the twelve parameters are testable and all eleven separate
    perfectly, so all eleven survive correction. Against an all-positive
    primary, the nine positive ones agree and the two negative ones do not.
    """
    primary = np.ones(12)
    sensitivity_power.report_arm("synthetic", _synthetic_arm(), primary_deltas=primary)
    out = capsys.readouterr().out
    assert "11/12 survive Benjamini-Hochberg at 0.05" in out
    assert "9/12 agree on sign with the primary arm" in out
    assert out.count("   NO") == 2


def test_report_arm_omits_agreement_when_there_is_no_primary(capsys):
    sensitivity_power.report_arm("synthetic", _synthetic_arm())
    out = capsys.readouterr().out
    assert "11/12 survive Benjamini-Hochberg at 0.05" in out
    assert "agree on sign" not in out


def test_sensitivity_power_reproduces_the_reported_counts(capsys):
    """End-to-end on the released matrices: the numbers the paper cites.

    A regression in either the statistics or the shipped CSVs moves one of
    these counts, which is the failure this is here to catch.
    """
    assert sensitivity_power.main([]) == 0
    out = capsys.readouterr().out
    primary = out.split("Wide-band DEAM draw")[0]
    assert "300 tracks — group A n=150, group B n=150" in primary
    # The primary arm holds the published bands fixed and only raises n, so this
    # is the count that answers "was the benchmark simply underpowered".
    assert "11/12 survive Benjamini-Hochberg at 0.05" in primary
    assert "10/12 survive Benjamini-Hochberg at 0.05; 11/12 agree on sign" in out
    assert "4/12 survive Benjamini-Hochberg at 0.05; 9/12 agree on sign" in out


def test_analyze_results_reproduces_the_published_null(tmp_path):
    """The 60-track benchmark's headline: no A-vs-B contrast survives BH."""
    assert analyze_results.main(["--no-figure", "--out-dir", str(tmp_path)]) == 0
    summary = pd.read_csv(tmp_path / "summary_statistics.csv")
    assert len(summary) == 12
    assert (summary["A_n"] == 10).all() and (summary["B_n"] == 30).all()
    # Two of the twenty clinical tracks return no HNR, which is the one place
    # the published matrix is not complete; every other group size is full.
    hnr = summary["parameter"] == "HNR (dB)"
    assert summary.loc[hnr, "C_n"].item() == 18
    assert (summary.loc[~hnr, "C_n"] == 20).all()
    assert (summary["BH_q_A_vs_B"] >= 0.05).all(), "the published null must hold"
    assert summary["BH_q_A_vs_B"].min() == pytest.approx(0.1892, abs=5e-4)
