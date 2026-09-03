# Changelog

All notable changes to DEBUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] — 2026-09-03

Companion-review alignment and the power-sensitivity release. Every
change below landed through a reviewed pull request (#3, #13, #14,
#22–#24, #26–#30).

### Added
- **The primary power-sensitivity arm** (`validation/data/parameters_sensitivity_narrow150.csv`).
  The published arousal bands are held exactly fixed and 150 tracks per group are
  drawn at random within each, so the only difference from the released
  benchmark is *n*. **Eleven of twelve** A-vs-B contrasts survive
  Benjamini-Hochberg, against zero of twelve in the benchmark drawn from the
  identical population. This is the arm that separates "underpowered" from
  "bands too narrow", and it settles it as the former: the published contrast
  was real and could not be seen at *n*=10. `sensitivity_power.py` now reports
  this arm first and marks the other two draws' sign agreement against it.
- **Power-sensitivity analysis for the A-vs-B contrast** (`validation/sensitivity_power.py`
  plus two 300-track matrices in `validation/data/`). The 60-track benchmark
  reports that nothing survives Benjamini-Hochberg correction, which on its own
  cannot distinguish "the parameters do not separate these categories" from
  "this design cannot see effects of that size". Simulated power at the observed
  effect sizes puts the published design at **11-30 %**, so the null was
  uninformative. A 150-per-group draw from the same DEAM pool, by a stated rule
  and the same 45 s standardisation, separates on **ten of twelve** with
  *q* < 0.001; an independent FMA draw (ambient/drone/minimal against the rest,
  compared only within FMA) agrees with it on ten of twelve signs.
- **Issue forms for bug reports and feature requests**
  (`.github/ISSUE_TEMPLATE/`). CONTRIBUTING already listed what a usable bug
  report contains — Python version, OS, `debussy.__version__`, a minimal
  reproducer, expected vs actual — but none of it was asked for at filing time,
  so a reporter had to find and read CONTRIBUTING first. The bug form prompts
  for those fields directly and asks reporters to *describe* problem audio
  rather than attach it; the feature form asks for the autonomic-arousal use
  case, which is the scope test CONTRIBUTING applies. Blank issues stay enabled.

### Changed
- **The paper, the docs and `validation/README.md` now say that the published
  A-vs-B effect sizes are unstable in sign** and must not be read as findings.
  Four of them — LAeq, spectral centroid, sharpness, spectral flatness — are
  positive at *n*=10 and strongly negative in both larger draws, which is the
  direction the acoustics predict. **The released 60-track benchmark data is
  unchanged**; this documents what it can and cannot support.
- **`attack_times_ms()` return keys renamed** `frac_below_50ms` →
  `frac_below_reference_ms` and `n_below_50ms` → `n_below_reference_ms`. The old
  names hard-coded a number the caller is invited to change. `Result` fields
  (`sharp_onset_pct`, `sharp_onset_count`) are unaffected.
- Code and API-doc prose describing these two numbers now calls them reference
  values rather than thresholds, matching the constants block that already
  said so. The `"threshold"` key returned by `coverage_items()` keeps its name;
  only its rendered value is now derived from the constants.
- **Tier data is now a single source of truth** (`debussy._tiers`). Every
  parameter's four evidence scores, evidence class and design implication live
  in one table, and the tier is *derived* from them by the review's banding plus
  its boundary rule — so moving a parameter is a one-line score edit rather than
  a hunt through graders and prose. `docs/reference_ranges.md` is generated from
  that table by `tools/gen_reference_ranges.py`; the graders in `_core` assert
  their membership against it; and tests fail if the derived tiers stop matching
  the published ones or if the documentation falls behind. The scores are
  exported (`PARAMETERS`, `parameters_in_tier`, `parameter`) so users can apply
  their own weighting instead of accepting the published assignment.
- **Scores updated to the companion review's score audit.** Five Effect Evidence
  scores were lowered (roughness 4→2, onset dynamics 4→3, sharpness 3→2, pitch
  3→2, semantic content 2→1) and one Appraisal Independence score raised (onset
  dynamics 2→3). Composites: roughness 12→10, sharpness 8→7, pitch 7→6, semantic
  content 5→4.
- **Semantic content (lyrics) moved from Tier 2 to Tier 3** — the one audit
  change that shifted a tier. It is now reported by `tier3_items()` with an
  `interpretation` rather than by `tier2_items()` with a `status`. It remains
  item 9 of the reporting guideline regardless of tier.
- **The Tier-1 boundary rule is now mechanical**: a parameter in the 9–12 band is
  held in Tier 2 if and only if its Appraisal Independence is below 3. Tempo is
  the only parameter it touches. This replaces the previous prose rationale,
  which could not be checked.
- **Numeric limits are reframed as reference values, not thresholds.** The review
  labels every figure it quotes an exemplar drawn from the cited studies and
  states that the evidence supports the *direction* of each principle, not its
  cut-point. DEBUSSY's grading is unchanged in behaviour, but the values are now
  named constants (`ROUGHNESS_REFERENCE_ASPER`, `ATTACK_REFERENCE_MS`,
  `TEMPO_EXEMPLAR_BPM`, …) documented as defaults of DEBUSSY's own screening
  rubric, overridable per protocol. A `FAIL` means "outside the range the cited
  literature reports", never "shown to raise autonomic arousal".
- Documentation now states that the eleven-item reporting guideline is
  independent of the tier hierarchy, so rejecting the tiers is no reason to
  reject the tool.
- **`CONTRIBUTING.md` now says where to seek support.** It covered how to
  contribute and how to report a bug, but a user with a usage question had
  nowhere obvious to go and would reasonably have filed a bug report by
  default. A "Getting help" section now points at the documentation first and
  then at the issue tracker under the `question` label, notes that Discussions
  is not enabled so the two share one tracker, and warns that reporters without
  triage rights cannot apply the label themselves.
- **The 60-track benchmark is now documented on the site, not only in the
  paper.** `docs/validation.md` gained the category composition, the 58/60
  completeness result and the A-vs-B and category-C statistics, which previously
  existed only in `paper/paper.md`; the page had said the numbers were
  "maintained in paper/paper.md" and described the benchmark by the wrong
  categories. Its reference-range paragraph also still called the values
  "directional guidance" and Tier 2 "soft", which the score audit had already
  replaced everywhere else.

### Fixed
- **The temporal-coverage metrics now read the reference-value constants
  instead of repeating them as literals.** `ROUGHNESS_REFERENCE_ASPER` and
  `ATTACK_REFERENCE_MS` are documented as named constants so a protocol needing
  different limits can state its own, but `roughness_coverage_pct` counted
  frames above a hard-coded `0.3`, `sharp_onset_pct`/`sharp_onset_count`
  counted onsets below a hard-coded `50.0`, and `coverage_items()` /
  `plot_coverage()` printed those numbers as literal strings. Re-pointing a
  constant therefore moved the Tier-1 mean check but not the coverage figure
  graded against `ROUGHNESS_COVERAGE_CAUTION_PCT` /
  `ROUGHNESS_COVERAGE_FAIL_PCT`, so a stimulus could be cautioned or failed
  against a limit nobody had set. Default output is unchanged — the constants
  hold the same values the literals did.
- `attack_times_ms()` omitted the sharp-onset count key entirely on the
  fewer-than-two-onsets path, where the other early return supplies it.
- **A clip exactly one 50 ms window long no longer crashes `analyze_audio()`.**
  `dynamic_range_db()` guarded only `len(y) < win`, but its frame loop stops
  before `i = len(y) - win`, so at exactly one window it built an empty array
  and `np.percentile` raised a bare `IndexError` — a clip one sample shorter or
  longer analysed fine. Such a clip holds a single short-term RMS value, so it
  now reports a 0 dB span, matching what the streaming long-file path already
  returned when it collected no full window. Longer inputs are unaffected, so
  the published benchmark values are unchanged.

## [0.2.2] — 2026-08-10

### Changed
- **Terminology aligned with the companion review.** The project described
  itself throughout as computing "twelve reporting parameters", which conflated
  two distinct things in the parent manuscript: its **Table 1** evaluates
  *twelve* acoustic parameters and scores them into three tiers, while its
  **Table 2** proposes an *eleven-item* minimum reporting guideline. DEBUSSY
  implements Table 2. README, the documentation site, package metadata, the
  CLI help text and the module docstrings now say so, and each artifact spells
  out that the two lists are different.
- **`docs/reference_ranges.md` rewritten against Table 1.** The previous version
  put spectral slope, tempo and modulation rate in Tier 3 and named only two
  Tier-2 parameters. Tiers, composite evidence scores and design strategies now
  match the review, including the two boundary cases (predictability enters
  Tier 1 at 9 points; tempo scores 10 but is held in Tier 2 because training and
  culture modulate the tempo–arousal relationship).
- **API reference pages written.** All six were placeholder stubs reading
  "Stub created …, will be expanded" — visible on the published site since the
  docs deployment landed. Each family page now documents its functions, units,
  fixed internal choices, when a value is legitimately `None`, and which
  reporting item it serves.

### Fixed
- Removed a leftover generated comment stamp from `docs/api/index.md`.

## [0.2.1] — 2026-08-10

First release published to PyPI.

### Fixed
- **Roughness and sharpness silently returned `None` on a clean install.**
  `mosqito` imports `matplotlib` inside `roughness_dw` and `sharpness_din_st`
  but does not declare it as a dependency, so an environment without matplotlib
  lost both psychoacoustic parameters — two of the eleven reporting items —
  with the failure recorded only in `Result.notes` and no error raised. It went
  unnoticed because development environments happened to have matplotlib
  installed. `matplotlib` is now a required dependency, and a regression test
  asserts both parameters compute on a strongly modulated tone (the existing
  psychoacoustic tests skip on `None`, so they could not catch this).
- **`py.typed` was declared in `[tool.setuptools.package-data]` but absent from
  the source tree**, so the marker never shipped and the annotated public API
  provided no type information to consumers. The file now exists and is verified
  present in both the wheel and the sdist.

### Added
- Publish-on-tag workflow using PyPI Trusted Publishing (OIDC), with a TestPyPI
  dry-run path and a guard that refuses to publish when the git tag and the
  packaged version disagree.

## [0.2.0] — 2026-08-10

### Added
- **`suppress_warnings=True`** on `analyze_audio()` / `analyse()` and
  `--suppress-warnings` on the CLI: silences the 48 kHz resample notice and the
  full-scale clipping warning for quiet batch runs.
- **`Result.to_dict()` and `Result.to_json()`** — lossless serialisation of every
  reporting field; `json.loads(r.to_json())` round-trips back to an equal `Result`.
- **Clipping detection**: a `UserWarning` and a `Result.notes` annotation when the
  input contains samples at digital full scale, whose level and spectral metrics
  are therefore suspect.
- **Documentation site** at <https://hyeonjoong.github.io/debussy>, built with
  mkdocs-material and deployed from CI; installation, CLI reference, per-family
  API pages, validation, reference ranges, tool comparison, FAQ, troubleshooting.
- **`validation/`** — the audio manifest, the raw per-track parameter matrix, the
  summary statistics, and the two scripts that regenerate them, so every number
  in the paper's validation section can be checked. `analyze_results.py` also
  computes the Benjamini–Hochberg q-values the paper reports.
- Runnable examples: `batch_report.py`, `csv_writer.py`, `json_export.py`.

### Fixed
- **`spectral_slope` crashed on clips shorter than ~1.4 s**: the FFT window was
  rounded *up* to the next power of two, which could exceed the signal length.
  It now rounds down. Values for the validation-benchmark tracks are unchanged.
- The 48 kHz resample notice is now a DEBUSSY-owned `UserWarning` rather than a
  read of mosqito's stdout, which some builds emit and others do not.

### Changed
- Test suite expanded from 22 to 56 tests, covering short clips, stereo downmix,
  the resample path, calibration offset, empty-onset handling, serialisation,
  clipping, the noise floor, import time, long-input probe mode, `write_csv`
  round-trips and the CLI. Three placeholder tests that were skipped, and so
  asserted nothing, were replaced with real ones.
- The scheduled workflow that paced commits has been retired; the heartbeat
  check remains with a 30-day threshold.

### Added (0.1.x development)
- **Temporal-coverage descriptors** (`Result.roughness_coverage_pct`,
  `Result.sharp_onset_pct`, `Result.sharp_onset_count`) and `coverage_items()` /
  `plot_coverage()`: the proportion of a stimulus that crosses each Tier-1
  threshold, so a long clip that is calm on average no longer hides brief harsh
  passages. Additive — the twelve headline parameters and their validated
  values are unchanged (regression-locked against golden values on short files).
- **Conservative coverage-gated Tier-1 roughness**: the status is the *more
  severe* of the paper's whole-file 0.3 asper check and the proportion of time
  above 0.3 asper (new `CAUTION` status for intermittent roughness). Coverage
  can only make a verdict more conservative, never rescue a high mean. The
  per-frame threshold and the 2 %/10 % bands are documented as provisional
  screening heuristics, not validated cut-offs.
- **Length-aware analysis of long files** (`Result.analysis_mode`): recordings
  longer than 90 s are characterised from evenly spaced short probes spanning
  the whole file (bounded memory/runtime) rather than via a duration limit, so
  long-form ambient/sleep stimuli are supported. Level metrics (LAeq, dynamic
  range, crest) are computed *exactly* over the whole file by streaming — they
  are not estimated from probes. Coverage on long files is a **sample**, so a
  "clean" roughness reading is **never certified** (capped at `CAUTION`). Short
  files — including every validation-benchmark track — are still analysed in
  full, byte for byte.

### Changed
- Sharp-onset share is now an **annotation**, not a hard fail: librosa onset +
  10–90 % rise is an envelope descriptor, not a validated startle metric (it
  ignores absolute level), so it can only downgrade an otherwise-passing attack
  check to `CAUTION` (and only when both substantial and non-incidental,
  `n ≥ 5`). The Tier-1 attack verdict remains the paper's median-onset rule.

### Fixed
- Corrected `Homepage`/`Repository`/`Issues`/CI/clone URLs to the actual
  repository owner (`github.com/hyeonjoong/debussy`).

## [0.1.0] — 2026-05-27

### Added
- Initial library release split from the Hugging Face Space demo.
- `analyze_audio()` single-call entry point returning the `Result` dataclass
  with the reporting items defined in the companion paper.
- Family submodules: `debussy.level`, `debussy.envelope`, `debussy.spectral`,
  `debussy.tonal`, `debussy.psychoacoustic`.
- Tier-1 / Tier-2 / Tier-3 framework helpers (`tier1_items`, `tier2_items`,
  `tier3_items`, `tier1_compliance`, `format_compliance`).
- Optional plotting helpers (`plot_spectrogram`, `plot_parameter_radar`,
  `plot_tier_compliance`).
- `pyproject.toml` packaging (PEP 621).
- pytest test suite.
- GitHub Actions CI on Python 3.10, 3.11, 3.12.

### Validation
- 60-track open-dataset + clinical benchmark:
  - A2 (DEAM low-arousal, *n*=10)
  - B1 (DEAM mid-to-high arousal, *n*=15)
  - B2 (FMA medium, *n*=15, genre-stratified)
  - C1 (BELL-001 SleepThera, *n*=20, breath-paced biofeedback stimuli)
- Fifty-eight of sixty tracks produce twelve non-null parameters in
  physiologically plausible range; the two exceptions are ~10 s breath clips
  with no autocorrelation peak above the voicing gate, so HNR is undefined.
  No failures, no out-of-range values.

[Unreleased]: https://github.com/hyeonjoong/debussy/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/hyeonjoong/debussy/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/hyeonjoong/debussy/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/hyeonjoong/debussy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hyeonjoong/debussy/releases/tag/v0.1.0
