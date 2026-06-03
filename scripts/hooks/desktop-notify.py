#!/usr/bin/env python3
"""
Stop hook — sends a macOS desktop notification when Claude finishes a response.
Useful for long-running tasks so you can do other things and come back.
Only fires when the session has been running for > 30 seconds.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import load_session, get_project_name, notify


MIN_SESSION_SECONDS = 30  # don't notify for quick one-shot responses


def main():
    state = load_session()
    started_at = state.get("started_at", "")

    try:
        start = datetime.fromisoformat(started_at)
        elapsed = (datetime.now() - start).total_seconds()
    except Exception:
        elapsed = 0

    if elapsed < MIN_SESSION_SECONDS:
        return  # too short — skip notification

    project = get_project_name()
    files_edited = len(state.get("files_edited", []))
    cost = state.get("estimated_cost_usd", 0)

    if files_edited > 0:
        message = f"{files_edited} file{'s' if files_edited != 1 else ''} edited · ~${cost:.3f}"
    else:
        message = "Response ready"

    notify(title=f"Claude · {project}", message=message)


if __name__ == "__main__":
    main()
