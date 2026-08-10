# DEBUSSY

**DEBUSSY** computes a fixed set of **twelve acoustic reporting parameters** from
an audio stimulus in a single call, in output formats designed for reproducible
psychophysiology and autonomic-arousal research.

```python
from debussy import analyze_audio

result = analyze_audio("stimulus.wav")
print(result.laeq_dbfs_a, result.roughness_asper, result.sharpness_acum)
```

New here? Start with the [Quickstart](quickstart.md), or install first via the
[Installation guide](installation.md).

## Why DEBUSSY

Characterising auditory stimuli for autonomic-arousal work — sleep, anxiety,
cardiac vagal tone, biofeedback — normally means gluing `librosa` together with
`MOSQITO` and writing several hundred lines of bookkeeping per study. Because
every lab makes slightly different choices (window length, A-weighting timebase,
onset detector, library version), the resulting tables are not comparable across
studies.

DEBUSSY fixes the choices, names them, and returns one schema:

1. **One call, twelve parameters, one schema** — `analyze_audio()` returns a typed
   `Result` dataclass ready to become a manuscript table row.
2. **Standardised internals** — window lengths, A-weighting coefficients and the
   spectral-slope band are fixed and documented; deviating requires an explicit
   override, which leaves a record at the call site.
3. **Tiered evaluation built in** — each parameter is tagged Tier 1 (universal
   design check), Tier 2 (directional guideline) or Tier 3 (exploratory), which
   separates *"is this stimulus admissible?"* from *"what does it do?"*.

## The twelve parameters

| Family | Parameters |
|---|---|
| Level | LAeq (dBFS-A), dynamic range (dB), crest factor (dB) |
| Temporal envelope | attack time mean/median/SD (ms), tempo (BPM), modulation peak (Hz) |
| Spectral shape | spectral centroid (Hz), spectral slope β |
| Tonal | harmonics-to-noise ratio (dB), spectral flatness [0, 1] |
| Psychoacoustic | roughness (asper), sharpness (acum) |

Per-family details live under the API section, starting at
[API overview](api/index.md). Thresholds and how each tier is graded are in
[Reference ranges](reference_ranges.md).

## Where to go next

- [Quickstart](quickstart.md) — first analysis in five lines
- [Command-line interface](cli.md) — batch a folder, write CSV
- [Validation](validation.md) — the 60-track benchmark behind the published figures
- [Comparison with other tools](comparing_with_other_tools.md) — librosa, MOSQITO, Essentia, spafe
- [FAQ](faq.md) and [Troubleshooting](troubleshooting.md)

A no-install demo is available on
[Hugging Face Spaces](https://huggingface.co/spaces/jjjooong/debussy); the
library is the primary deliverable and the artefact intended for citation.

## Licence

MIT. Source at [github.com/hyeonjoong/debussy](https://github.com/hyeonjoong/debussy).
