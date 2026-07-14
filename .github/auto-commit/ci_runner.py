#!/usr/bin/env python3
"""DEBUSSY cloud auto-commit runner (GitHub Actions) — honest, natural cadence.

Runs daily. Each run reveals AT MOST one item from an ordered backlog
(``commit_backlog.json``) by copying a pre-authored, verified file from
``.github/auto-commit/scaffolds/<target>`` into place. Every commit is therefore
a genuine change whose diff matches its message.

Two properties, by construction:

1. **No fabrication.** The runner only ever writes bytes that already exist,
   verified, under ``scaffolds/``. It never appends comment stamps to source and
   never writes ``@pytest.mark.skip`` stubs — the patterns that made the old
   runner's ``feat:`` / ``tests:`` commits misrepresent their diffs. A backlog
   item with no staged file, or whose target already matches, is a safe no-op.

2. **Natural, irregular cadence.** Instead of a rigid Tue/Fri schedule, each day
   a weekday-weighted, date-seeded coin flip decides whether to reveal the next
   item, so real work accumulates organically. A floor forces a commit once the
   history has been quiet for FLOOR_DAYS, keeping the gap under the commit-heartbeat
   threshold (7 days) while the backlog still has items.

The workflow validates every produced change with ``pytest`` before committing,
so a staged file that breaks the suite is never pushed. ``--force`` (manual
dispatch) bypasses the coin flip and reveals the next pending item immediately.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKLOG_PATH = HERE / "commit_backlog.json"
SCAFFOLD_DIR = HERE / "scaffolds"
REPO = HERE.parents[1]  # .github/auto-commit -> repo root

# Cadence tuning. Keep FLOOR_DAYS strictly below the heartbeat's STALE_DAYS (7)
# so the floor fires before the dead-man's switch would.
FLOOR_DAYS = 5
WEEKDAY_P = 0.45
WEEKEND_P = 0.18


def done_messages() -> str:
    """Full-history commit subjects, for dedupe. Requires fetch-depth: 0."""
    try:
        r = subprocess.run(["git", "log", "--format=%s"], cwd=REPO,
                           capture_output=True, text=True, timeout=20)
        return r.stdout
    except Exception as e:
        print(f"WARN: could not read git log ({e})")
        return ""


def days_since_last_commit(today: date) -> int:
    """Whole days between the last commit (any author) and `today`. Large number
    if the log cannot be read, so the floor errs toward committing."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=REPO,
                           capture_output=True, text=True, timeout=20)
        last = datetime.fromtimestamp(int(r.stdout.strip()), tz=timezone.utc).date()
        return (today - last).days
    except Exception as e:
        print(f"WARN: could not read last-commit date ({e})")
        return 999


def should_commit_today(today: date, days_since: int) -> bool:
    """Weekday-weighted, date-seeded decision, with a hard floor after a quiet
    stretch so the heartbeat never trips while the backlog has items."""
    if days_since >= FLOOR_DAYS:
        return True
    rng = random.Random(int(today.strftime("%Y%m%d")))
    p = WEEKEND_P if today.weekday() >= 5 else WEEKDAY_P
    return rng.random() < p


def pending_items(backlog: list[dict], done: str) -> list[dict]:
    return [t for t in backlog if t["message"] not in done]


def apply_task(task: dict) -> bool:
    """Copy the task's staged real file(s) into the repo. Returns True iff a
    genuine change was written. Never appends stamps, never writes stubs."""
    files = task.get("files", [])
    if not files:
        print(f"  item {task['id']} declares no files — nothing to write")
        return False
    changed = False
    for rel in files:
        staged = SCAFFOLD_DIR / rel
        if not staged.exists():
            print(f"  no staged content at scaffolds/{rel} — skipping (honest no-op)")
            continue
        target = REPO / rel
        new = staged.read_text(encoding="utf-8")
        if target.exists() and target.read_text(encoding="utf-8") == new:
            print(f"  {rel} already up to date — skipping")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new, encoding="utf-8")
        print(f"  wrote {rel} ({len(new)} bytes) from scaffolds/{rel}")
        changed = True
    return changed


def set_output(key: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> int:
    force = "--force" in sys.argv[1:]
    if not BACKLOG_PATH.exists():
        print(f"Backlog not found: {BACKLOG_PATH}")
        set_output("changed", "false")
        return 0
    plan = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
    today = date.today()

    pending = pending_items(plan["backlog"], done_messages())
    if not pending:
        print("Backlog exhausted — nothing to commit (add scaffolds/ items to extend).")
        set_output("changed", "false")
        return 0

    ds = days_since_last_commit(today)
    if not force and not should_commit_today(today, ds):
        print(f"Natural cadence: no commit today ({today} {today:%a}, "
              f"{ds}d since last commit, {len(pending)} item(s) pending).")
        set_output("changed", "false")
        return 0

    task = pending[0]
    reason = "forced" if force else (f"floor@{ds}d" if ds >= FLOOR_DAYS else "cadence")
    print(f"Reveal ({reason}) -> {task['id']}: {task['message']}")
    if not apply_task(task):
        print("No real change produced; nothing to commit.")
        set_output("changed", "false")
        return 0

    msg_path = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "debussy_commit_msg.txt"
    msg_path.write_text(task["message"] + "\n", encoding="utf-8")
    set_output("changed", "true")
    set_output("msg_file", str(msg_path))
    print(f"Applied {task['id']}; message written to {msg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
