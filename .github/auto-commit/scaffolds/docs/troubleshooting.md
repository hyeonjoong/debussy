# Troubleshooting

## `LibsndfileError` / "Format not recognised" when reading a file

`soundfile` uses libsndfile, whose codec support varies by platform and build.
For MP3/M4A or exotic formats, transcode to WAV first:

```bash
ffmpeg -i input.mp3 -ac 1 -ar 48000 output.wav
```

`-ar 48000` writes 48 kHz so mosqito does not need to resample; `-ac 1` downmixes
to mono (DEBUSSY averages channels anyway).

## `ffmpeg: command not found`

Install ffmpeg via your package manager (`brew install ffmpeg`,
`apt install ffmpeg`, `choco install ffmpeg`). DEBUSSY itself does not call
ffmpeg, but it is the simplest way to prepare unsupported inputs.

## A "[Warning] Signal resampled to 48 kHz" line appears

This is printed by mosqito when the input is not already 48 kHz — it is
informational, not an error. Pass `suppress_warnings=True` (Python) or
`--suppress-warnings` (CLI) to silence it. The reported `sample_rate` stays the
file's native rate.

## A `clipping: N full-scale sample(s)` warning appears

The input has samples pinned at digital full scale (|amplitude| ≥ 0.999), which
distorts level and spectral metrics. Re-export the stimulus with headroom (peak
below 0 dBFS). The warning is recorded in `Result.notes`; `suppress_warnings=True`
silences the warning but keeps the note.

## Analysis of a long file seems approximate

Files longer than `DEBUSSY_MAX_ANALYZE_S` (default 50 s) use probe-based
analysis: level metrics are exact (whole-file stream) but psychoacoustic and
spectral metrics are the median across evenly spaced probes, and a "clean"
verdict is never certified from a sample. Check `Result.analysis_mode` — it is
`"probe"` (or `"truncated"` when the format cannot be seeked) rather than
`"full"`.

## Roughness or sharpness is `None`

mosqito could not compute the metric for this signal (e.g. near-silence or a
signal too short for its analysis window). The underlying error is appended to
`Result.notes`. Level, spectral, and tonal metrics are unaffected.
