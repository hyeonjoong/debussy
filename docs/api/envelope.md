# Envelope

**Reporting item 2 — attack time distribution** and **item 4 — tempo /
modulation rate.**

```python
from debussy.envelope import attack_times_ms, tempo_bpm, modulation_peak_hz
```

## `attack_times_ms(y, fs, librosa) -> dict`

Per-onset attack time: onsets from `librosa.onset.onset_detect` with
backtracking, then for each onset the **10 %–90 % rise time** of the Hilbert
envelope (smoothed over 5 ms) up to the next onset.

Returns `n_onsets`, `mean_ms`, `median_ms`, `sd_ms`, `frac_below_50ms` and
`n_below_50ms`. With fewer than two onsets the statistics are `None` — an
honest "undefined", not zero.

The companion review's Tier-1 onset-dynamics check uses the **median**
(> 50 ms). The share and count of sub-50 ms onsets are reported alongside but
only ever downgrade a pass to `CAUTION`, never fail outright: envelope rise time
ignores absolute level, so it is a descriptor of onset shape rather than a
validated startle metric, and a couple of incidental transients should not
condemn a long quiet piece.

## `tempo_bpm(y, fs, librosa) -> float | None`

`librosa.feature.tempo`. Returns `None` rather than raising when beat tracking
fails — a pure tone or an unmodulated drone has no meaningful tempo.

## `modulation_peak_hz(y, fs) -> float | None`

Dominant amplitude-modulation rate in the **0.5–20 Hz** band: the Hilbert
envelope is resampled to ~200 Hz, mean-removed, and the largest peak of its
magnitude spectrum within the band is returned. `None` if the signal is shorter
than one second of envelope.

This is the band where modulation interacts with respiratory and cardiac
rhythms, which is why the guideline pairs it with tempo — a breath-paced
stimulus may have no beat at all but a clear 0.1–0.3 Hz envelope cycle.
