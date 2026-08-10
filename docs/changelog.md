# Changelog

This page surfaces the project `CHANGELOG.md` in the documentation site. The
authoritative history lives in the repository root; notable user-facing changes
are summarised below.

## Unreleased

- **`analyze_audio(..., suppress_warnings=True)`** and CLI `--suppress-warnings`:
  silence the 48 kHz resample notice and the full-scale clipping warning for
  quiet batch runs.
- **`Result.to_dict()` / `Result.to_json()`**: lossless serialisation of every
  reporting field (round-trips back to an equal `Result`).
- **Clipping warning**: a `UserWarning` (and a `Result.notes` annotation) is
  emitted when the input has samples at digital full scale.
- **Fix**: `spectral_slope` no longer raises on clips shorter than ~1.4 s (the
  FFT window could exceed the signal length).
- Expanded the test suite to cover short clips, stereo downmix, the resample
  path, calibration, empty-onset handling, serialisation, clipping, the noise
  floor, import time and long-input probe mode.

See `CHANGELOG.md` for the full, versioned list.
