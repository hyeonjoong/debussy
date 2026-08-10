---
title: 'DEBUSSY: A Python toolbox implementing an eleven-item minimum acoustic reporting guideline for autonomic-arousal stimuli'
tags:
  - Python
  - audio analysis
  - psychoacoustics
  - music information retrieval
  - autonomic arousal
  - reproducibility
authors:
  - name: Hyeon-Joong Kim
    orcid: 0000-0002-2898-0464
    corresponding: true
    affiliation: 1
  - name: Kyurim Kang
    orcid: 0000-0001-8061-4456
    affiliation: 2
  - name: Tuomas Eerola
    orcid: 0000-0002-2896-929X
    affiliation: 3
affiliations:
  - name: Neurotech Research Institute, Bell Therapeutics, Seoul, Republic of Korea
    index: 1
  - name: Center for Music and Medicine, Johns Hopkins University School of Medicine, Baltimore, MD, USA
    index: 2
  - name: Department of Music, Durham University, United Kingdom
    index: 3
date: 10 August 2026
bibliography: paper.bib
---

# Summary

`DEBUSSY` is an open-source Python toolbox implementing the eleven-item minimum
acoustic reporting guideline for autonomic-arousal stimuli proposed in the parent
review [@Kim:2026nbr], in a single call, with output formats designed for
reproducible psychophysiology research. Nine items are measured from the audio
and span five families: level (LAeq, dynamic range, crest
factor), temporal envelope (attack time, tempo, modulation peak), spectral shape
(centroid, slope $\beta$), tonal structure (harmonics-to-noise ratio, spectral
flatness), and psychoacoustic descriptors (roughness in asper, sharpness in
acum); attack time is additionally reported as mean, median and standard
deviation across detected onsets. The remaining two items — lyrics presence and
delivery method — are recorded from the caller, since no analyser can determine
them. DEBUSSY composes time-frequency primitives from `librosa` [@McFee:2015]
with psychoacoustic models from `MOSQITO` [@MOSQITO:2021], adds a small number of
internally implemented metrics (spectral slope $\beta$ on a 50 Hz – $f_s/2$
log–log fit, attack time on an onset-aligned 10–90 % rise window), and exposes
the result through a single `analyze_audio(path)` entry point returning a typed
`Result` dataclass with every item plus run metadata.

# Statement of need

Researchers preparing auditory stimuli for autonomic-arousal experiments —
sleep, anxiety, cardiac vagal tone, biofeedback — routinely characterise their
stimuli using a custom subset of level, temporal, spectral, and psychoacoustic
descriptors, then report them in tables [@Zwicker:2007]. In practice this means
gluing together at least two Python libraries (`librosa` for time-frequency
descriptors, `MOSQITO` for ISO/DIN-aligned psychoacoustic metrics) and writing
several hundred lines of bookkeeping per study. The resulting reports are not
directly comparable across labs, because each lab implements the same parameter
with slightly different choices: window length, A-weighting timebase, onset
detector, library version. DEBUSSY closes this gap with three design choices:

1. **One call, one schema.** A single `analyze_audio()` returns a dataclass
   carrying the eleven items in the order and units of the reporting table of
   the parent review [@Kim:2026nbr], so authors can copy rows into a manuscript
   table without further wrangling.
2. **Standardised internals.** Window lengths, A-weighting filter coefficients
   and the spectral-slope band are fixed and documented; deviating requires an
   explicit override, which leaves a record at the call site.
3. **Tiered evaluation built in.** Each parameter is tagged Tier 1 (universal
   design check), Tier 2 (directional guideline) or Tier 3 (exploratory), which
   separates "is this stimulus admissible?" from "what does this stimulus do?" —
   the operational decision researchers actually face.

# State of the field

Several mature Python toolboxes overlap with DEBUSSY. `librosa` [@McFee:2015] is
the de-facto reference for time-frequency primitives and supplies DEBUSSY's
spectral and temporal building blocks, but ships no psychoacoustic metrics and
no fixed reporting schema. `MOSQITO` [@MOSQITO:2021] provides the ISO 532-1
loudness, DIN 45692 sharpness and Daniel–Weber roughness implementations DEBUSSY
calls, but is a building block rather than a study-facing reporter. `Essentia`
[@Bogdanov:2013] is feature-rich but bundles a large native dependency stack and
targets ML feature extraction rather than human-readable reporting. `Spafe`
[@Malek:2023] shares the "one library, many features" philosophy but focuses on
speech and omits psychoacoustic descriptors. `libsoni` [@OzerEtAl:2024] is
closest in spirit — a layered toolbox built on librosa for one research workflow
— and shaped DEBUSSY's modular layout. DEBUSSY's contribution is therefore not a
new algorithm but an opinionated *report-level* combination of librosa and
MOSQITO with study-facing conventions, a fixed schema, and a validation suite
exercising every parameter on open data.

# Software design

DEBUSSY is organised as five subpackages matching the parameter families —
`level`, `envelope`, `spectral`, `tonal`, `psychoacoustic` — plus a top-level
`analyze_audio()` that orchestrates them and returns the `Result` dataclass.
`Result.to_dict()` and `to_json()` give lossless serialisation; `write_csv()`
appends manuscript-ready rows. Long inputs are characterised from evenly spaced
probes spanning the whole recording, while level metrics are computed exactly by
streaming, so a long file never silently reports a truncated first window. A
Gradio interface on Hugging Face Spaces provides a no-install demo; the library
is the primary deliverable. Full API documentation is published at
<https://hyeonjoong.github.io/debussy>.

# Validation

DEBUSSY was validated on a 60-track benchmark spanning three acoustic
categories: the DEAM static-annotation corpus [@Aljanaki:2017] low-arousal
subset as "relaxation" (A, *n*=10); DEAM mid-to-high arousal plus a
genre-stratified FMA-medium subset [@Defferrard:2017] as "frequently listened"
(B, *n*=30); and the BELL-001 SleepThera breath-paced biofeedback stimuli used
in clinical trials (C, *n*=20). All audio was standardised to 44.1 kHz mono
16-bit PCM WAV. The pipeline produced a complete set of measured values for
**58 of 60 tracks** — the two exceptions are ~10 s breath clips with no autocorrelation
peak above the voicing gate, so HNR is undefined.

The A-vs-B contrast is exploratory and underpowered: three parameters reach
uncorrected *p* < 0.05, but none survive Benjamini–Hochberg correction across
the twelve tests (smallest *q* = .19) and group A is small. The C category
separates far more sharply, with very large effect sizes (|δ| ≥ 0.7) against
*both* music categories on **seven of the twelve measured quantities** — LAeq, dynamic
range, attack-time median, roughness, sharpness, spectral slope $\beta$ and
spectral flatness (crest factor is close behind, δ = +0.81 against A and +0.68
against B) — the acoustic fingerprint expected of quiet, dynamically wide,
sharp-onset breath recordings, and detected across all four family modules. The
purpose is not to argue a substantive claim about music or breath stimuli, which
belongs to the parent review, but to demonstrate that every parameter returns a
sensible, bounded, finite-variance distribution on acoustically very different
material. Two commercial reference lists [@LewisHodgson:2011] are excluded
pending separate licensing; adding them would bring group A to *n*=30. The
manifest, the raw per-track parameter matrix and the scripts that regenerate
both are released in `validation/`.

![Distribution of the twelve quantities DEBUSSY measures on the 60-track benchmark. Violin–box–strip panels show relaxation (A, DEAM low-arousal, *n*=10) versus frequently-listened music (B, DEAM mid-to-high arousal + FMA-medium, *n*=30); green diamonds overlay the BELL-001 clinical stimuli (C, *n*=20). Cliff's δ and Mann–Whitney *p* for the A-vs-B contrast are annotated; asterisks mark uncorrected *p* < 0.05, none of which survive Benjamini–Hochberg correction. \label{fig:distributions}](figures/Fig1_60tracks_with_C_overlay.png)

# Research impact

DEBUSSY was developed in support of an ongoing review of acoustic determinants
of autonomic arousal [@Kim:2026nbr], where it screened candidate stimuli against
a Tier-1 acceptability rubric before they entered behavioural studies. It is now
used in Bell Therapeutics' BELL-001 SleepThera clinical-trial stimulus library,
where table-ready parameter reporting supports design-history and quality
documentation. Releasing it independently of the parent study makes it cheap for
other researchers to characterise stimuli against the same reporting guideline
with the same internal choices, so acoustic descriptors become comparable across
laboratories — for level metrics, comparability additionally requires a shared
calibration offset, since LAeq is reported in uncalibrated dBFS by default.

# AI usage disclosure

Drafting of this manuscript, parts of the test scaffolding, and the
standardisation and batch scripts used Claude (Anthropic) and ChatGPT (OpenAI)
under human authorial review. All algorithmic implementations, every validation
run, every figure, and the final wording were verified by the authors. No
generative AI was used to produce, edit, or curate the audio data or annotations
on which the validation depends.

# Acknowledgements

We thank the Bell Therapeutics Neurotech Research Institute team for
clinical-side requirements and operational support. DEBUSSY builds directly on
`librosa` and `MOSQITO`; we are grateful to both communities.

# References
