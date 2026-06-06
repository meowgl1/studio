#!/usr/bin/env python3
"""
PostToolUse hook for Read — tracks files read in session state.
Gateguard checks files_read to decide if an Edit/Write is safe.
Without this hook, files_read is never populated and gateguard blocks all edits.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import load_session, save_session


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except Exception:
        input_data = {}

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")

    if not file_path:
        return

    state = load_session()
    files_read = state.get("files_read", [])
    if file_path not in files_read:
        files_read.append(file_path)
    state["files_read"] = files_read
    save_session(state)


if __name__ == "__main__":
    main()
