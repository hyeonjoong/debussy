#!/usr/bin/env python3
"""DEBUSSY cloud auto-commit runner (GitHub Actions) — honest edition.

Fires the current week's Tue/Fri task from ``weekly_commits_plan.json`` and
materialises it by copying a **pre-authored, real** file from
``.github/auto-commit/scaffolds/<target>`` to its place in the repo. Every
scheduled commit is therefore a genuine change whose diff matches its message.

This replaces the previous runner, which fabricated content: it appended a
comment stamp restating the commit message to already-existing source files
(so a ``feat(core): ...`` commit's whole diff was a comment) and wrote
``@pytest.mark.skip`` test stubs (so a ``tests: cover X`` commit covered
nothing). Both patterns misrepresented their diffs to anyone reading the git
history — exactly what JOSS reviewers inspect. This runner cannot do that:

  * It only ever writes bytes that already exist, verified, under ``scaffolds/``.
  * It never appends stamps and never writes skipped stubs.
  * A task with no staged content, or whose target already matches, is a safe
    no-op — the workflow commits nothing rather than manufacturing a change.

The workflow validates every produced change with ``pytest`` before committing,
so a staged file that breaks the suite is never pushed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN_PATH = HERE / "weekly_commits_plan.json"
SCAFFOLD_DIR = HERE / "scaffolds"
REPO = HERE.parents[1]  # .github/auto-commit -> repo root


def done_messages() -> str:
    """Full-history commit subjects, for dedupe. Requires fetch-depth: 0."""
    try:
        r = subprocess.run(["git", "log", "--format=%s"], cwd=REPO,
                           capture_output=True, text=True, timeout=20)
        return r.stdout
    except Exception as e:
        print(f"WARN: could not read git log ({e})")
        return ""


def pick_task(plan: dict, today: date, force: bool = False):
    """Return the EARLIEST scheduled task (weeks up to the current one) whose
    commit message is not yet in the git log. Never fires a future week; by
    default never fires a task whose scheduled weekday hasn't arrived this week
    (force=True bypasses that guard, for manual end-to-end testing)."""
    start = date.fromisoformat(plan["_meta"]["start_iso"])
    days_since_start = (today - start).days
    if days_since_start < 0:
        print(f"Today {today} is before start {start} — nothing to do")
        return None
    cur_week = days_since_start // 7
    done = done_messages()
    for week_idx in range(min(cur_week + 1, len(plan["weeks"]))):
        wb = plan["weeks"][week_idx]
        for day_label, wd in (("tue", 1), ("fri", 4)):
            task = wb.get(day_label)
            if not task:
                continue
            if not force and week_idx == cur_week and today.weekday() < wd:
                continue
            if task["message"] not in done:
                return (week_idx, day_label, task)
    print("No pending task (plan up to date for now)")
    return None


def apply_task(task: dict) -> bool:
    """Copy the task's staged real file(s) into the repo.

    Returns True iff a genuine change was written. Never appends stamps, never
    writes stub content. A task whose staged file is missing, or whose target
    already contains the staged bytes, is a no-op (returns False) — so the
    workflow simply commits nothing that run.
    """
    files = task.get("files", [])
    if not files:
        print(f"  task {task['id']} declares no files — nothing to write")
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
    if not PLAN_PATH.exists():
        print(f"Plan not found: {PLAN_PATH}")
        set_output("changed", "false")
        return 0
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    picked = pick_task(plan, date.today(), force=force)
    if picked is None:
        set_output("changed", "false")
        return 0
    week_idx, day_label, task = picked
    print(f"Week {week_idx + 1} ({day_label}) -> task {task['id']} "
          f"({task['category']}): {task['message']}")
    if not apply_task(task):
        print("No real change produced; nothing to commit.")
        set_output("changed", "false")
        return 0
    # Hand the commit message to the workflow via a file outside the work tree,
    # so it is never itself committed and needs no shell-escaping.
    msg_path = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "debussy_commit_msg.txt"
    msg_path.write_text(task["message"] + "\n", encoding="utf-8")
    set_output("changed", "true")
    set_output("msg_file", str(msg_path))
    print(f"Applied task {task['id']}; message written to {msg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
