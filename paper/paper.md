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
  - name: Jonghwa Jeonglok Park
    orcid: 0000-0002-0097-5196
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
acoustic reporting guideline for autonomic-arousal stimuli proposed in the
parent review [@Kim:2026nbr], in a single call, with output formats designed
for reproducible psychophysiology research. Nine items are measured from the
audio — LAeq and dynamic range, attack time, tempo and modulation rate,
spectral centroid and slope $\beta$, harmonics-to-noise ratio, spectral
flatness, roughness in asper and sharpness in acum. The remaining two, lyrics
presence and delivery method, are recorded from the caller, since no analyser
can determine them. DEBUSSY composes `librosa` [@McFee:2015] time-frequency
primitives with `MOSQITO` [@MOSQITO:2021] psychoacoustic models and a few
internally implemented metrics behind a single `analyze_audio(path)` entry
point, returning a typed `Result` dataclass with every item plus run metadata.

# Statement of need

Researchers preparing auditory stimuli for autonomic-arousal experiments —
sleep, anxiety, cardiac vagal tone, biofeedback — routinely characterise their
stimuli with a custom subset of level, temporal, spectral and psychoacoustic
descriptors, then report them in tables [@Zwicker:2007]. That means gluing at
least two Python libraries together and several hundred lines of bookkeeping
per study, and the results are not comparable across labs, because each
implements the same parameter with slightly different choices: window length,
A-weighting timebase, onset detector, library version. DEBUSSY fixes those
choices and names them, returning one dataclass carrying the eleven items in
the order and units of the review's reporting table [@Kim:2026nbr]; deviating
from a documented constant requires an explicit override, recorded at the call
site.

Each parameter also carries the review's tier — Tier 1 (fixed design
constraint, one value serving every listener), Tier 2 (directional, optimum set
per listener) or Tier 3 (exploratory). Only Tier 1 is graded pass/fail, and
against *reference values* the review reports rather than validated cut-offs: a
failing status means "outside the range the cited literature reports", not
"shown to raise arousal".

# State of the field

Several mature Python toolboxes overlap with DEBUSSY. `librosa` [@McFee:2015]
and `MOSQITO` [@MOSQITO:2021], which DEBUSSY calls, are libraries rather than
study-facing reporters, and neither fixes a reporting schema. `Essentia`
[@Bogdanov:2013] targets ML feature extraction and bundles a large native
dependency stack; `Spafe` [@Malek:2023] focuses on speech and omits
psychoacoustic descriptors. `libsoni` [@OzerEtAl:2024] is closest in spirit — a
layered toolbox built on librosa for one research workflow — and shaped
DEBUSSY's modular layout. DEBUSSY's contribution is not a new algorithm but an
opinionated *report-level* combination with a fixed schema; a
capability-by-capability comparison is maintained in the documentation.

# Software design

DEBUSSY is organised as five subpackages matching the parameter families, plus
a top-level `analyze_audio()` returning the `Result` dataclass, with lossless
JSON serialisation and manuscript-ready CSV rows. Long inputs are characterised
from evenly spaced probes spanning the whole recording, while level metrics are
computed exactly by streaming, so a long file never silently reports a
truncated first window. The library, not the Hugging Face Spaces demo, is the
citable artefact; full documentation is at
<https://hyeonjoong.github.io/debussy>.

# Validation

DEBUSSY was validated on a 60-track benchmark of three acoustic categories:
DEAM [@Aljanaki:2017] low-arousal "relaxation" (A, *n*=10), DEAM mid-to-high
arousal plus a genre-stratified FMA-medium subset [@Defferrard:2017] as
"frequently listened" (B, *n*=30), and BELL-001 SleepThera breath-paced
biofeedback stimuli (C, *n*=20). Complete measured values were produced for
**58 of 60 tracks**, the two exceptions being short breath clips for which HNR
is undefined.

The point is not a claim about music or breath stimuli, which belongs to the
parent review, but a demonstration that every parameter returns a bounded,
finite-variance distribution on acoustically very different material. Category C
separates from both music categories with very large effect sizes on seven of
the twelve quantities. The A-vs-B contrast is underpowered — nothing survives
Benjamini–Hochberg correction, and at *n*=10 its δ values are unstable in sign:
redrawn at 150 per group in the same bands, eleven of twelve separate and four
reverse. Two commercial lists [@LewisHodgson:2011] await licensing. The
manifest, parameter matrix, statistics and regenerating scripts are in
`validation/` and described at
<https://hyeonjoong.github.io/debussy/validation/>.

![Distribution of the twelve quantities DEBUSSY measures on the 60-track benchmark. Violin–box–strip panels show relaxation (A, *n*=10) versus frequently-listened music (B, *n*=30); green diamonds overlay the clinical stimuli (C, *n*=20). Cliff's δ and Mann–Whitney *p* for the A-vs-B contrast are annotated; asterisks mark uncorrected *p* < 0.05, none of which survive correction; see `validation/sensitivity_power.py`. \label{fig:distributions}](figures/Fig1_60tracks_with_C_overlay.png)

# Research impact

DEBUSSY was developed in support of an ongoing review of acoustic determinants
of autonomic arousal [@Kim:2026nbr], where it screened candidate stimuli
against the Tier-1 reference values, and is now used in Bell Therapeutics'
BELL-001 SleepThera clinical-trial stimulus library, where table-ready
reporting supports design-history documentation. Releasing it independently
lets others characterise stimuli against the same guideline with the same
internal choices, though comparing level metrics also needs a shared
calibration offset, since LAeq is uncalibrated dBFS by default.

# AI usage disclosure

Drafting of this manuscript, parts of the test scaffolding, and the
standardisation and batch scripts used Claude (Anthropic) and ChatGPT (OpenAI)
under human authorial review. All algorithmic implementations, validation runs,
figures and final wording were verified by the authors. No generative AI
produced, edited or curated the audio data or annotations the validation rests
on.

# Acknowledgements

We thank the Bell Therapeutics Neurotech Research Institute team for
clinical-side requirements and operational support, and the `librosa` and
`MOSQITO` communities, on whose work DEBUSSY builds directly.

# References
