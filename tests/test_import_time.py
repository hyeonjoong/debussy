"""Import-time overhead.

Heavy dependencies (librosa, mosqito, matplotlib) are imported lazily inside the
functions that use them, so a bare ``import debussy`` should stay light and must
not pull them into ``sys.modules``. Each check runs in a subprocess for a cold,
isolated measurement.

The cost of ``import debussy`` is dominated by the modules it genuinely needs at
module scope — numpy, scipy.signal, soundfile. So rather than asserting an
absolute wall-clock bound, which is meaningless on a shared CI runner whose
speed varies run to run, the budget is expressed *relative* to importing that
mandatory core. That ratio is a property of the code, not of the machine.
"""
from __future__ import annotations

import subprocess
import sys

# What `import debussy` unavoidably pulls in at module scope.
CORE_IMPORTS = "import numpy, scipy.signal, soundfile"

# DEBUSSY's own module-scope work should be a rounding error next to its core
# dependencies. 2x leaves generous headroom for runner noise while still failing
# loudly if something heavy starts being imported eagerly.
MAX_RATIO = 2.0

# Absolute ceiling, deliberately loose: catches a pathological regression (an
# eager librosa import costs many seconds) without flaking on a slow runner.
ABSOLUTE_CEILING_S = 20.0

_TIMER = """
import time
t = time.perf_counter()
{stmt}
print(time.perf_counter() - t)
"""


def _time_import(stmt: str) -> float:
    out = subprocess.run([sys.executable, "-c", _TIMER.format(stmt=stmt)],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    return float(out.stdout.strip())


def test_import_is_cheap_relative_to_its_core_dependencies():
    core = _time_import(CORE_IMPORTS)
    full = _time_import("import debussy")
    # Guard against a near-zero denominator on a warm filesystem cache.
    ratio = full / max(core, 1e-3)
    assert ratio < MAX_RATIO, (
        f"import debussy took {full:.2f}s versus {core:.2f}s for "
        f"{CORE_IMPORTS} alone (ratio {ratio:.1f}x, budget {MAX_RATIO}x) — "
        f"something heavy is likely being imported at module scope"
    )


def test_import_time_has_not_exploded():
    full = _time_import("import debussy")
    assert full < ABSOLUTE_CEILING_S, f"import took {full:.2f}s"


def test_heavy_deps_are_lazy():
    """The deterministic version of the check above — no timing involved.

    matplotlib is a *required* dependency (mosqito imports it internally without
    declaring it), but it must still not be imported until a plotting or
    psychoacoustic call actually needs it.
    """
    code = (
        "import sys, debussy\n"
        "for mod in ('librosa', 'mosqito', 'matplotlib'):\n"
        "    assert mod not in sys.modules, f'{mod} imported eagerly'\n"
        "print('ok')\n"
    )
    out = subprocess.run([sys.executable, "-c", code],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
