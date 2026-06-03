#!/usr/bin/env python3
"""
Stop hook — persists session state after each Claude Code response.
Tracks files edited during the session.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import load_session, save_session


def main():
    state = load_session()

    # Claude Code passes tool use data via stdin in some hook configurations
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except Exception:
        input_data = {}

    # Track files edited from tool use data
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name in ("Edit", "Write", "MultiEdit"):
        file_path = tool_input.get("file_path") or tool_input.get("path")
        if file_path:
            edited_files = state.get("files_edited", [])
            if file_path not in edited_files:
                edited_files.append(file_path)
            state["files_edited"] = edited_files

    save_session(state)


if __name__ == "__main__":
    main()
