"""write_csv round-trip.

The CSV header must be exactly the Result fields (in order), with one data row
per analysed file whose values match the Result. Repeated calls append rather
than rewrite the header, and refuse to append to a CSV whose header is not the
current Result schema.
"""
from __future__ import annotations

import csv
from dataclasses import fields

import numpy as np
import soundfile as sf
import pytest

from debussy import analyze_audio, write_csv, Result


@pytest.fixture
def two_results(tmp_path):
    fs = 48000
    results = []
    for i in range(2):
        t = np.arange(int(fs * 2.5)) / fs
        y = 0.4 * np.sin(2 * np.pi * (220 + 90 * i) * t)
        p = tmp_path / f"s{i}.wav"
        sf.write(p, y.astype(np.float32), fs, subtype="PCM_16")
        results.append(analyze_audio(str(p)))
    return results


def test_csv_header_is_result_fields(two_results, tmp_path):
    out = tmp_path / "r.csv"
    write_csv(two_results, str(out))
    with open(out, newline="") as fh:
        header = next(csv.reader(fh))
    assert header == [f.name for f in fields(Result)]


def test_csv_has_one_row_per_result(two_results, tmp_path):
    out = tmp_path / "r.csv"
    write_csv(two_results, str(out))
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(two_results)
    assert rows[0]["file"] == two_results[0].file
    assert float(rows[0]["laeq_dbfs_a"]) == two_results[0].laeq_dbfs_a


def test_csv_append_accumulates(two_results, tmp_path):
    out = tmp_path / "r.csv"
    write_csv(two_results[:1], str(out))   # creates file + header + 1 row
    write_csv(two_results[1:], str(out))   # appends 1 row, no new header
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2


def test_csv_append_refuses_a_different_header(two_results, tmp_path):
    # A report started before 0.4.0 lacks the fields Result gained since.
    # Appending to it used to write the new rows under the old header, so
    # every column after the first missing field held the wrong value.
    old = [f.name for f in fields(Result) if f.name != "beat_agreement"]
    out = tmp_path / "old.csv"
    out.write_text(",".join(old) + "\n", encoding="utf-8")
    before = out.read_bytes()
    with pytest.raises(ValueError, match="beat_agreement"):
        write_csv(two_results, str(out))
    assert out.read_bytes() == before


def test_csv_empty_existing_file_gets_a_header(two_results, tmp_path):
    out = tmp_path / "empty.csv"
    out.touch()
    write_csv(two_results, str(out))
    with open(out, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(two_results)
    assert rows[0]["file"] == two_results[0].file
