# FAQ

## What does DEBUSSY compute?

Twelve reporting parameters for autonomic-arousal stimulus preparation: A-weighted
level (LAeq, dBFS-A), dynamic range, crest factor, onset attack times, roughness
(asper), tempo / amplitude-modulation rate, spectral centroid, sharpness (acum),
spectral slope, harmonics-to-noise ratio, spectral flatness, plus the two
categorical fields (lyrics, delivery). Length-aware temporal-coverage descriptors
report the *proportion* of a clip that crosses each Tier-1 threshold.

## How do I analyse one file?

```python
from debussy import analyze_audio
r = analyze_audio("stimulus.wav")
print(r.laeq_dbfs_a, r.roughness_asper)
print(r.to_json())          # full result as JSON
```

## Which file formats and sample rates are supported?

Anything `soundfile`/`libsndfile` can read (WAV, FLAC, OGG, AIFF …). MP3 support
depends on your libsndfile build; if it fails, decode to WAV first (see
[Troubleshooting](troubleshooting.md)). Any sample rate is accepted; mosqito
resamples to 48 kHz internally for the psychoacoustic metrics and prints a
notice — pass `suppress_warnings=True` to silence it.

## Why is `laeq_dbfs_a` negative?

Digital audio carries no absolute SPL, so LAeq is reported in dBFS-A (A-weighted,
full-scale relative), which is ≤ 0. For true dB SPL, calibrate against a reference
recording and pass `calibration_offset_db=<offset>`; the offset is added directly
to LAeq and nothing else.

## Why are some parameters `None`?

Some metrics are undefined on adversarial inputs: a pure tone has no amplitude
modulation (roughness/modulation may be None), and a clip with fewer than two
detected onsets has no attack estimate. `None` means "not well-defined here", not
"error".

## Do I need a GPU?

No. Analysis is CPU-only. mosqito's roughness runs at roughly real time, so files
longer than ~50 s are characterised from evenly spaced probes rather than in full;
set `DEBUSSY_MAX_ANALYZE_S` to change the cap.
