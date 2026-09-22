"""Masking model, and the perceptually weighted spectral flatness it enables.

Item 11 of the reporting set recommends the perceptual spectral flatness
measure, in which the energy at each frequency is weighted by the masking
energy there (Bosi & Goldberg, *Introduction to Digital Audio Coding*,
Springer 2003, p. 218) rather than taken at face value. Unweighted flatness
measures tonality; the perceptual variant measures how tonal the signal is
*to a listener*, discounting energy that sits where hearing is insensitive or
where louder components mask it.

That weighting needs a masking model, and this module is it: MPEG-1
Psychoacoustic Model 1 (ISO/IEC 11172-3, Annex D.1), which Marina Bosi named
as the reference to follow when we asked which model to take. It is
specified in full in the standard, which is what makes it the right choice
here: an implementation can be checked against the published psychoacoustics
rather than against its own plausibility.

The weighted flatness itself is not implemented here yet. The masking
threshold is derived from the signal, so dividing the signal by it flattens
whatever is measured: a pure tone masks itself and comes out flatter than
noise, which inverts the ordering a tonality measure has to produce. Which
normalisation p. 218 intends is a question for the source rather than for
guesswork, and it is outstanding with the author. The threshold this module
returns is the input that variant will need, and is worth having on its own:
it states which parts of a stimulus a listener can actually hear.

What is and is not verified
---------------------------
The standard's own conformance vectors are not public, so this is not
certified bit-exact against the reference decoder, and the docstrings do not
claim it is. What ``tests/test_masking.py`` does check is every
published quantity the model is built from and every qualitative property it
must have: the absolute threshold against the Terhardt formula at named
frequencies and at its minimum, the Bark scale against Zwicker's tabulated
critical-band edges, the spreading function's continuity at all three
internal breakpoints and its asymmetry, tone-versus-noise masker
classification on synthesised signals, monotonicity of the masked threshold
in masker level, and the reduction to the absolute threshold in silence.

Conventions
-----------
Analysis runs at a fixed 48 kHz with a 512-point FFT, the Layer I
configuration the Annex D index rules are written for, so the tonal
neighbourhood widths are the standard's own rather than a reinterpretation.
Input at another rate is resampled. A full-scale sine reads 96 dB SPL, the
standard's normalisation.
"""
from typing import Optional

import numpy as np

#: Analysis rate and transform size: the Layer I configuration that Annex D's
#: tonal-neighbourhood index rules are specified for.
MODEL_SR = 48000
MODEL_NFFT = 512

#: Sound pressure level assigned to a full-scale sine, per the standard.
FULL_SCALE_SPL_DB = 96.0

#: A masker must exceed its neighbours by this much to count as tonal
#: (ISO/IEC 11172-3 Annex D.1, step 2).
TONAL_PROMINENCE_DB = 7.0

#: Two tonal maskers closer than this are not separately resolvable; the
#: weaker is dropped (Annex D.1, step 3).
MASKER_MERGE_BARK = 0.5

#: Zwicker's critical-band edges in Hz. Used to place the noise maskers, one
#: per band, at the geometric mean of the lines that contribute to it.
CRITICAL_BAND_EDGES_HZ = np.array([
    0, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720,
    2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000,
    15500, 24000,
], dtype=float)


def hz_to_bark(f_hz: np.ndarray) -> np.ndarray:
    """Critical-band rate in Bark (Zwicker & Terhardt 1980)."""
    f = np.asarray(f_hz, dtype=float)
    return 13.0 * np.arctan(0.00076 * f) + 3.5 * np.arctan((f / 7500.0) ** 2)


def absolute_threshold_db(f_hz: np.ndarray) -> np.ndarray:
    """Threshold in quiet, dB SPL (Terhardt's approximation).

    This is the curve the standard tabulates. Below 20 Hz the approximation
    diverges, so it is evaluated no lower than that.
    """
    f = np.maximum(np.asarray(f_hz, dtype=float), 20.0) / 1000.0
    return (3.64 * f ** -0.8
            - 6.5 * np.exp(-0.6 * (f - 3.3) ** 2)
            + 1e-3 * f ** 4)


def spreading_db(dz: np.ndarray, masker_spl_db: float) -> np.ndarray:
    """Masking spread, dB, at a Bark distance ``dz`` from a masker.

    The four-branch function of Annex D.1 step 4. It is level-dependent and
    asymmetric: masking reaches further upward in frequency than downward,
    and the upward reach widens with masker level.
    """
    dz = np.asarray(dz, dtype=float)
    x = float(masker_spl_db)
    out = np.full(dz.shape, -np.inf)

    b1 = (dz >= -3.0) & (dz < -1.0)
    out[b1] = 17.0 * (dz[b1] + 1.0) - (0.4 * x + 6.0)

    b2 = (dz >= -1.0) & (dz < 0.0)
    out[b2] = (0.4 * x + 6.0) * dz[b2]

    b3 = (dz >= 0.0) & (dz < 1.0)
    out[b3] = -17.0 * dz[b3]

    b4 = (dz >= 1.0) & (dz < 8.0)
    out[b4] = -17.0 * dz[b4] + 0.15 * x * (dz[b4] - 1.0)

    return out


def _power_spectrum_db(frame: np.ndarray) -> np.ndarray:
    """Hann-windowed power spectrum in dB SPL, full-scale sine at 96 dB."""
    n = MODEL_NFFT
    w = np.hanning(n + 1)[:n]
    # Scaled by the window's coherent gain, so a bin-centred sine of unit
    # amplitude puts |X| = 1 in its bin and therefore reads exactly
    # FULL_SCALE_SPL_DB. A sine between bins reads up to 1.4 dB lower, which
    # is the Hann scalloping loss and not an error.
    scale = 2.0 / np.sum(w)
    spec = np.fft.rfft(frame * w, n=n) * scale
    power = np.abs(spec) ** 2
    return FULL_SCALE_SPL_DB + 10.0 * np.log10(power + 1e-30)


def _tonal_neighbourhood(k: int) -> np.ndarray:
    """Index offsets checked for the 7 dB tonality test (Annex D.1, step 2).

    The neighbourhood widens with frequency because the critical bands do.
    The three ranges are the standard's own, for 48 kHz and a 512-point
    transform.
    """
    if k < 63:
        return np.array([-2, 2])
    if k < 127:
        return np.array([-3, -2, 2, 3])
    return np.arange(-6, 7)[np.abs(np.arange(-6, 7)) >= 2]


def _maskers(spl: np.ndarray, freqs: np.ndarray):
    """Tonal and noise maskers, before decimation.

    Returns two lists of ``(frequency_hz, level_db)``.
    """
    n = len(spl)
    tonal, tonal_lines = [], set()
    kmax = min(n - 7, 250)
    for k in range(2, kmax):
        if not (spl[k] > spl[k - 1] and spl[k] >= spl[k + 1]):
            continue
        nb = _tonal_neighbourhood(k)
        idx = k + nb
        idx = idx[(idx >= 0) & (idx < n)]
        if idx.size and np.all(spl[k] - spl[idx] >= TONAL_PROMINENCE_DB):
            # The masker carries the energy of the peak and its two shoulders.
            lines = [k - 1, k, k + 1]
            power = np.sum(10.0 ** (spl[lines] / 10.0))
            tonal.append((float(freqs[k]), float(10.0 * np.log10(power))))
            tonal_lines.update(lines)
            tonal_lines.update(int(i) for i in idx)

    noise = []
    for lo, hi in zip(CRITICAL_BAND_EDGES_HZ[:-1], CRITICAL_BAND_EDGES_HZ[1:]):
        in_band = np.nonzero((freqs >= lo) & (freqs < hi))[0]
        rest = [int(i) for i in in_band if int(i) not in tonal_lines]
        if not rest:
            continue
        power = np.sum(10.0 ** (spl[rest] / 10.0))
        if power <= 0:
            continue
        # Placed at the geometric mean of the contributing lines, as specified.
        f_geo = float(np.exp(np.mean(np.log(np.maximum(freqs[rest], 1.0)))))
        noise.append((f_geo, float(10.0 * np.log10(power))))

    return tonal, noise


def _decimate(tonal, noise):
    """Drop inaudible maskers, and tonal maskers masked by a stronger one.

    Annex D.1 step 3: a masker below the threshold in quiet cannot mask
    anything, and two tonal maskers within half a Bark are not separately
    resolvable.
    """
    def audible(ms):
        return [(f, x) for f, x in ms
                if x >= float(absolute_threshold_db(np.array([f]))[0])]

    tonal, noise = audible(tonal), audible(noise)
    tonal = sorted(tonal, key=lambda t: -t[1])
    kept = []
    for f, x in tonal:
        z = float(hz_to_bark(np.array([f]))[0])
        if all(abs(z - float(hz_to_bark(np.array([g]))[0])) > MASKER_MERGE_BARK
               for g, _ in kept):
            kept.append((f, x))
    return sorted(kept), noise


def global_masking_threshold_db(frame: np.ndarray) -> np.ndarray:
    """Masked threshold per FFT bin, dB SPL, for one frame.

    The power sum of the threshold in quiet and every individual masker's
    contribution (Annex D.1, step 5).
    """
    spl = _power_spectrum_db(frame)
    freqs = np.fft.rfftfreq(MODEL_NFFT, 1.0 / MODEL_SR)
    z = hz_to_bark(freqs)
    quiet = absolute_threshold_db(freqs)
    total = 10.0 ** (quiet / 10.0)

    tonal, noise = _decimate(*_maskers(spl, freqs))
    for masker_set, tonal_kind in ((tonal, True), (noise, False)):
        for f, x in masker_set:
            zj = float(hz_to_bark(np.array([f]))[0])
            av = (-1.525 - 0.275 * zj - 4.5 if tonal_kind
                  else -1.525 - 0.175 * zj - 0.5)
            lt = x + av + spreading_db(z - zj, x)
            total += 10.0 ** (np.where(np.isfinite(lt), lt, -np.inf) / 10.0)

    return 10.0 * np.log10(np.maximum(total, 1e-30))
