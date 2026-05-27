"""Temporal-envelope descriptors on a click train of known tempo."""
from debussy import analyze_audio


def test_tempo_click_train_120bpm(click_train):
    """A 120-BPM click train should resolve to a tempo close to 120 (with octave tolerance)."""
    r = analyze_audio(click_train)
    assert r.tempo_bpm is not None
    # librosa beat tracker may report half/double the true tempo for very regular impulse trains
    plausible_set = {60.0, 120.0, 240.0}
    closest = min(plausible_set, key=lambda t: abs(t - r.tempo_bpm))
    assert abs(closest - r.tempo_bpm) < 10.0, (
        f"Tempo {r.tempo_bpm} not close to any of 60/120/240"
    )


def test_attack_times_finite(click_train):
    """A click train has very sharp onsets; attack-time median should be a finite small number."""
    r = analyze_audio(click_train)
    assert r.attack_median_ms is not None
    assert 0 < r.attack_median_ms < 200
