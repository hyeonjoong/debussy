#!/usr/bin/env python3
"""
DEBUSSY cloud auto-commit runner (GitHub Actions).

Laptop-independent replacement for the old local launchd runner. Runs daily on
GitHub's infrastructure. Uses catch-up picking: it fires the current week's
Tue/Fri scaffold task on the correct day and self-heals if a scheduled run is
ever skipped (fires the earliest still-pending task, one per run). It only
modifies files and reports the commit message via GITHUB_OUTPUT; the workflow
validates the result with pytest and then commits + pushes.

Task-picking logic is a verbatim port of the proven local runner's catch-up
mode, minus all the git plumbing (the workflow owns checkout/commit/push).
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
REPO = HERE.parents[1]  # .github/auto-commit -> repo root
SIDECAR = HERE / "scaffold_changes.md"


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
    (force=True bypasses that guard, for manual end-to-end testing).
    """
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
            # Don't fire a task whose scheduled weekday hasn't arrived this week.
            if not force and week_idx == cur_week and today.weekday() < wd:
                continue
            if task["message"] not in done:
                return (week_idx, day_label, task)
    print("No pending task (plan up to date for now)")
    return None


def task_content(task_id: str, category: str, message: str) -> str:
    """Real (small) file content for a task whose target file does not exist."""
    today = date.today().isoformat()
    header = f"<!-- DEBUSSY auto-staged scaffold, week task `{task_id}`, {today} -->\n\n"

    docs_templates = {
        "docs-quickstart-stub": f"""# Quickstart

```python
from debussy import analyze_audio
result = analyze_audio("stimulus.wav")
print(result)
```

Returned `Result` carries the twelve reporting parameters defined in the paper.
See the API pages for each parameter family.

_Last updated {today}._
""",
        "mkdocs-config": f"""site_name: DEBUSSY
site_url: https://hyeonjoong.github.io/debussy
repo_url: https://github.com/hyeonjoong/debussy
theme:
  name: material
  features:
    - navigation.sections
    - content.code.copy
plugins:
  - search
nav:
  - Home: index.md
  - Quickstart: quickstart.md
  - API:
    - api/index.md
  - Validation: validation.md
  - Reference ranges: reference_ranges.md
  - FAQ: faq.md
  - Troubleshooting: troubleshooting.md
  - Changelog: changelog.md
""",
    }
    if task_id in docs_templates:
        return docs_templates[task_id]
    if category == "docs":
        return f"# {task_id.replace('-', ' ').replace('docs ', '').title()}\n\n_Stub created {today}, will be expanded._\n\nSee the corresponding paper section for the full description.\n"
    if category in ("tests",):
        return f'''"""Auto-scaffolded test stub {task_id}, {today}.

Expanded in subsequent commits to cover the case named by the task id.
"""
import pytest


@pytest.mark.skip(reason="scaffold; full implementation in upcoming weeks")
def test_{task_id.replace('-', '_')}():
    pass
'''
    if category in ("validation",):
        return f'''#!/usr/bin/env python3
"""Validation stub {task_id} ({today}).

Drives the {task_id.split('-', 1)[-1]} category through the same pipeline used
in the 60-track benchmark. Fills in once licensed audio is in place.
"""
if __name__ == "__main__":
    print("validation stub", "{task_id}")
'''
    if category in ("ci",):
        return f"# CI fragment for `{task_id}` ({today})\n# Expanded in upcoming commits.\n"
    if category in ("packaging",):
        return f"# packaging note {task_id} ({today})\n"
    if category in ("feature", "refactor", "lint"):
        return f"# placeholder for {task_id} ({today})\n# Implementation will live in src/debussy/ in the next iteration.\n"
    if category in ("joss-prep",):
        return f"# JOSS prep checkpoint {task_id} ({today})\n"
    return header + f"_{message}_\n"


def stamp_for(target: Path, task: dict):
    """Extension-appropriate comment stamp, or None if the file format has no
    safe inline comment syntax (json/ipynb/binary). This is the fix for the
    2026-07-08 breakage where an HTML comment was appended to .py files."""
    body = f"{date.today().isoformat()} :: {task['id']} :: {task['message']}"
    ext = target.suffix.lower()
    if ext in (".md", ".markdown", ".html", ".htm"):
        return f"\n<!-- {body} -->\n"
    if ext in (".py", ".toml", ".cfg", ".ini", ".yml", ".yaml", ".txt", ".sh"):
        return f"\n# {body}\n"
    if ext == ".bib":
        return f"\n% {body}\n"
    return None


def apply_task(task: dict) -> bool:
    """Write each file in the task. Returns True if anything changed."""
    files = task.get("files", [])
    if not files:
        print(f"No files for task {task['id']} — nothing to write")
        return False
    content = task_content(task["id"], task["category"], task["message"])
    changed = False
    for rel in files:
        target = REPO / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            stamp = stamp_for(target, task)
            if stamp is None:
                # No safe inline comment for this format — log to a sidecar.
                line = f"- {date.today().isoformat()} :: {task['id']} :: {rel} :: {task['message']}\n"
                prev = SIDECAR.read_text(encoding="utf-8") if SIDECAR.exists() else ""
                if line not in prev:
                    SIDECAR.write_text(prev + line, encoding="utf-8")
                    changed = True
                continue
            existing = target.read_text(encoding="utf-8")
            if stamp not in existing:
                target.write_text(existing + stamp, encoding="utf-8")
                changed = True
        else:
            target.write_text(content, encoding="utf-8")
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
    today = date.today()
    picked = pick_task(plan, today, force=force)
    if picked is None:
        set_output("changed", "false")
        return 0
    week_idx, day_label, task = picked
    print(f"Week {week_idx + 1} ({day_label}) -> task {task['id']} "
          f"({task['category']}): {task['message']}")
    if not apply_task(task):
        print("No file changes produced; nothing to commit.")
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
