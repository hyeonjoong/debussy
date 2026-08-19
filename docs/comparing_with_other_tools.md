# Comparing DEBUSSY with other tools

DEBUSSY is not a replacement for general-purpose audio libraries — it *composes*
them into a single, opinionated report tuned for autonomic-arousal stimulus
preparation. It leans on `librosa` for onset/tempo/spectral features and on
`mosqito` for the psychoacoustic metrics, then adds the three-tier compliance
framework and length-aware coverage descriptors on top.

| Capability | DEBUSSY | librosa | mosqito | essentia | spafe |
|---|---|---|---|---|---|
| A-weighted LAeq (dBFS-A) | ✅ | ✗ | ✗ | partial | ✗ |
| Onset attack-time distribution | ✅ | building blocks | ✗ | partial | ✗ |
| Roughness / sharpness (Zwicker/DIN) | ✅ (via mosqito) | ✗ | ✅ | partial | ✗ |
| Spectral centroid / flatness / slope | ✅ | ✅ | ✗ | ✅ | ✅ |
| HNR | ✅ | ✗ | ✗ | partial | ✗ |
| One report of the 12 arousal parameters | ✅ | ✗ | ✗ | ✗ | ✗ |
| Tier-1/2/3 evidence grading | ✅ | ✗ | ✗ | ✗ | ✗ |
| Temporal coverage (% of clip over threshold) | ✅ | ✗ | ✗ | ✗ | ✗ |

**When to use each**

- **librosa / essentia / spafe** — you want raw MIR features and full control
  over framing, or features DEBUSSY does not report.
- **mosqito** — you need the psychoacoustic metrics on their own, or other Sottek
  /Zwicker quantities DEBUSSY does not surface.
- **DEBUSSY** — you want the specific eleven-item arousal report, the
  pass/fail/guidance tiers, and coverage descriptors in one call, reproducible
  across a stimulus set.

DEBUSSY's psychoacoustic values are exactly mosqito's (it wraps them), so results
are consistent with a direct mosqito run at 48 kHz.
