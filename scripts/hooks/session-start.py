#!/usr/bin/env python3
"""
SessionStart hook — detects the active project and loads any prior session state.
Prints a brief context note to stderr.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import (
    get_project_name,
    get_project_root,
    get_project_studio_dir,
    load_session,
    save_session,
    SESSIONS_DIR,
)


def get_recent_sessions(project: str, limit: int = 3) -> list[dict]:
    """Find recent session files for this project."""
    import json

    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            if data.get("project") == project:
                sessions.append(data)
                if len(sessions) >= limit:
                    break
        except Exception:
            continue
    return sessions


def main():
    project = get_project_name()
    project_root = get_project_root()
    studio_dir = get_project_studio_dir()

    # Start a new session state
    state = load_session()
    state["project"] = project
    state["started_at"] = datetime.now().isoformat()
    save_session(state)

    lines = [f"[studio] session start · project: {project}"]

    if project_root:
        lines.append(f"  root: {project_root}")

    if studio_dir:
        context_file = studio_dir / "context.md"
        tasks_file = studio_dir / "tasks.md"
        has_context = context_file.exists()
        has_tasks = tasks_file.exists()
        lines.append(f"  context.md: {'✓' if has_context else '✗ (missing)'}")
        lines.append(f"  tasks.md:   {'✓' if has_tasks else '✗ (missing)'}")

    recent = get_recent_sessions(project)
    if recent:
        last = recent[0]
        last_date = last.get("started_at", "")[:10]
        last_files = len(last.get("files_edited", []))
        lines.append(f"  last session: {last_date} · {last_files} files edited")

    print("\n".join(lines), file=sys.stderr)


if __name__ == "__main__":
    main()
