# Spectral

**Reporting item 5 — spectral centroid** and **item 7 — spectral slope β.**

```python
from debussy.spectral import spectral_centroid_hz, spectral_slope
```

## `spectral_centroid_hz(y, fs, librosa) -> float`

Mean of `librosa.feature.spectral_centroid` across frames — the spectral centre
of gravity, in Hz. Rises with high-frequency energy, so it tracks perceived
brightness and correlates with (but is not) sharpness.

## `spectral_slope(y, fs) -> dict`

Least-squares slope of log₁₀ power against log₁₀ frequency, fitted over
**50 Hz to fs/2** on a Hann-windowed segment of up to 65 536 samples.

Returns `{"beta": float | None, "band_lo_hz": 50.0, "band_hi_hz": fs/2}`.
`beta` is `None` when the usable segment is under 1024 samples or fewer than 16
bins survive the band mask.

The convention is the familiar one: β ≈ 0 is white, β ≈ −1 pink, β ≈ −2 brown.
More negative means energy concentrated low, which the review associates with
calmer stimuli.

!!! warning "Fixed by design"
    The 50 Hz lower edge and the log–log fit are **fixed and documented** rather
    than configurable. Slope is exquisitely sensitive to band choice, and a
    parameter that each lab tunes silently is not comparable across studies —
    the whole point of the guideline. Override the function explicitly if you
    must deviate, so the deviation is visible at the call site.

!!! note "Short clips"
    The FFT window is rounded **down** to a power of two no larger than the
    signal. Before v0.2.0 it rounded up, which raised an exception on clips
    under about 1.4 s.
