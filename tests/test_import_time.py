"""Import-time overhead.

Heavy dependencies (librosa, mosqito) are imported lazily inside the functions
that use them, so a bare ``import debussy`` should stay light and must not pull
them into sys.modules. Run in a subprocess for a cold, isolated measurement.
"""
from __future__ import annotations

import subprocess
import sys


def test_import_time_under_2s():
    code = (
        "import time\n"
        "t = time.perf_counter()\n"
        "import debussy\n"
        "print(time.perf_counter() - t)\n"
    )
    out = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert float(out.stdout.strip()) < 2.0, f"import took {out.stdout.strip()}s"


def test_heavy_deps_are_lazy():
    code = (
        "import sys, debussy\n"
        "assert 'librosa' not in sys.modules, 'librosa imported eagerly'\n"
        "assert 'mosqito' not in sys.modules, 'mosqito imported eagerly'\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
