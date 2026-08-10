# Tonal

**Reporting item 8 — harmonicity / HNR** and **item 11 — spectral flatness.**

```python
from debussy.tonal import hnr_db, spectral_flatness
```

## `hnr_db(y, fs, f0_min=75.0, f0_max=600.0, frame_ms=40.0, hop_ms=10.0) -> float | None`

Harmonics-to-noise ratio in dB, by autocorrelation on voiced frames. For each
40 ms frame the normalised autocorrelation peak *r* is found in the lag range
implied by `f0_min`–`f0_max`, and converted as `10·log₁₀(r / (1 − r))`. Frames
below −40 dB relative to the loudest frame are gated out as unvoiced; the return
value is the mean over the surviving frames.

**Returns `None`** when the signal is shorter than one frame, when the lag range
collapses, or when no frame passes the voicing gate. This is common and
legitimate — two of the sixty benchmark tracks are ~10 s breath recordings with
no autocorrelation peak above the gate, and report `None` rather than a
fabricated number.

Higher HNR means a clearer tonal structure; the review places harmonicity in
Tier 3, since the direction of its effect depends on cultural and individual
factors that cannot be prescribed universally.

## `spectral_flatness(y, librosa) -> float`

Mean of `librosa.feature.spectral_flatness` — the ratio of geometric to
arithmetic mean of the power spectrum, bounded in [0, 1]. Near 0 is tonal, near
1 is noise-like.

This formalises the tonal-to-noise continuum that separates predictable tonal
stimuli from broadband masking noise, which is why it earns a reporting slot
even though it is Tier 3 for design purposes.
