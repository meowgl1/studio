#!/usr/bin/env python3
"""
PreToolUse hook — before first Edit/Write on a file, checks if it was read first.
Prevents blind edits on files Claude hasn't seen.
Tracks read files in session state.

Exit code 2 = block the tool call with a message.
Exit code 0 = allow.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import load_session, save_session


# Files that are always safe to create without reading (new files)
SKIP_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".env.example"}


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except Exception:
        input_data = {}

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    path = Path(file_path)

    # Allow creating new files — they don't exist yet
    if not path.exists():
        sys.exit(0)

    # Allow non-code files
    if path.suffix.lower() in SKIP_EXTENSIONS:
        sys.exit(0)

    state = load_session()
    files_read = set(state.get("files_read", []))
    files_edited = set(state.get("files_edited", []))

    # Already edited this session — already read before
    if file_path in files_edited:
        sys.exit(0)

    # File was read this session
    if file_path in files_read:
        sys.exit(0)

    # File exists but hasn't been read — warn and block
    print(
        f"[gateguard] Read {path.name} before editing — use the Read tool first.\n"
        f"  Path: {file_path}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
