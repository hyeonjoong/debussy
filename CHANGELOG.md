# Changelog

All notable changes to DEBUSSY will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-05-27

### Added
- Initial library release split from the Hugging Face Space demo.
- `analyze_audio()` single-call entry point returning the `Result` dataclass
  with the eleven reporting parameters defined in the companion paper.
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
- All sixty tracks produce eleven non-null parameters in physiologically
  plausible range; no failures, no out-of-range values.

[Unreleased]: https://github.com/jjjooong/debussy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jjjooong/debussy/releases/tag/v0.1.0
