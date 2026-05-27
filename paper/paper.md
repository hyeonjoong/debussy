---
title: 'DEBUSSY: A Python toolbox for 11-parameter acoustic reporting of audio stimuli used in autonomic-arousal research'
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
  - name: <Tuomas Eerola — pending consent>
    orcid: 0000-0002-2896-929X
    affiliation: 2
affiliations:
  - name: Neurotech Research Institute, Bell Therapeutics, Seoul, Republic of Korea
    index: 1
  - name: Department of Music, Durham University, United Kingdom
    index: 2
date: <DD Month 2026>
bibliography: paper.bib
---

# Summary

`DEBUSSY` is an open-source Python toolbox that computes a fixed set of eleven acoustic reporting parameters from an audio stimulus, in a single call, with output formats designed for reproducible psychophysiology and autonomic-arousal research. The parameters span five families: level (LAeq, dynamic range, crest factor), temporal envelope (attack time, tempo, modulation peak), spectral shape (centroid, slope $\beta$), tonal structure (harmonics-to-noise ratio, spectral flatness), and psychoacoustic descriptors (roughness in asper, sharpness in acum). DEBUSSY composes time-frequency primitives from `librosa` [@McFee:2015] with psychoacoustic models from `MOSQITO` [@MOSQITO:2021], adds a small number of internally implemented metrics (e.g. spectral slope $\beta$ on a 50 Hz – $f_s/2$ log–log fit, attack time on an onset-aligned 10–90 % rise window), and exposes the result through a single `analyze_audio(path)` entry point that returns a typed `Result` dataclass with all eleven parameters plus run metadata. A Gradio interface on Hugging Face Spaces provides a no-install demo for non-programming users; the underlying library is the primary deliverable.

# Statement of need

Researchers preparing auditory stimuli for autonomic-arousal experiments — sleep, anxiety, cardiac vagal tone, biofeedback — routinely characterise their stimuli using a custom subset of level, temporal, spectral, and psychoacoustic descriptors, then report them in tables [@Zwicker:2007]. In practice, building this characterisation requires gluing together at least two Python libraries (`librosa` for time-frequency descriptors, `MOSQITO` for ISO/DIN-aligned psychoacoustic metrics) and writing several hundred lines of bookkeeping per study. The resulting reports are not directly comparable across labs because each lab implements the same parameter with slightly different choices (window length, A-weighting timebase, onset detector, mosqito version). DEBUSSY closes this gap with three design choices:

1. **One call, eleven parameters, one schema.** A single `analyze_audio()` returns a dataclass with the eleven parameters in the order and units of the reporting table used in [@KimPlaceholder:2026], so authors can copy-paste rows into a manuscript table without further wrangling.
2. **Standardised internals.** Window lengths, A-weighting filter coefficients, and the spectral-slope band are fixed and documented; users who need to deviate from these defaults must override the relevant function explicitly, leaving a record in the call site.
3. **Tier-1 / Tier-2 / Tier-3 evaluation built in.** Each parameter is tagged with a tier indicating whether it is a Tier-1 universal design check, a Tier-2 directional guideline, or a Tier-3 exploratory descriptor. This separates "is this stimulus admissible?" from "what does this stimulus do?", which is the operational decision researchers actually have to make.

# State of the field

Several mature Python toolboxes overlap with DEBUSSY. `librosa` [@McFee:2015] is the de-facto reference for time-frequency primitives in music-information-retrieval research and supplies the spectral and temporal building blocks DEBUSSY uses; it does not, however, ship psychoacoustic metrics (roughness, sharpness) and does not produce a single fixed reporting schema. `MOSQITO` [@MOSQITO:2021] provides the ISO 532-1 loudness, DIN 45692 sharpness, and Daniel–Weber roughness implementations that DEBUSSY calls, but it is a building block rather than a study-facing reporter. `Essentia` [@Bogdanov:2013] is feature-rich but bundles a large native dependency stack and is oriented to ML-feature extraction rather than human-readable reporting. `Spafe` [@Malek:2023] focuses on speech feature extraction and shares DEBUSSY's "single library covers many features" philosophy, but does not include psychoacoustic descriptors or autonomic-research conventions. `libsoni` [@OzerEtAl:2024] is the closest in spirit (a layered Python toolbox built on librosa for a specific research workflow, in their case sonification) and provided a model for the modular subpackage layout DEBUSSY adopts. DEBUSSY's contribution is therefore not a new algorithm, but an opinionated *report-level* combination of librosa and MOSQITO with study-facing conventions, a fixed reporting schema, and a validation suite that exercises every parameter on open data.

# Software design

DEBUSSY is structured as five subpackages corresponding to the five parameter families, plus a top-level `analyze_audio()` function that orchestrates them:

- `debussy.level` — LAeq (A-weighted, uncalibrated dBFS unless a calibration offset is provided), dynamic range (95th – 5th percentile of short-term RMS), crest factor (20 · log₁₀ peak / RMS).
- `debussy.envelope` — attack time per onset (10–90 % rise window, mean / median / SD), tempo (`librosa` beat tracker), modulation peak (envelope spectrum peak in 0.5 – 20 Hz).
- `debussy.spectral` — spectral centroid, spectral slope $\beta$ on the 50 Hz – $f_s/2$ band of a log–log PSD fit.
- `debussy.tonal` — harmonics-to-noise ratio from autocorrelation on voiced frames; spectral flatness in [0, 1].
- `debussy.psychoacoustic` — roughness in asper (Daniel–Weber, via MOSQITO); sharpness in acum (DIN 45692, via MOSQITO).

The Gradio web interface at `huggingface.co/spaces/jjjooong/debussy` is built on top of the library and provides a no-install demo for non-programming users; it is not the primary deliverable. Figure 1 in the validation section shows the per-parameter distribution for the validation benchmark; readers interested in algorithmic details should consult the library's documentation site.

# Validation

DEBUSSY was validated on a 60-track benchmark spanning three acoustic categories: the DEAM static-annotation corpus [@Aljanaki:2017], the FMA-medium subset [@Defferrard:2017], and the BELL-001 SleepThera breath-paced biofeedback stimulus set used in clinical trials. Tracks were selected by deterministic, documented criteria — DEAM low-arousal subset for the "relaxation" category A (*n*=10); DEAM mid-to-high arousal subset and FMA-medium subset (genre-stratified across Rock, Pop, Hip-Hop, Electronic, Folk, Jazz, International and Instrumental) for "frequently listened" B (*n*=30); and the BELL-001 SleepThera library covering four progressive training days × inhale/exhale pairs for clinical-trial stimuli C (*n*=20). All audio was standardised to 44.1 kHz mono 16-bit PCM WAV. The full pipeline (`analyze_audio()` on each clip) completed in approximately 37 minutes on a single thread of an Apple M-series CPU, and produced eleven non-null parameters for **59 of 60 tracks** (one HNR value undefined for a very short BELL-001 exhale clip with no voiced frames; all other parameters present for every track). The validation script, the audio manifest, and the raw per-track parameter matrix are released alongside the paper.

![Distribution of the twelve DEBUSSY reporting parameters on the 60-track validation benchmark. Violin–box–strip combinations show the "relaxation" category A (DEAM low-arousal, *n*=10) versus the "frequently-listened" category B (DEAM mid-to-high arousal + FMA-medium, *n*=30); green diamonds overlay the BELL-001 SleepThera clinical-trial stimuli C (*n*=20). Cliff's δ and Mann–Whitney *p*-values for the A-vs-B contrast are annotated; asterisks mark *p* < 0.05. The BELL-001 stimuli separate sharply from both music categories on level (LAeq), dynamic range, attack time, roughness, sharpness, spectral slope and spectral flatness, consistent with their character as quiet, dynamically wide, sharp-onset breath recordings rather than continuous music. \label{fig:distributions}](figures/Fig1_60tracks_with_C_overlay.png)

Three parameters reach medium effect size at *p* < 0.05 for the A-vs-B contrast: LAeq (δ = +0.44, *p* = .041), attack-time median (δ = +0.43, *p* = .047), and spectral centroid (δ = +0.45, *p* = .038). Two commercial reference lists (Mindlab Top 10 [@LewisHodgson:2011] and a clinical/research-cited relaxation set including Arvo Pärt, Brian Eno, Erik Satie, Claude Debussy and others) are excluded from this validation pending separate licensing; their inclusion will bring the A category to *n*=30.

The BELL-001 stimuli (C) provide the most striking demonstration of DEBUSSY's discrimination capacity: relative to both A and B, they show very large effect sizes (|δ| ≥ 0.7) on **eight of the twelve parameters** — LAeq (markedly quieter, median −37.5 vs −17.4 dBFS-A in A), dynamic range (much wider, 65.6 vs 7.8 dB), crest factor (higher peak-to-RMS), attack-time median (shorter onsets), roughness (near-zero amplitude modulation), sharpness (much lower high-frequency emphasis), spectral slope β (less steep) and spectral flatness (much more noise-like). This is the acoustic fingerprint expected for breath recordings, and is identified consistently by every DEBUSSY family-module. The point of the validation is not to argue any substantive claim about music or breath stimuli — that is the role of the parent study — but to demonstrate that **every one of the eleven DEBUSSY parameters returns a sensible, finite, finite-variance distribution on three acoustically very different stimulus categories**, and that the parameters together discriminate categories with large effect sizes when meaningful acoustic differences exist. \autoref{fig:distributions} shows the full result.

# Research impact

DEBUSSY was developed in support of an ongoing review of acoustic determinants of autonomic arousal [@KimPlaceholder:2026], where it screened candidate stimuli against an internal acceptability rubric (Tier-1 universal design check) before they entered behavioural studies. It is now used in Bell Therapeutics' BELL-001 SleepThera clinical-trial stimulus library, where reproducible, table-ready parameter reporting is a regulatory requirement. By releasing DEBUSSY independently of the parent study, we aim to make it cheap for other autonomic-arousal researchers to characterise stimuli using the same eleven parameters with the same internal choices, so that acoustic descriptors become directly comparable across studies and laboratories.

# AI usage disclosure

Drafting of this manuscript, parts of the test scaffolding, and the standardisation/batch scripts used Claude (Anthropic) and ChatGPT (OpenAI) under human authorial review. All algorithmic implementations, every validation run, every figure, and the final wording of the paper were verified by the authors. No generative AI was used to produce, edit, or curate the audio data or annotations on which the validation depends.

# Acknowledgements

We thank Tuomas Eerola (Durham University) for discussion of the validation framing and stimulus selection criteria, and the Bell Therapeutics Neurotech Research Institute team for clinical-side requirements and operational support. DEBUSSY builds directly on `librosa` and `MOSQITO`; we are grateful to both communities.

# References
