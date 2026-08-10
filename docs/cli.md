# Command-line interface

Installing the package adds a `debussy` console script (equivalently
`python -m debussy._core`).

```bash
debussy STIMULUS.wav [MORE.wav ...] [options]
```

## Options

| Option | Description |
|---|---|
| `--csv PATH` | Append each result as a row to `PATH` (created if missing), in the `Result` field schema. |
| `--lyrics {yes,no,unknown}` | Record whether the stimulus contains lyrics (default `unknown`). |
| `--delivery TEXT` | Free-text delivery descriptor (e.g. `headphones`, `free-field`). |
| `--calibration-offset-db FLOAT` | dB offset added to LAeq for SPL calibration (default `0` → output in dBFS-A). |
| `--suppress-warnings` | Silence the 48 kHz resample notice and the full-scale clipping warning. |

## Examples

```bash
# One file, human-readable report
debussy stimulus.wav

# A folder's worth, appended to a CSV, quiet
debussy stimuli/*.wav --csv report.csv --suppress-warnings

# With SPL calibration
debussy stimulus.wav --calibration-offset-db 94.0
```

The command prints a per-parameter report per file and exits `0` if at least one
file was analysed, `1` otherwise. For programmatic use call
`debussy.analyze_audio()` — see the [Quickstart](quickstart.md).
