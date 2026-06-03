#!/usr/bin/env python3
"""
PostToolUse hook — runs linting/type-checking after file edits.
Language is auto-detected from file extension.
Non-blocking: warns but does not fail the response.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

from lib.studio import detect_language


def run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=25,
            cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except FileNotFoundError:
        return 0, ""  # tool not installed — skip silently


def check_python(file_path: str) -> list[str]:
    issues = []
    cwd = str(Path(file_path).parent)

    code, out = run(["ruff", "check", "--select=E,W,F", file_path])
    if code != 0 and out:
        issues.append(f"ruff: {out}")

    return issues


def check_typescript(file_path: str) -> list[str]:
    issues = []
    project_root = find_project_root(file_path, "tsconfig.json")

    if project_root:
        code, out = run(["npx", "tsc", "--noEmit", "--pretty", "false"], cwd=project_root)
        if code != 0 and out:
            # Filter to only lines relevant to the edited file
            rel = Path(file_path).relative_to(project_root) if Path(file_path).is_absolute() else Path(file_path)
            relevant = [l for l in out.splitlines() if str(rel) in l or "error TS" in l]
            if relevant:
                issues.append("tsc: " + "\n".join(relevant[:5]))

    return issues


def find_project_root(file_path: str, marker: str) -> str | None:
    path = Path(file_path).resolve()
    for parent in [path.parent, *path.parent.parents]:
        if (parent / marker).exists():
            return str(parent)
    return None


def main():
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except Exception:
        input_data = {}

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    if not file_path or not Path(file_path).exists():
        return

    lang = detect_language(file_path)
    if lang is None:
        return

    issues = []
    if lang == "python":
        issues = check_python(file_path)
    elif lang == "typescript":
        issues = check_typescript(file_path)

    if issues:
        print(f"[quality-gate] {Path(file_path).name}", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
    else:
        print(f"[quality-gate] ✓ {Path(file_path).name}", file=sys.stderr)


if __name__ == "__main__":
    main()
