# DEBUSSY

[![CI](https://github.com/jjjooong/debussy/actions/workflows/tests.yml/badge.svg)](https://github.com/jjjooong/debussy/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/debussy-audio.svg)](https://pypi.org/project/debussy-audio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![HuggingFace Demo](https://img.shields.io/badge/🤗-Try%20on%20HF%20Spaces-yellow)](https://huggingface.co/spaces/jjjooong/debussy)

> **DEBUSSY** is a Python toolbox that computes a fixed set of **eleven acoustic
> reporting parameters** from an audio stimulus, in a single call, with output
> formats designed for **reproducible psychophysiology and autonomic-arousal
> research**.

## Statement of need

Researchers preparing auditory stimuli for autonomic-arousal experiments — sleep,
anxiety, cardiac vagal tone, biofeedback — routinely characterise their stimuli
using a custom subset of level, temporal, spectral, and psychoacoustic
descriptors, then report them in tables. Building this characterisation usually
means gluing together at least two Python libraries (`librosa` for time-frequency
descriptors, `MOSQITO` for ISO/DIN-aligned psychoacoustic metrics) and writing
several hundred lines of bookkeeping per study. The resulting reports are not
directly comparable across labs because each lab implements the same parameter
with slightly different choices (window length, A-weighting timebase, onset
detector, mosqito version).

DEBUSSY closes this gap with three design choices:

1. **One call, eleven parameters, one schema.** A single `analyze_audio()`
   returns a dataclass with the eleven parameters in the order and units of the
   reporting table used in our companion review paper.
2. **Standardised internals.** Window lengths, A-weighting filter coefficients,
   and the spectral-slope band are fixed and documented.
3. **Tier-1 / Tier-2 / Tier-3 evaluation built in.** Each parameter is tagged
   with a tier indicating whether it is a universal design check, a directional
   guideline, or an exploratory descriptor.

## The eleven parameters

| # | Parameter | Unit | Family |
|---|---|---|---|
| 1 | LAeq | dBFS-A | Level |
| 2 | Dynamic range | dB | Level |
| 3 | Crest factor | dB | Level |
| 4 | Attack time (mean, median, SD) | ms | Temporal envelope |
| 5 | Tempo | BPM | Temporal envelope |
| 6 | Modulation peak | Hz | Temporal envelope |
| 7 | Spectral centroid | Hz | Spectral shape |
| 8 | Spectral slope β | — | Spectral shape |
| 9 | HNR | dB | Tonal |
| 10 | Spectral flatness | [0, 1] | Tonal |
| 11 | Roughness, sharpness | asper, acum | Psychoacoustic |

## Install

```bash
pip install debussy-audio
```

To install from source:

```bash
git clone https://github.com/jjjooong/debussy.git
cd debussy
pip install -e .
```

Optional extras: `pip install debussy-audio[plot]` for matplotlib plots,
`debussy-audio[test]` for the test suite, `debussy-audio[demo]` for the
Gradio web UI.

## Quickstart

```python
from debussy import analyze_audio

result = analyze_audio("stimulus.wav")
print(result)
# Result(file='stimulus.wav', duration_s=45.06, sample_rate=44100,
#        laeq_dbfs_a=-17.89, dynamic_range_db=8.1, crest_factor_db=10.93,
#        attack_mean_ms=101.59, attack_median_ms=56.11, attack_sd_ms=124.35,
#        roughness_asper=0.07, tempo_bpm=132.5, modulation_peak_hz=1.154,
#        spectral_centroid_hz=3070.1, sharpness_acum=1.521,
#        spectral_slope_beta=-5.368, hnr_db=2.12, spectral_flatness=0.0011, ...)

# Tier framework
from debussy import tier1_compliance, format_compliance
print(format_compliance(result))
```

## Validation

DEBUSSY has been validated on a **60-track open-dataset + clinical benchmark**:

- **A2 (DEAM low-arousal)** *n*=10
- **B1 (DEAM mid-to-high arousal)** *n*=15
- **B2 (FMA medium)** *n*=15 (genre-stratified)
- **C1 (BELL-001 SleepThera)** *n*=20 (breath-paced biofeedback stimuli)

All sixty tracks produce eleven non-null parameters within physiologically
plausible ranges. See `paper/` for the JOSS methods paper, including
distribution figures and effect-size analysis.

Validation data and scripts are released alongside the paper for full
reproducibility.

## Citation

If you use DEBUSSY in your research, please cite:

```bibtex
@article{Kim2026,
  title   = {DEBUSSY: A Python toolbox for 11-parameter acoustic reporting of audio stimuli used in autonomic-arousal research},
  author  = {Kim, Hyeon-Joong and others},
  year    = {2026},
  journal = {Journal of Open Source Software},
  note    = {Manuscript in preparation}
}
```

## Architecture

```
debussy/
├── level          (LAeq, dynamic range, crest factor)
├── envelope       (attack time, tempo, modulation peak)
├── spectral       (centroid, slope β)
├── tonal          (HNR, spectral flatness)
├── psychoacoustic (roughness asper, sharpness acum via MOSQITO)
└── _core          (single-call analyze_audio orchestrator + Result dataclass)
```

The Gradio interface at <https://huggingface.co/spaces/jjjooong/debussy> is a
demo UI built on top of the library; it is not the primary deliverable. The
library is the artefact intended for citation and reuse.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, feature requests, and
pull requests welcome.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgements

DEBUSSY builds directly on [librosa](https://librosa.org/) and
[MOSQITO](https://mosqito.readthedocs.io/). We are grateful to both communities.

