# Changelog

All notable changes to DEBUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  with the twelve reporting parameters defined in the companion paper.
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

[Unreleased]: https://github.com/hyeonjoong/debussy/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/hyeonjoong/debussy/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hyeonjoong/debussy/releases/tag/v0.1.0
