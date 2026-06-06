"""
Shared utilities for studio hook scripts and dashboard.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


# ─── Paths ────────────────────────────────────────────────────────────────────

STUDIO_DIR = Path.home() / ".studio"
SESSIONS_DIR = STUDIO_DIR / ".sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


# ─── Project detection ────────────────────────────────────────────────────────

def get_project_root() -> Path | None:
    """Walk up from cwd to find nearest .studio/ directory."""
    cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
    for parent in [cwd, *cwd.parents]:
        if (parent / ".studio").exists():
            return parent
    return None


def get_project_studio_dir() -> Path | None:
    root = get_project_root()
    return (root / ".studio") if root else None


def get_project_name() -> str:
    root = get_project_root()
    if root:
        return root.name
    return Path(os.environ.get("CLAUDE_CWD", os.getcwd())).name


# ─── Session state ────────────────────────────────────────────────────────────

def get_session_id() -> str:
    """Get current session ID from Claude Code environment."""
    return os.environ.get("CLAUDE_SESSION_ID", "unknown")


def get_session_file() -> Path:
    session_id = get_session_id()
    return SESSIONS_DIR / f"{session_id}.json"


def load_session() -> dict:
    session_file = get_session_file()
    if session_file.exists():
        return json.loads(session_file.read_text())
    return {
        "session_id": get_session_id(),
        "project": get_project_name(),
        "started_at": datetime.now().isoformat(),
        "files_edited": [],
        "decisions": [],
        "input_tokens": 0,
        "output_tokens": 0,
    }


def save_session(state: dict) -> None:
    session_file = get_session_file()
    state["updated_at"] = datetime.now().isoformat()
    session_file.write_text(json.dumps(state, indent=2))


# ─── Token / context tracking ─────────────────────────────────────────────────

# Context window for claude-sonnet-4-6
CONTEXT_WINDOW = 200_000


def context_utilization(input_tokens: int) -> float:
    """Return context window utilization as a percentage (0–100)."""
    return round((input_tokens / CONTEXT_WINDOW) * 100, 1)


# ─── Changelog helpers ────────────────────────────────────────────────────────

def get_changelog_dir() -> Path | None:
    studio_dir = get_project_studio_dir()
    if studio_dir:
        return studio_dir / "changelog"
    return STUDIO_DIR / ".sessions" / "global-changelog"


def append_to_changelog(entry: str) -> None:
    changelog_dir = get_changelog_dir()
    if changelog_dir is None:
        return
    changelog_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = changelog_dir / f"{today}.md"
    separator = "\n\n---\n\n" if log_file.exists() else ""
    with log_file.open("a") as f:
        f.write(separator + entry)


# ─── macOS notifications ──────────────────────────────────────────────────────

def notify(title: str, message: str, subtitle: str = "") -> None:
    """Send macOS notification via osascript."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        if subtitle:
            script += f' subtitle "{subtitle}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass  # notifications are non-critical


# ─── File type detection ─────────────────────────────────────────────────────

def detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".sql": "sql",
    }
    return mapping.get(ext)
