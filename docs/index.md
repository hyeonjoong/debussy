# DEBUSSY

**DEBUSSY** implements the **eleven-item minimum acoustic reporting guideline**
for autonomic-arousal stimuli — nine items measured from the audio in a single
call, plus two recorded alongside them — in output formats designed for
reproducible psychophysiology research.

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

1. **One call, one schema** — `analyze_audio()` returns a typed `Result`
   dataclass ready to become a manuscript table row.
2. **Standardised internals** — window lengths, A-weighting coefficients and the
   spectral-slope band are fixed and documented; deviating requires an explicit
   override, which leaves a record at the call site.
3. **Tiered evaluation built in** — each parameter is tagged Tier 1 (fixed
   design constraint), Tier 2 (directional, optimum set per listener) or Tier 3
   (exploratory), which separates *"is this stimulus admissible?"* from *"what
   does it do?"*. DEBUSSY screens against the *reference values* the companion
   review reports, which it labels exemplars rather than validated cut-offs.

## The eleven reporting items

Table 2 of the companion review — the minimum set proposed for the field.
Nine are measured from the audio; lyrics presence and delivery method are
recorded by the caller, since no analyser can determine them.

| # | Item | Unit | Family |
|---|---|---|---|
| 1 | LAeq + dynamic range | dBFS-A, dB | [Level](api/level.md) |
| 2 | Attack time distribution | ms | [Envelope](api/envelope.md) |
| 3 | Roughness | asper | [Psychoacoustic](api/psychoacoustic.md) |
| 4 | Tempo / modulation rate | BPM, Hz | [Envelope](api/envelope.md) |
| 5 | Spectral centroid | Hz | [Spectral](api/spectral.md) |
| 6 | Sharpness | acum | [Psychoacoustic](api/psychoacoustic.md) |
| 7 | Spectral slope β | — | [Spectral](api/spectral.md) |
| 8 | Harmonicity / HNR | dB | [Tonal](api/tonal.md) |
| 9 | Lyrics presence | yes/no | *caller-supplied* |
| 10 | Delivery method | categorical | *caller-supplied* |
| 11 | Spectral flatness | [0, 1] | [Tonal](api/tonal.md) |

`Result` also carries crest factor and temporal-coverage descriptors as
diagnostics beyond the guideline. Per-family detail is in the
[API overview](api/index.md); thresholds and tier grading are in
[Reference ranges](reference_ranges.md).

!!! note "Eleven items, twelve parameters — not the same list"
    The companion review *evaluates* **twelve** acoustic parameters (its
    Table 1) and separately *proposes* this **eleven-item** reporting guideline
    (its Table 2). DEBUSSY implements the reporting guideline.

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
