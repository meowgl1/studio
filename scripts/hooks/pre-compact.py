#!/usr/bin/env python3
"""
PreCompact hook — saves session state before Claude Code compacts the context.
Prevents losing track of what was done in long sessions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import load_session, save_session, get_project_name
from datetime import datetime


def main():
    state = load_session()
    state["last_compact"] = datetime.now().isoformat()
    state["compact_count"] = state.get("compact_count", 0) + 1
    save_session(state)

    project = get_project_name()
    compact_count = state["compact_count"]
    files_count = len(state.get("files_edited", []))

    # Output to stderr so it appears in Claude's context as a note
    print(
        f"[studio] pre-compact: saved state for '{project}' "
        f"(compact #{compact_count}, {files_count} files edited this session)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
