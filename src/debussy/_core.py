#!/usr/bin/env python3
"""
DEBUSSY — Descriptive Evidence-Based aUditory Stimulus SurveY

Computes the 12-item acoustic reporting parameters proposed in the BELL
Therapeutics sound paper (Kim, Ha, Park, Thayer, Bosi, Eerola — Table 2 of
the manuscript "Acoustic Parameters and Norms for Autonomic Arousal
Modulation").

Usage:
    python debussy.py audio.wav
    python debussy.py audio.wav --csv results.csv
    python debussy.py a.wav b.wav c.wav --csv compare.csv

Dependencies:
    pip install librosa mosqito soundfile numpy scipy

Items computed:
    1. LAeq + dynamic range  (dB, A-weighted relative to digital full scale)
    2. Attack time distribution (ms; mean / median / SD across detected onsets)
    3. Roughness (asper, Daniel-Weber via mosqito; mean over time)
    4. Tempo / modulation rate (BPM; modulation peak Hz)
    5. Spectral centroid (Hz; mean)
    6. Sharpness (acum, DIN 45692 via mosqito; mean)
    7. Spectral slope β (dimensionless; linear fit of log10(P) vs log10(f))
    8. Harmonicity / HNR (dB; autocorrelation-based, mean over voiced frames)
   11. Spectral Flatness (dimensionless; mean)

Not auto-detected (supply manually with flags):
    9. Lyrics presence   --lyrics yes|no
   10. Delivery method   --delivery "free-field|headphones|binaural|bone-conduction|..."

Notes on calibration:
    Digital audio files do not encode absolute SPL. LAeq is therefore reported
    in dBFS-A (A-weighted, full-scale relative). For true dB SPL, calibrate
    against a reference recording and apply --calibration-offset DB.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import dataclass, asdict, field
from typing import Optional

import numpy as np
import soundfile as sf
import scipy.signal as sps


# ---------- A-weighting (IEC 61672-1) ----------

def a_weighting_filter(fs: float):
    """Return SOS coefficients for an A-weighting filter at sample rate fs."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    A1000 = 1.9997  # gain at 1 kHz (dB), used to normalise

    nums = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20)), 0.0, 0.0, 0.0, 0.0]
    dens = np.convolve(
        [1.0, 4 * np.pi * f4, (2 * np.pi * f4) ** 2],
        [1.0, 4 * np.pi * f1, (2 * np.pi * f1) ** 2],
    )
    dens = np.convolve(np.convolve(dens, [1.0, 2 * np.pi * f3]), [1.0, 2 * np.pi * f2])

    b, a = sps.bilinear(nums, dens, fs)
    return sps.tf2sos(b, a)


def laeq_dbfs(y: np.ndarray, fs: int) -> float:
    """A-weighted equivalent continuous level in dBFS-A (full-scale relative)."""
    sos = a_weighting_filter(fs)
    y_a = sps.sosfilt(sos, y)
    rms = np.sqrt(np.mean(y_a ** 2) + 1e-20)
    return 20.0 * np.log10(rms + 1e-20)


def dynamic_range_db(y: np.ndarray, fs: int, win_ms: float = 50.0) -> float:
    """Crest-style dynamic range: difference between 95th and 5th percentile
    of short-term RMS levels (dB)."""
    win = max(1, int(fs * win_ms / 1000))
    hop = max(1, win // 2)
    if len(y) < win:
        return 0.0
    rms = np.array([
        np.sqrt(np.mean(y[i:i + win] ** 2) + 1e-20)
        for i in range(0, len(y) - win, hop)
    ])
    db = 20.0 * np.log10(rms + 1e-20)
    return float(np.percentile(db, 95) - np.percentile(db, 5))


# ---------- Attack time ----------

def attack_times_ms(y: np.ndarray, fs: int, librosa) -> dict:
    """Estimate per-onset attack times (10%–90% rise time of local envelope)."""
    onsets = librosa.onset.onset_detect(
        y=y, sr=fs, units="samples", backtrack=True
    )
    if len(onsets) < 2:
        return {"n_onsets": int(len(onsets)), "mean_ms": None,
                "median_ms": None, "sd_ms": None, "frac_below_50ms": None}

    env = np.abs(sps.hilbert(y))
    smoothing_n = max(1, int(0.005 * fs))  # 5 ms smoothing
    env = np.convolve(env, np.ones(smoothing_n) / smoothing_n, mode="same")

    attacks = []
    for k, on in enumerate(onsets):
        end = onsets[k + 1] if k + 1 < len(onsets) else min(on + int(0.5 * fs), len(env))
        seg = env[on:end]
        if len(seg) < int(0.005 * fs):
            continue
        peak = seg.max()
        if peak <= 0:
            continue
        thr10 = 0.10 * peak
        thr90 = 0.90 * peak
        i10 = np.argmax(seg >= thr10)
        # i90 search after i10
        post = seg[i10:]
        i90 = np.argmax(post >= thr90)
        if i90 == 0 and post[0] < thr90:
            continue
        attack_samples = i90
        attacks.append(attack_samples / fs * 1000.0)

    if not attacks:
        return {"n_onsets": int(len(onsets)), "mean_ms": None,
                "median_ms": None, "sd_ms": None,
                "frac_below_50ms": None, "n_below_50ms": 0}
    arr = np.array(attacks)
    return {
        "n_onsets": int(len(onsets)),
        "mean_ms": float(np.mean(arr)),
        "median_ms": float(np.median(arr)),
        "sd_ms": float(np.std(arr)),
        # Both the SHARE and the COUNT of onsets faster than the 50 ms startle
        # threshold. Count matters: a couple of incidental sharp transients in a
        # long file should not read the same as pervasive sharp onsets. NOTE:
        # librosa onset + 10-90% rise is an envelope descriptor, not a validated
        # startle metric (it ignores absolute level), so this annotates rather
        # than hard-fails the Tier-1 check.
        "frac_below_50ms": float(np.mean(arr < 50.0) * 100.0),
        "n_below_50ms": int(np.sum(arr < 50.0)),
    }


# ---------- Tempo / modulation rate ----------

def tempo_bpm(y: np.ndarray, fs: int, librosa) -> Optional[float]:
    try:
        t = librosa.feature.tempo(y=y, sr=fs)
        return float(np.atleast_1d(t)[0])
    except Exception:
        return None


def modulation_peak_hz(y: np.ndarray, fs: int) -> Optional[float]:
    """Dominant amplitude-modulation rate (Hz) in 0.5–20 Hz range,
    derived from the envelope spectrum."""
    env = np.abs(sps.hilbert(y))
    # downsample envelope to ~200 Hz
    target_fs = 200
    if fs > target_fs:
        env = sps.resample_poly(env, target_fs, fs)
    else:
        target_fs = fs
    env = env - np.mean(env)
    n = len(env)
    if n < target_fs:
        return None
    spec = np.abs(np.fft.rfft(env))
    freqs = np.fft.rfftfreq(n, 1.0 / target_fs)
    mask = (freqs >= 0.5) & (freqs <= 20.0)
    if not mask.any():
        return None
    band = spec[mask]
    band_f = freqs[mask]
    idx = int(np.argmax(band))
    return float(band_f[idx])


# ---------- Spectral features ----------

def spectral_centroid_hz(y: np.ndarray, fs: int, librosa) -> float:
    sc = librosa.feature.spectral_centroid(y=y, sr=fs)
    return float(np.mean(sc))


def spectral_flatness(y: np.ndarray, librosa) -> float:
    sf_ = librosa.feature.spectral_flatness(y=y)
    return float(np.mean(sf_))


def spectral_slope(y: np.ndarray, fs: int) -> dict:
    """Linear fit of log10(power) vs log10(frequency), 50 Hz – fs/2.
    Returns beta (slope), and the analysis band edges."""
    n = 1 << int(np.ceil(np.log2(min(len(y), 65536))))
    if n < 1024:
        return {"beta": None, "band_lo_hz": None, "band_hi_hz": None}
    seg = y[:n] * np.hanning(n)
    spec = np.abs(np.fft.rfft(seg)) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    lo, hi = 50.0, fs / 2.0
    mask = (freqs >= lo) & (freqs < hi) & (spec > 0)
    if mask.sum() < 16:
        return {"beta": None, "band_lo_hz": lo, "band_hi_hz": hi}
    lf = np.log10(freqs[mask])
    lp = np.log10(spec[mask] + 1e-30)
    beta, _ = np.polyfit(lf, lp, 1)
    return {"beta": float(beta), "band_lo_hz": lo, "band_hi_hz": float(hi)}


# ---------- HNR (autocorrelation-based, à la Praat) ----------

def hnr_db(y: np.ndarray, fs: int,
           f0_min: float = 75.0, f0_max: float = 600.0,
           frame_ms: float = 40.0, hop_ms: float = 10.0) -> Optional[float]:
    frame = int(fs * frame_ms / 1000)
    hop = int(fs * hop_ms / 1000)
    if len(y) < frame:
        return None
    lag_min = max(1, int(fs / f0_max))
    lag_max = min(frame - 1, int(fs / f0_min))
    if lag_max <= lag_min:
        return None

    vals = []
    window = np.hanning(frame)
    for i in range(0, len(y) - frame, hop):
        seg = (y[i:i + frame] - np.mean(y[i:i + frame])) * window
        e0 = np.sum(seg * seg)
        if e0 <= 1e-10:
            continue
        # voicing gate: skip near-silent frames (–40 dB below max RMS)
        # (added below after collecting RMS)
        ac = np.correlate(seg, seg, mode="full")
        ac = ac[len(seg) - 1:]
        ac0 = ac[0]
        if ac0 <= 0:
            continue
        ac_norm = ac / ac0
        peak = np.max(ac_norm[lag_min:lag_max + 1])
        peak = float(np.clip(peak, 1e-6, 0.9999))
        hnr = 10.0 * np.log10(peak / (1.0 - peak))
        vals.append((hnr, np.sqrt(np.mean(seg * seg))))
    if not vals:
        return None
    rms_max = max(v[1] for v in vals)
    if rms_max <= 0:
        return None
    thresh = rms_max * 0.01  # -40 dB gate
    voiced = [v[0] for v in vals if v[1] >= thresh and v[0] > 0]
    if not voiced:
        return None
    return float(np.mean(voiced))


# ---------- Psychoacoustics (mosqito) ----------

def psychoacoustics(y: np.ndarray, fs: int) -> dict:
    """Compute roughness (asper) and sharpness (acum) using mosqito."""
    out = {"roughness_asper": None, "sharpness_acum": None,
           "roughness_coverage_pct": None}
    try:
        from mosqito.sq_metrics import roughness_dw
        R, _, _, _ = roughness_dw(y, fs, overlap=0.5)
        R = np.asarray(R, dtype=float)
        out["roughness_asper"] = float(np.nanmean(R))
        # Temporal coverage: share of the duration whose instantaneous
        # roughness exceeds the 0.3 asper amygdala-activation threshold.
        # The whole-file mean can stay below 0.3 while brief rough passages
        # still cross it — coverage exposes that proportion.
        finite = R[np.isfinite(R)]
        if finite.size:
            out["roughness_coverage_pct"] = float(np.mean(finite > 0.3) * 100.0)
    except Exception as e:
        out["_roughness_err"] = str(e)
    try:
        from mosqito.sq_metrics import sharpness_din_st
        S = sharpness_din_st(y, fs, weighting="din")
        out["sharpness_acum"] = float(np.nanmean(S))
    except Exception as e:
        out["_sharpness_err"] = str(e)
    # (Zwicker loudness was previously computed here but never surfaced in
    # Result — dropped to avoid the wasted per-probe runtime.)
    return out


# ---------- Pipeline ----------

@dataclass
class Result:
    file: str
    duration_s: float
    sample_rate: int
    laeq_dbfs_a: float
    dynamic_range_db: float
    attack_n_onsets: int
    attack_mean_ms: Optional[float]
    attack_median_ms: Optional[float]
    attack_sd_ms: Optional[float]
    roughness_asper: Optional[float]
    tempo_bpm: Optional[float]
    modulation_peak_hz: Optional[float]
    spectral_centroid_hz: float
    sharpness_acum: Optional[float]
    spectral_slope_beta: Optional[float]
    hnr_db: Optional[float]
    lyrics: str  # "yes" / "no" / "unknown"
    delivery: str
    spectral_flatness: float
    crest_factor_db: Optional[float] = None
    # --- Temporal coverage (exploratory; additive — does NOT alter the 12
    # headline parameters or the validation benchmark). Each reports the
    # PROPORTION of the stimulus that violates a Tier-1 threshold, so a long
    # clip that is calm on average but has brief harsh passages no longer
    # passes silently. ---
    roughness_coverage_pct: Optional[float] = None   # % time roughness > 0.3 asper
    sharp_onset_pct: Optional[float] = None           # % onsets attack < 50 ms
    sharp_onset_count: int = 0                        # count of onsets attack < 50 ms
    # "full"  = whole file analysed (exact, used for every benchmark track)
    # "probe" = long file estimated from evenly spaced probes (coverage is a
    #           SAMPLE — rare events may be missed, so "clean" is never certified)
    # "truncated" = long file, only the first window analysed (no seeking)
    analysis_mode: str = "full"
    notes: str = ""


# --- Long-file handling -------------------------------------------------------
# mosqito's roughness runs at ~1.7x real time and an 8 h file would not fit in
# memory, so files longer than MAX_ANALYZE_S are characterised from evenly
# spaced short probes spanning the whole recording rather than by a duration
# cap (long ambient/sleep pieces are legitimate stimuli). Short files — which
# includes every validation-benchmark track — are analysed in full, byte for
# byte as before, so the published parameter values are unchanged.
# Default kept just above the longest validation-benchmark track (45.1 s) so
# every benchmark track is still analysed in full (byte-identical reproduction),
# while any longer upload takes the bounded probe path. The psychoacoustic
# metrics (mosqito roughness/sharpness) run ~real-time on broadband audio, so a
# dense 45 s clip can take ~1 minute on a slow CPU. The interactive Space lowers
# this via DEBUSSY_MAX_ANALYZE_S so even short dense clips stay responsive; the
# library keeps the 50 s default for exact benchmark reproduction.
MAX_ANALYZE_S = float(os.environ.get("DEBUSSY_MAX_ANALYZE_S", "50.0"))
PROBE_S = 3.0             # length of each probe window (s)
PROBE_BUDGET_S = 18.0     # total audio analysed for long files (s)

# Per-field rounding used when aggregating probes (matches _result_from_signal).
_NDIG = {
    "laeq_dbfs_a": 2, "dynamic_range_db": 2, "crest_factor_db": 2,
    "attack_mean_ms": 2, "attack_median_ms": 2, "attack_sd_ms": 2,
    "roughness_asper": 3, "tempo_bpm": 1, "modulation_peak_hz": 3,
    "spectral_centroid_hz": 1, "sharpness_acum": 3, "spectral_slope_beta": 3,
    "hnr_db": 2, "spectral_flatness": 4,
}


def _result_from_signal(y: np.ndarray, fs: int, file: str, duration_s: float,
                        lyrics: str, delivery: str,
                        calibration_offset_db: float = 0.0,
                        extra_note: str = "", analysis_mode: str = "full") -> Result:
    """Compute a full Result from an in-memory mono signal."""
    import librosa  # lazy

    laeq = laeq_dbfs(y, fs) + calibration_offset_db
    drange = dynamic_range_db(y, fs)
    peak = float(np.max(np.abs(y)))
    rms = float(np.sqrt(np.mean(y * y)) + 1e-20)
    crest_db = float(20.0 * np.log10(peak / rms)) if peak > 0 else None
    att = attack_times_ms(y, fs, librosa)
    bpm = tempo_bpm(y, fs, librosa)
    mod = modulation_peak_hz(y, fs)
    sc = spectral_centroid_hz(y, fs, librosa)
    sl = spectral_slope(y, fs)
    flat = spectral_flatness(y, librosa)
    hnr = hnr_db(y, fs)
    psy = psychoacoustics(y, fs)

    notes = []
    if calibration_offset_db == 0.0:
        notes.append("LAeq in dBFS-A (uncalibrated)")
    for k in ("_roughness_err", "_sharpness_err"):
        if psy.get(k):
            notes.append(f"{k.strip('_')}: {psy[k]}")
    if extra_note:
        notes.append(extra_note)

    return Result(
        file=file,
        duration_s=duration_s,
        sample_rate=int(fs),
        laeq_dbfs_a=round(laeq, 2),
        dynamic_range_db=round(drange, 2),
        attack_n_onsets=att["n_onsets"],
        attack_mean_ms=round(att["mean_ms"], 2) if att["mean_ms"] is not None else None,
        attack_median_ms=round(att["median_ms"], 2) if att["median_ms"] is not None else None,
        attack_sd_ms=round(att["sd_ms"], 2) if att["sd_ms"] is not None else None,
        roughness_asper=round(psy["roughness_asper"], 3) if psy["roughness_asper"] is not None else None,
        tempo_bpm=round(bpm, 1) if bpm is not None else None,
        modulation_peak_hz=round(mod, 3) if mod is not None else None,
        spectral_centroid_hz=round(sc, 1),
        sharpness_acum=round(psy["sharpness_acum"], 3) if psy["sharpness_acum"] is not None else None,
        spectral_slope_beta=round(sl["beta"], 3) if sl["beta"] is not None else None,
        hnr_db=round(hnr, 2) if hnr is not None else None,
        lyrics=lyrics,
        delivery=delivery,
        spectral_flatness=round(flat, 4),
        crest_factor_db=round(crest_db, 2) if crest_db is not None else None,
        roughness_coverage_pct=(round(psy["roughness_coverage_pct"], 1)
                                if psy.get("roughness_coverage_pct") is not None else None),
        sharp_onset_pct=(round(att["frac_below_50ms"], 1)
                         if att.get("frac_below_50ms") is not None else None),
        sharp_onset_count=int(att.get("n_below_50ms", 0) or 0),
        analysis_mode=analysis_mode,
        notes="; ".join(notes),
    )


def _stream_level_metrics(path: str, calibration_offset_db: float = 0.0,
                          win_ms: float = 50.0) -> dict:
    """Whole-file LAeq (A-weighted energy), dynamic range (p95-p5 of short-term
    RMS) and crest factor, computed by streaming the file in blocks. These are
    cheap O(n) operations, so for long files they are computed exactly over the
    WHOLE recording rather than estimated from probes — unlike the dynamic
    range, in particular, a few short probes cannot capture the true quiet-to-
    loud span of a long piece."""
    import scipy.signal as sps
    info = sf.info(path)
    fs = int(info.samplerate)
    win = max(1, int(fs * win_ms / 1000))
    sos = a_weighting_filter(fs)
    zi = sps.sosfilt_zi(sos) * 0.0

    sum_sq_a = 0.0      # A-weighted energy → LAeq
    n_a = 0
    sum_sq = 0.0        # broadband energy → global RMS for crest
    n_tot = 0
    peak = 0.0
    st_db = []          # short-term RMS levels (dB) → dynamic range
    carry = np.empty(0, dtype=np.float64)

    for block in sf.blocks(path, blocksize=fs * 30, dtype="float64",
                           always_2d=False):
        if block.ndim > 1:
            block = np.mean(block, axis=1)
        block = np.asarray(block, dtype=np.float64)
        if block.size:
            peak = max(peak, float(np.max(np.abs(block))))
        sum_sq += float(np.sum(block * block)); n_tot += block.size
        ya, zi = sps.sosfilt(sos, block, zi=zi)
        sum_sq_a += float(np.sum(ya * ya)); n_a += ya.size
        buf = np.concatenate([carry, block])
        nwin = len(buf) // win
        if nwin:
            frames = buf[:nwin * win].reshape(nwin, win)
            rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-20)
            st_db.append(20.0 * np.log10(rms + 1e-20))
            carry = buf[nwin * win:]
        else:
            carry = buf

    laeq = 10.0 * np.log10(sum_sq_a / max(n_a, 1) + 1e-20) + calibration_offset_db
    rms_tot = np.sqrt(sum_sq / max(n_tot, 1) + 1e-20)
    crest = float(20.0 * np.log10(peak / rms_tot)) if peak > 0 else None
    if st_db:
        alldb = np.concatenate(st_db)
        dr = float(np.percentile(alldb, 95) - np.percentile(alldb, 5))
    else:
        dr = 0.0
    return {"laeq_dbfs_a": round(float(laeq), 2),
            "dynamic_range_db": round(dr, 2),
            "crest_factor_db": round(crest, 2) if crest is not None else None}


def _aggregate_probes(results: list, file: str, duration_s: float, fs: int,
                      lyrics: str, delivery: str, note: str,
                      level_override: dict) -> Result:
    """Pool per-probe Results: the expensive psychoacoustic / spectral metrics
    are the median across probes; level metrics are overridden with the exact
    whole-file streamed values; onset count is summed; coverage is pooled but
    NEVER used to certify "clean" (see tier1_items)."""
    from statistics import median

    def med(field):
        vals = [getattr(r, field) for r in results if getattr(r, field) is not None]
        return round(float(median(vals)), _NDIG.get(field, 3)) if vals else None

    def avg(field):
        vals = [getattr(r, field) for r in results if getattr(r, field) is not None]
        return round(float(sum(vals) / len(vals)), 1) if vals else None

    return Result(
        file=file,
        duration_s=duration_s,
        sample_rate=int(fs),
        laeq_dbfs_a=level_override.get("laeq_dbfs_a"),
        dynamic_range_db=level_override.get("dynamic_range_db"),
        attack_n_onsets=sum((getattr(r, "attack_n_onsets", 0) or 0) for r in results),
        attack_mean_ms=med("attack_mean_ms"),
        attack_median_ms=med("attack_median_ms"),
        attack_sd_ms=med("attack_sd_ms"),
        roughness_asper=med("roughness_asper"),
        tempo_bpm=med("tempo_bpm"),
        modulation_peak_hz=med("modulation_peak_hz"),
        spectral_centroid_hz=med("spectral_centroid_hz") or 0.0,
        sharpness_acum=med("sharpness_acum"),
        spectral_slope_beta=med("spectral_slope_beta"),
        hnr_db=med("hnr_db"),
        lyrics=lyrics,
        delivery=delivery,
        spectral_flatness=med("spectral_flatness") or 0.0,
        crest_factor_db=level_override.get("crest_factor_db"),
        roughness_coverage_pct=avg("roughness_coverage_pct"),
        sharp_onset_pct=avg("sharp_onset_pct"),
        sharp_onset_count=sum((getattr(r, "sharp_onset_count", 0) or 0) for r in results),
        analysis_mode="probe",
        notes=note,
    )


def analyse(path: str, lyrics: str = "unknown", delivery: str = "unknown",
            calibration_offset_db: float = 0.0) -> Result:
    info = sf.info(path)
    fs = int(info.samplerate)
    total = int(info.frames)
    dur = float(total) / float(fs) if fs else 0.0

    # Short files (incl. every benchmark track): analyse in full, unchanged.
    if dur <= MAX_ANALYZE_S:
        y, fs2 = sf.read(path, always_2d=False)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        y = y.astype(np.float64)
        return _result_from_signal(y, fs2, os.path.basename(path),
                                   round(len(y) / fs2, 3),
                                   lyrics, delivery, calibration_offset_db)

    # Long files: evenly spaced short probes spanning the whole recording.
    probe_frames = int(PROBE_S * fs)
    n_probes = max(4, int(PROBE_BUDGET_S / PROBE_S))
    span = total - probe_frames
    starts = ([0] if span <= 0
              else [int(round(span * i / (n_probes - 1))) for i in range(n_probes)])

    probes = []
    for s in starts:
        try:
            blk, _ = sf.read(path, start=s, stop=min(s + probe_frames, total),
                             always_2d=False)
        except Exception:
            continue
        if blk.ndim > 1:
            blk = np.mean(blk, axis=1)
        if len(blk) >= int(0.5 * fs):
            probes.append(blk.astype(np.float64))

    if not probes:
        # Seeking unsupported for this format: fall back to the first window.
        y, fs2 = sf.read(path, start=0, stop=min(int(MAX_ANALYZE_S * fs), total),
                         always_2d=False)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        y = y.astype(np.float64)
        note = (f"truncated: first {len(y) / fs2:.0f}s of {dur:.0f}s "
                f"(format does not support seeking for probe-based analysis)")
        return _result_from_signal(y, fs2, os.path.basename(path), round(dur, 3),
                                   lyrics, delivery, calibration_offset_db,
                                   extra_note=note, analysis_mode="truncated")

    results = [_result_from_signal(p, fs, "probe", round(len(p) / fs, 3),
                                   lyrics, delivery, calibration_offset_db)
               for p in probes]
    # Level metrics (esp. dynamic range) cannot be recovered from short probes,
    # so compute them exactly over the whole file by streaming.
    level = _stream_level_metrics(path, calibration_offset_db)
    analysed_s = int(len(results) * PROBE_S)
    pct = 100.0 * analysed_s / dur if dur else 0.0
    note = (f"probe-based: {len(results)}x{PROBE_S:.0f}s probes (~{analysed_s}s, "
            f"{pct:.1f}% of {dur:.0f}s); level metrics exact (whole-file stream), "
            f"psychoacoustic/spectral = median across probes; coverage is a "
            f"sample so 'clean' is NOT certified")
    return _aggregate_probes(results, os.path.basename(path), round(dur, 3),
                             fs, lyrics, delivery, note, level)


def print_report(r: Result) -> None:
    rows = [
        ("File",                            r.file),
        ("Duration (s)",                    r.duration_s),
        ("Sample rate (Hz)",                r.sample_rate),
        ("",                                ""),
        ("1. LAeq (dBFS-A)",                r.laeq_dbfs_a),
        ("   Dynamic range (dB, p95-p5)",   r.dynamic_range_db),
        ("2. Attack time mean (ms)",        r.attack_mean_ms),
        ("   Attack time median (ms)",      r.attack_median_ms),
        ("   Attack time SD (ms)",          r.attack_sd_ms),
        ("   Onsets detected",              r.attack_n_onsets),
        ("3. Roughness (asper)",            r.roughness_asper),
        ("4. Tempo (BPM)",                  r.tempo_bpm),
        ("   Modulation peak (Hz)",         r.modulation_peak_hz),
        ("5. Spectral centroid (Hz)",       r.spectral_centroid_hz),
        ("6. Sharpness (acum)",             r.sharpness_acum),
        ("7. Spectral slope β",             r.spectral_slope_beta),
        ("8. HNR (dB)",                     r.hnr_db),
        ("9. Lyrics presence",              r.lyrics),
        ("10. Delivery method",             r.delivery),
        ("11. Spectral flatness",           r.spectral_flatness),
    ]
    width = max(len(k) for k, _ in rows)
    for k, v in rows:
        if k == "":
            print()
            continue
        print(f"  {k.ljust(width)} : {v}")
    if r.notes:
        print(f"\n  notes: {r.notes}")


def write_csv(results: list[Result], csv_path: str) -> None:
    fields = list(asdict(results[0]).keys())
    new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        for r in results:
            w.writerow(asdict(r))


# ---------- Public API alias (matches handoff doc / Gradio app) ----------

def analyze_audio(audio_file: str,
                  delivery_method: str = "unknown",
                  lyrics_presence: Optional[str] = None,
                  calibration_offset_db: float = 0.0) -> Result:
    """Canonical entry point for programmatic use.
    `lyrics_presence` may be 'yes', 'no', None, or 'unknown'."""
    lyrics = lyrics_presence if lyrics_presence in ("yes", "no") else "unknown"
    return analyse(audio_file, lyrics=lyrics,
                   delivery=delivery_method or "unknown",
                   calibration_offset_db=calibration_offset_db)


# ---------- Three-tier framework (paper Sections 3-4) ----------
#
# Tier 1 — Universal Design Check (hard pass/fail or info-only)
# Tier 2 — Directional Guidelines (in-range vs out-of-range, optimize per person)
# Tier 3 — Exploratory / Report Only (no threshold yet)

def _fmt(v, n=3):
    if v is None:
        return "—"
    if isinstance(v, float):
        if abs(v) < 0.01:
            return f"{v:.4f}"
        if abs(v) < 100:
            return f"{v:.{n}g}"
        return f"{v:.1f}"
    return str(v)


_SEVERITY = {"PASS": 0, "CAUTION": 1, "FAIL": 2}


def _worst_status(*statuses):
    """Most severe of the given statuses (FAIL > CAUTION > PASS); None if none
    are gradeable. Used so coverage can only make a verdict more conservative."""
    cand = [s for s in statuses if s in _SEVERITY]
    return max(cand, key=lambda s: _SEVERITY[s]) if cand else None


def tier1_items(r: Result) -> list[dict]:
    """Tier 1 — Universal design principles."""
    items = []

    # Roughness — coverage informs the verdict but only in the SAFE direction:
    # the status is the more severe of (a) the paper's whole-file 0.3 asper check
    # and (b) the proportion of time above 0.3 asper. So a high mean still fails
    # even if coverage looks low, and a low mean is downgraded when rough
    # passages recur. The per-frame 0.3 threshold and the 2%/10% bands are
    # provisional screening heuristics, not validated cut-offs. On long files
    # coverage is sampled (probes), so a "clean" reading is never certified.
    v = r.roughness_asper
    cov = r.roughness_coverage_pct
    probe = (r.analysis_mode != "full")
    if v is None and cov is None:
        items.append({"parameter": "Roughness", "value": "—", "unit": "asper",
                      "target": "mean < 0.3, ≤ 2% time > 0.3", "status": "N/A",
                      "note": "Roughness unavailable"})
    else:
        base = None if v is None else ("PASS" if v < 0.3 else "FAIL")
        if cov is None:
            cov_status, cov_note = None, "no coverage time series"
        elif cov <= 2.0:
            cov_status, cov_note = "PASS", f"{_fmt(cov)}% of time above 0.3 asper"
        elif cov <= 10.0:
            cov_status, cov_note = "CAUTION", f"intermittent — {_fmt(cov)}% of time above 0.3 asper"
        else:
            cov_status, cov_note = "FAIL", f"frequent — {_fmt(cov)}% of time above 0.3 asper"
        status = _worst_status(base, cov_status)
        # A sample cannot prove the absence of brief rough events.
        if probe and status == "PASS":
            status, cov_note = "CAUTION", cov_note + " (sampled — clean not certified)"
        items.append({"parameter": "Roughness", "value": _fmt(v), "unit": "asper",
                      "target": "mean < 0.3, ≤ 2% time > 0.3",
                      "status": status or "N/A", "note": cov_note})

    # Attack time — the Tier-1 verdict is the paper's whole-file median check
    # (> 50 ms). The share/count of sharp onsets is reported and can raise a
    # CAUTION, but is NOT a hard fail: librosa onset + 10-90% rise is an envelope
    # descriptor, not a validated startle metric (it ignores absolute level), and
    # a couple of incidental transients should not condemn a long, quiet piece.
    v = r.attack_median_ms
    sp = r.sharp_onset_pct
    nsharp = r.sharp_onset_count or 0
    if v is None and sp is None:
        items.append({"parameter": "Attack time (median)", "value": "—", "unit": "ms",
                      "target": "median > 50", "status": "N/A",
                      "note": "Too few onsets detected"})
    else:
        if v is None:
            status, note = "N/A", "median undefined"
        else:
            status = "PASS" if v > 50.0 else "FAIL"
            note = f"median {_fmt(v)} ms"
        # Sharp-onset annotation can only downgrade PASS→CAUTION, and only when
        # the pattern is both substantial (share) and non-incidental (count).
        if status == "PASS" and sp is not None and sp > 25.0 and nsharp >= 5:
            status = "CAUTION"
        if sp is not None:
            note += f"; {_fmt(sp)}% of onsets < 50 ms (n={nsharp})"
        items.append({"parameter": "Attack time (median)", "value": _fmt(v), "unit": "ms",
                      "target": "median > 50", "status": status, "note": note})

    # Event structure — informational (dynamic range + crest factor)
    dr = r.dynamic_range_db
    cf = r.crest_factor_db
    ev_val = f"DR {_fmt(dr)} dB / crest {_fmt(cf)} dB"
    items.append({"parameter": "Event structure", "value": ev_val, "unit": "",
                  "target": "lower = calmer", "status": "INFO",
                  "note": "Dynamic range + crest factor (event-free preferred)"})

    # Predictability — not auto-detectable
    items.append({"parameter": "Predictability", "value": "—", "unit": "",
                  "target": "—", "status": "MANUAL",
                  "note": "Structural property — manual assessment required"})
    return items


def tier2_items(r: Result) -> list[dict]:
    """Tier 2 — Directional guidelines (relaxation-oriented)."""
    items = []

    # Tempo — 60-80 BPM relaxation range
    v = r.tempo_bpm
    if v is None:
        items.append({"parameter": "Tempo", "value": "—", "unit": "BPM",
                      "status": "N/A",
                      "guidance": "Tempo not detected"})
    elif 60 <= v <= 80:
        items.append({"parameter": "Tempo", "value": _fmt(v), "unit": "BPM",
                      "status": "IN_RANGE",
                      "guidance": "Within relaxation range (60–80 BPM)"})
    else:
        items.append({"parameter": "Tempo", "value": _fmt(v), "unit": "BPM",
                      "status": "OUT_OF_RANGE",
                      "guidance": "Outside default range — personalization recommended"})

    # Sharpness — < 1.5 acum provisional target
    v = r.sharpness_acum
    if v is None:
        items.append({"parameter": "Sharpness", "value": "—", "unit": "acum",
                      "status": "N/A",
                      "guidance": "Sharpness not computed"})
    elif v < 1.5:
        items.append({"parameter": "Sharpness", "value": _fmt(v), "unit": "acum",
                      "status": "IN_RANGE",
                      "guidance": "Below provisional target (< 1.5 acum)"})
    else:
        items.append({"parameter": "Sharpness", "value": _fmt(v), "unit": "acum",
                      "status": "OUT_OF_RANGE",
                      "guidance": "Above provisional target — consider reducing high-frequency energy"})

    # Spectral centroid — directional only, no absolute threshold
    v = r.spectral_centroid_hz
    items.append({"parameter": "Spectral centroid", "value": _fmt(v), "unit": "Hz",
                  "status": "DIRECTIONAL",
                  "guidance": "Lower values associated with calmer perception (no absolute threshold)"})

    # Spectral slope β — preferred -1 to -2 (pink~brown)
    v = r.spectral_slope_beta
    if v is None:
        items.append({"parameter": "Spectral slope β", "value": "—", "unit": "",
                      "status": "N/A",
                      "guidance": "Slope not computed"})
    elif -2.0 <= v <= -1.0:
        items.append({"parameter": "Spectral slope β", "value": _fmt(v), "unit": "",
                      "status": "IN_RANGE",
                      "guidance": "Within preferred pink-to-brown range (−2 to −1)"})
    elif v > -0.5:
        items.append({"parameter": "Spectral slope β", "value": _fmt(v), "unit": "",
                      "status": "OUT_OF_RANGE",
                      "guidance": "White-like spectrum — consider steeper roll-off"})
    else:
        items.append({"parameter": "Spectral slope β", "value": _fmt(v), "unit": "",
                      "status": "OUT_OF_RANGE",
                      "guidance": "Outside preferred −2 to −1 range"})

    # Complexity — not auto-detectable
    items.append({"parameter": "Complexity", "value": "—", "unit": "",
                  "status": "MANUAL",
                  "guidance": "Composite property — manual assessment required"})

    # Lyrics — manual input
    items.append({"parameter": "Lyrics presence", "value": r.lyrics or "unknown", "unit": "",
                  "status": "MANUAL",
                  "guidance": "Instrumental stimuli preferred for autonomic protocols"})
    return items


def tier3_items(r: Result) -> list[dict]:
    """Tier 3 — Exploratory / report-only parameters."""
    items = []

    # HNR — no universal threshold
    v = r.hnr_db
    items.append({
        "parameter": "Harmonicity / HNR",
        "value": _fmt(v),
        "unit": "dB",
        "interpretation": ("Higher = more tonal" if v is not None else "—"),
        "note": "No universal threshold — large cross-cultural variation (Lahdelma & Eerola, 2022)",
    })

    # Familiarity — listener-dependent
    items.append({
        "parameter": "Familiarity",
        "value": "—",
        "unit": "",
        "interpretation": "Listener-dependent",
        "note": "Cannot be assessed from audio signal alone",
    })

    # Spectral flatness — proposed descriptor
    v = r.spectral_flatness
    if v is None:
        interp = "—"
    elif v < 0.1:
        interp = "Tonal"
    elif v < 0.4:
        interp = "Mixed"
    else:
        interp = "Noise-like"
    items.append({
        "parameter": "Spectral flatness",
        "value": _fmt(v, n=4),
        "unit": "",
        "interpretation": interp,
        "note": "Proposed descriptor — autonomic evidence pending (Bosi & Goldberg, 2003)",
    })
    return items


# ---------- Temporal coverage (exploratory, length-aware) ----------
#
# The 12 headline parameters are whole-file aggregates (means / percentiles),
# so a long stimulus that is calm on average can still contain brief passages
# that cross a Tier-1 threshold — and a mean hides them. Coverage reports the
# PROPORTION of the stimulus that violates each threshold, which is the
# clinically relevant quantity for a "do no harm / no startle" design check
# (a single sharp onset can drive arousal regardless of the average).
#
# This is additive and report-only: it does not change any of the 12
# parameters or the validation benchmark.

def coverage_items(r: Result) -> list[dict]:
    items = []

    v = r.roughness_coverage_pct
    if v is None:
        items.append({"parameter": "Roughness coverage", "value": "—",
                      "threshold": "> 0.3 asper",
                      "interpretation": "—",
                      "note": "Roughness time series unavailable"})
    else:
        if v == 0:
            interp = "Clean — never crosses threshold"
        elif v < 5:
            interp = "Brief excursions only"
        elif v < 25:
            interp = "Intermittent rough passages"
        else:
            interp = "Sustained roughness"
        sampled = " (sampled — clean not certified)" if r.analysis_mode != "full" else ""
        note = "Share of duration above the amygdala-activation threshold" + sampled
        items.append({"parameter": "Roughness coverage", "value": f"{_fmt(v)} %",
                      "threshold": "> 0.3 asper",
                      "interpretation": interp,
                      "note": note})

    v = r.sharp_onset_pct
    n = r.sharp_onset_count or 0
    if v is None:
        items.append({"parameter": "Sharp-onset share", "value": "—",
                      "threshold": "< 50 ms",
                      "interpretation": "—",
                      "note": "Too few onsets detected"})
    else:
        if n == 0:
            interp = "No startle-range onsets"
        elif v < 10 or n < 5:
            interp = "A few sharp onsets (incidental)"
        elif v < 33:
            interp = "Notable share of sharp onsets"
        else:
            interp = "Predominantly sharp onsets"
        items.append({"parameter": "Sharp-onset share", "value": f"{_fmt(v)} % (n={n})",
                      "threshold": "< 50 ms",
                      "interpretation": interp,
                      "note": "Envelope descriptor, not a validated startle metric — annotation only"})

    return items


def plot_coverage(r: Result):
    """Horizontal bars showing the proportion of the stimulus that violates
    each Tier-1 threshold (0 % = clean, 100 % = always violating)."""
    import matplotlib.pyplot as plt
    rows = [
        ("Roughness > 0.3 asper", r.roughness_coverage_pct),
        ("Onsets < 50 ms",        r.sharp_onset_pct),
    ]
    labels = [a for a, _ in rows]
    vals = [(b if b is not None else 0.0) for _, b in rows]

    def _col(p):
        if p is None:
            return "#cccccc"
        if p == 0:
            return "#2ca02c"
        if p < 5:
            return "#a8d08d"
        if p < 25:
            return "#f4b400"
        return "#d62728"

    colors = [_col(b) for _, b in rows]
    fig, ax = plt.subplots(figsize=(7.5, 2.4), dpi=110)
    ax.barh(range(len(labels)), vals, color=colors, edgecolor="white")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of stimulus duration violating threshold", fontsize=9)
    for i, (b) in enumerate(vals):
        txt = "—" if rows[i][1] is None else f"{b:.0f}%"
        ax.text(min(b + 2, 95), i, txt, va="center", fontsize=8)
    ax.set_title("Temporal coverage — how much, not just whether (exploratory)",
                 fontsize=10)
    fig.tight_layout()
    return fig


# Backwards-compatible aliases for older callers
def tier1_compliance(r: Result) -> dict:
    items = tier1_items(r)
    n_pass = sum(1 for it in items if it["status"] == "PASS")
    n_eval = sum(1 for it in items if it["status"] in ("PASS", "FAIL", "CAUTION"))
    # Re-shape to match old API
    checks = []
    for it in items:
        if it["status"] in ("PASS", "FAIL", "CAUTION", "N/A"):
            checks.append({
                "parameter": it["parameter"],
                "value": it["value"],
                "unit": it["unit"],
                "target": it["target"],
                "status": it["status"],
                "note": it["note"],
            })
    return {"checks": checks, "n_pass": n_pass, "n_eval": n_eval, "items": items}


def format_compliance(r: Result) -> str:
    """Text rendering of all three tiers for the CLI."""
    lines = ["", "=== Tier 1 — Universal Design Check ==="]
    for it in tier1_items(r):
        mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "CAUTION": "[CAUT]",
                "INFO": "[INFO]", "MANUAL": "[MAN ]", "N/A": "[N/A ]"}[it["status"]]
        lines.append(f"  {mark} {it['parameter']:24} {str(it['value']):>22} {it['unit']:6}"
                     f"  target {it['target']:<14}  {it['note']}")
    lines += ["", "=== Tier 2 — Directional Guidelines ==="]
    for it in tier2_items(r):
        mark = {"IN_RANGE": "[ IN ]", "OUT_OF_RANGE": "[OUT ]", "DIRECTIONAL": "[DIR ]",
                "MANUAL": "[MAN ]", "N/A": "[N/A ]"}[it["status"]]
        lines.append(f"  {mark} {it['parameter']:24} {str(it['value']):>14} {it['unit']:6}  {it['guidance']}")
    lines += ["", "=== Tier 3 — Exploratory / Report Only ==="]
    for it in tier3_items(r):
        lines.append(f"  [INFO] {it['parameter']:24} {str(it['value']):>14} {it['unit']:6}"
                     f"  {it['interpretation']:<14}  {it['note']}")
    return "\n".join(lines)


# ---------- Visualization ----------

def plot_spectrogram(audio_file: str):
    """Render a mel-spectrogram of the audio file. Returns a matplotlib Figure."""
    import librosa
    import librosa.display
    import matplotlib.pyplot as plt
    y, fs = sf.read(audio_file, always_2d=False)
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    y = y.astype(np.float64)
    S = librosa.feature.melspectrogram(y=y, sr=fs, n_mels=128, fmax=fs / 2)
    S_db = librosa.power_to_db(S, ref=np.max)
    fig, ax = plt.subplots(figsize=(8, 3.5), dpi=110)
    img = librosa.display.specshow(S_db, x_axis="time", y_axis="mel",
                                   sr=fs, fmax=fs / 2, ax=ax)
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    ax.set_title("Mel spectrogram")
    fig.tight_layout()
    return fig


def plot_parameter_radar(r: Result):
    """Radar of 6 auto-detected, normalisable parameters with Tier 1 zones shaded."""
    import matplotlib.pyplot as plt

    # Tuples: (label, value, tier1_max_for_axis, lower_is_better)
    axes = [
        ("Dynamic range\n(dB)",      r.dynamic_range_db,      30.0,  True),
        ("Attack mean\n(ms, inv.)",  r.attack_mean_ms,        200.0, False),
        ("Roughness\n(asper)",       r.roughness_asper,       1.0,   True),
        ("Sharpness\n(acum)",        r.sharpness_acum,        4.0,   True),
        ("Spectral slope β\n(inv.)", -(r.spectral_slope_beta or 0), 4.0, False),
        ("Spectral centroid\n(kHz)", (r.spectral_centroid_hz or 0)/1000.0, 8.0, True),
    ]
    vals = [min((v if v is not None else 0) / mx, 1.0) for _, v, mx, _ in axes]
    labels = [a[0] for a in axes]
    N = len(labels)
    theta = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    theta_closed = theta + [theta[0]]
    vals_closed = vals + [vals[0]]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True), dpi=110)
    ax.plot(theta_closed, vals_closed, color="#1f77b4", linewidth=2)
    ax.fill(theta_closed, vals_closed, alpha=0.25, color="#1f77b4")
    ax.set_xticks(theta)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["", "", "", ""])
    ax.set_ylim(0, 1.0)
    ax.set_title(f"DEBUSSY parameter profile — {r.file}", fontsize=10, pad=15)
    fig.tight_layout()
    return fig


def plot_tier_compliance(r: Result):
    """Stacked bar across all three tiers: green/red for Tier 1 pass/fail,
    amber for Tier 2 in/out-of-range, grey for info/manual/exploratory."""
    import matplotlib.pyplot as plt
    rows, colors = [], []
    status_color = {
        "PASS":         "#2ca02c",
        "FAIL":         "#d62728",
        "CAUTION":      "#e67e22",
        "IN_RANGE":     "#f4b400",
        "OUT_OF_RANGE": "#e67e22",
        "DIRECTIONAL":  "#bbbbbb",
        "INFO":         "#888888",
        "MANUAL":       "#888888",
        "N/A":          "#cccccc",
    }
    for it in tier1_items(r):
        rows.append(("T1 · " + it["parameter"], it["status"]))
    for it in tier2_items(r):
        rows.append(("T2 · " + it["parameter"], it["status"]))
    for it in tier3_items(r):
        rows.append(("T3 · " + it["parameter"], "INFO"))
    labels = [r_[0] for r_ in rows]
    colors = [status_color.get(r_[1], "#888") for r_ in rows]
    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=110)
    ax.barh(range(len(labels)), [1] * len(labels), color=colors, edgecolor="white", linewidth=0.8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    n_t1_pass = sum(1 for it in tier1_items(r) if it["status"] == "PASS")
    n_t1_eval = sum(1 for it in tier1_items(r) if it["status"] in ("PASS", "FAIL", "CAUTION"))
    ax.set_title(f"Three-tier framework — Tier 1: {n_t1_pass}/{n_t1_eval} pass", fontsize=10)
    fig.tight_layout()
    return fig


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute 12-item acoustic reporting parameters for audio file(s).")
    ap.add_argument("files", nargs="+", help="Audio file(s) (wav/flac/mp3 — anything soundfile/librosa can read)")
    ap.add_argument("--csv", help="Append results to this CSV file (created if missing)")
    ap.add_argument("--lyrics", choices=["yes", "no", "unknown"], default="unknown",
                    help="Item #9 — lyrics presence")
    ap.add_argument("--delivery", default="unknown",
                    help="Item #10 — delivery method (e.g. 'headphones', 'free-field', 'binaural', 'bone-conduction')")
    ap.add_argument("--calibration-offset-db", type=float, default=0.0,
                    help="Add this dB offset to LAeq for SPL calibration (default 0 — output in dBFS-A)")
    args = ap.parse_args()

    results = []
    for i, p in enumerate(args.files):
        if not os.path.exists(p):
            print(f"SKIP (not found): {p}", file=sys.stderr)
            continue
        if i > 0:
            print()
        print(f"=== {p} ===")
        try:
            r = analyse(p, lyrics=args.lyrics, delivery=args.delivery,
                        calibration_offset_db=args.calibration_offset_db)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue
        print_report(r)
        results.append(r)

    if args.csv and results:
        write_csv(results, args.csv)
        print(f"\n→ wrote {len(results)} row(s) to {args.csv}")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())

<!-- 2026-07-08 :: core-typing :: refactor(core): tighten type hints on the public analyze_audio() signature -->
