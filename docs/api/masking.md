# Masking

Groundwork for reporting item 11, the perceptually weighted spectral flatness.
MPEG-1 Psychoacoustic Model 1, ISO/IEC 11172-3 Annex D.1.

```python
from debussy.masking import global_masking_threshold_db
```

Item 11 recommends the perceptual spectral flatness measure, in which the energy
at each frequency is weighted by the masking energy there (Bosi and Goldberg,
*Introduction to Digital Audio Coding*, Springer 2003, p. 218). That weighting
needs a masking model, and this module is it.

!!! note "Nothing here runs inside `analyze_audio()`"
    The weighted flatness itself is not implemented, so no reported value comes
    from this module, and `Result.spectral_flatness` remains the unweighted
    geometric-to-arithmetic mean ratio from [Tonal](tonal.md). The masked
    threshold is derived from the signal, so dividing the signal by it flattens
    whatever is measured: a pure tone masks itself and comes out flatter than
    noise, which inverts the ordering a tonality measure has to produce. Which
    normalisation p. 218 intends is a question for the source rather than for
    guesswork, and it is outstanding with the author.

    The threshold is the input that variant will need, and is useful on its own:
    it states which parts of a stimulus a listener can actually hear.

## Calling convention

The model runs at one fixed configuration, the Layer I setup that Annex D's
tonal-neighbourhood index rules are written for, so that the neighbourhood
widths are the standard's own rather than a reinterpretation.

| Constant | Value | Meaning |
|---|---|---|
| `MODEL_SR` | 48000 | Sample rate the model is specified at |
| `MODEL_NFFT` | 512 | Transform size |
| `FULL_SCALE_SPL_DB` | 96.0 | Level assigned to a full-scale sine |
| `TONAL_PROMINENCE_DB` | 7.0 | Margin over its neighbours for a masker to count as tonal (step 2) |
| `MASKER_MERGE_BARK` | 0.5 | Tonal maskers closer than this are not separately resolvable (step 3) |
| `CRITICAL_BAND_EDGES_HZ` | 26 values | Zwicker's band edges, one noise masker per band |

The caller supplies the framing. `global_masking_threshold_db` takes exactly
`MODEL_NFFT` samples and has no sample-rate argument, so it cannot and does not
resample: the frame is assumed to be at `MODEL_SR` already, and any other length
raises `ValueError` from the window multiply. Resample and frame the signal
before calling.

```python
import numpy as np
from debussy.masking import MODEL_SR, MODEL_NFFT, global_masking_threshold_db

t = np.arange(MODEL_NFFT) / MODEL_SR
frame = np.sin(2 * np.pi * 1031.25 * t)        # one full-scale 1 kHz frame
threshold = global_masking_threshold_db(frame)  # 257 values, dB SPL
```

## `global_masking_threshold_db(frame) -> np.ndarray`

The masked threshold for one frame: 257 values in dB SPL, one per real-FFT bin,
spaced 93.75 Hz apart. It is the power sum of the threshold in quiet and every
surviving masker's contribution (Annex D.1 step 5), so it is never below the
threshold in quiet.

Four steps run inside it:

1. Spectrum. Hann-windowed power spectrum in dB SPL, scaled by the window's
   coherent gain so a bin-centred full-scale sine reads exactly 96.00 dB. A sine
   between bins reads up to 1.4 dB lower, which is Hann scalloping loss and not
   an error.
2. Masker identification. A local peak that exceeds every neighbour in its index
   neighbourhood by `TONAL_PROMINENCE_DB` becomes a tonal masker carrying the
   energy of the peak and its two shoulders; the neighbourhood widens with
   frequency, as the critical bands do. Everything not claimed by a tonal masker
   is pooled into one noise masker per critical band, placed at the geometric
   mean of its contributing lines.
3. Decimation. Maskers below the threshold in quiet are dropped, and of two
   tonal maskers within `MASKER_MERGE_BARK` only the stronger is kept.
4. Spreading. Each masker gets its masking index, which is steeper for tonal than
   for noise maskers and frequency-dependent in both cases, and is then spread by
   `spreading_db`.

Tonal peaks in the lowest two bins (below about 190 Hz) and in the top seven are
not picked up as tonal maskers, because the index neighbourhood would run off the
end of the spectrum. Their energy still raises the threshold through the noise
masker for their critical band: a full-scale 93.8 Hz tone yields no tonal masker
and still lifts its own bin from 24.2 dB in quiet to 79.9 dB.

Masking is local. A full-scale 1031 Hz tone raises the 1125 Hz bin to 79.7 dB
while leaving the 10 kHz bin at 10.7 dB, against 10.6 dB in quiet.

## `absolute_threshold_db(f_hz) -> np.ndarray`

Threshold in quiet in dB SPL, by Terhardt's approximation, which is the curve the
standard tabulates. 3.37 dB at 1 kHz, with its minimum of -4.98 dB at 3324 Hz,
inside the 3 to 4 kHz band where hearing is most sensitive.

The approximation diverges below 20 Hz, so the frequency is clamped there:
anything below 20 Hz returns the 20 Hz value of 83.2 dB rather than a number that
keeps climbing.

## `hz_to_bark(f_hz) -> np.ndarray`

Critical-band rate in Bark (Zwicker and Terhardt 1980). Against the 24 tabulated
interior edges in `CRITICAL_BAND_EDGES_HZ`, which should land on whole Bark
numbers, it agrees to 0.20 Bark at worst and 0.09 Bark at the median.

## `spreading_db(dz, masker_spl_db) -> np.ndarray`

How far a masker's masking reaches, in dB relative to the masker, at a Bark
distance `dz` from it. Positive `dz` is above the masker in frequency. This is
the four-branch function of Annex D.1 step 4; outside its support, below -3 Bark
and at or above +8 Bark, it returns `-inf`.

It is asymmetric and level-dependent, which is the point of using it rather than
a fixed skirt: masking reaches further upward in frequency than downward, the
upward reach widens with masker level, and the downward skirt steepens.

| Masker level | At +2 Bark | At -2 Bark |
|---|---|---|
| 40 dB | -28 dB | -39 dB |
| 60 dB | -25 dB | -47 dB |
| 80 dB | -22 dB | -55 dB |

## What is and is not verified

The standard's own conformance vectors are not public, so this is not certified
bit-exact against the reference decoder, and neither the docstrings nor this page
claim it is.

What `tests/test_masking.py` checks is every published quantity the model is
built from, and every qualitative property it must have to be a masking model at
all: the absolute threshold against the Terhardt formula at named frequencies and
at its minimum, the Bark scale against Zwicker's tabulated critical-band edges,
the spreading function's continuity at all three internal breakpoints and its
asymmetry, tone-versus-noise masker classification on synthesised signals,
monotonicity of the masked threshold in masker level, locality, and reduction to
the threshold in quiet on silence, which it matches to 2.8e-14 dB.
