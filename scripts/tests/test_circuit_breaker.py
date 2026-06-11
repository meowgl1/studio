#!/usr/bin/env python3
"""
End-to-end test for circuit-breaker.py rollback path.

Setup:
  1. Git repo in /tmp/cb_test/
  2. dummy.py committed with clean content
  3. dummy.py modified ("dirty" edit)
  4. Session state file created with files_edited pointing to dummy.py
  5. Circuit breaker invoked twice with failing pytest output
  6. After second invocation: verify dummy.py reverted to clean content
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

HOOK = Path.home() / ".studio" / "scripts" / "hooks" / "circuit-breaker.py"
SESSIONS_DIR = Path.home() / ".studio" / ".sessions"

CLEAN_CONTENT = 'def greet(name: str) -> str:\n    return f"Hello {name}"\n'
DIRTY_CONTENT = 'def greet(name: str) -> str:\n    return f"Hello {name} [DIRTY EDIT]"\n'

FAILING_OUTPUT = "FAILED tests/test_dummy.py::test_greet - AssertionError: assert 'Hello world' == 'Hello world [DIRTY EDIT]'"


def run_hook(command: str, output: str, session_id: str) -> tuple[int, str]:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": output,
    })
    env = os.environ.copy()
    env["CLAUDE_SESSION_ID"] = session_id
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stderr.strip()


def setup_repo() -> tuple[Path, str]:
    """Create temp git repo, commit clean dummy.py, then write dirty version."""
    repo = Path(tempfile.mkdtemp(prefix="cb_test_"))

    subprocess.run(["git", "init", str(repo)], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, cwd=repo)
    subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, cwd=repo)

    dummy = repo / "dummy.py"
    dummy.write_text(CLEAN_CONTENT)
    subprocess.run(["git", "add", "dummy.py"], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, capture_output=True)

    # Dirty edit (simulate what Claude wrote)
    dummy.write_text(DIRTY_CONTENT)

    return repo, str(dummy)


def setup_session(session_id: str, file_path: str) -> Path:
    """Write a fake session state file so the hook finds files_edited."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    session_file = SESSIONS_DIR / f"{session_id}.json"
    state = {
        "session_id": session_id,
        "project": "cb_test",
        "started_at": "2026-06-10T10:00:00",
        "files_edited": [file_path],
        "input_tokens": 0,
        "output_tokens": 0,
    }
    session_file.write_text(json.dumps(state))
    return session_file


def cleanup(repo: Path, session_id: str) -> None:
    shutil.rmtree(repo, ignore_errors=True)
    (SESSIONS_DIR / f"{session_id}.json").unlink(missing_ok=True)
    (SESSIONS_DIR / f"cb_{session_id}.json").unlink(missing_ok=True)


# ─── Test ─────────────────────────────────────────────────────────────────────

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"

def check(label: str, condition: bool, detail: str = "") -> bool:
    icon = PASS if condition else FAIL
    msg = f"  {icon}  {label}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    return condition


def main() -> int:
    SESSION_ID = "cb_e2e_test"
    repo, dummy_path = setup_repo()
    session_file = setup_session(SESSION_ID, dummy_path)
    results = []

    print(f"\nCircuit Breaker — end-to-end test")
    print(f"  repo:    {repo}")
    print(f"  file:    {dummy_path}")
    print()

    try:
        # Precondition: file is dirty
        results.append(check(
            "precondition: dummy.py is dirty",
            Path(dummy_path).read_text() == DIRTY_CONTENT,
        ))

        # ── Attempt 1 ──────────────────────────────────────────────────────────
        code, stderr = run_hook("pytest tests/test_dummy.py", FAILING_OUTPUT, SESSION_ID)
        results.append(check(
            "attempt 1: exit code 0 (warn, no rollback yet)",
            code == 0,
            f"got exit {code} | stderr: {stderr[:120]}",
        ))
        results.append(check(
            "attempt 1: warning message contains '1/2'",
            "1/2" in stderr,
            f"stderr: {stderr[:120]}",
        ))
        results.append(check(
            "attempt 1: file still dirty (no rollback)",
            Path(dummy_path).read_text() == DIRTY_CONTENT,
        ))

        # ── Attempt 2 ──────────────────────────────────────────────────────────
        code, stderr = run_hook("pytest tests/test_dummy.py", FAILING_OUTPUT, SESSION_ID)
        results.append(check(
            "attempt 2: exit code 2 (TRIGGERED)",
            code == 2,
            f"got exit {code} | stderr: {stderr[:120]}",
        ))
        results.append(check(
            "attempt 2: TRIGGERED in stderr",
            "TRIGGERED" in stderr,
            f"stderr: {stderr[:120]}",
        ))
        results.append(check(
            "attempt 2: file rolled back to clean content",
            Path(dummy_path).read_text() == CLEAN_CONTENT,
            f"content: {Path(dummy_path).read_text()[:60]!r}",
        ))

        # Issues log written
        issues_log = Path.home() / ".studio" / "circuit_breaker_issues.log"
        results.append(check(
            "issues log written",
            issues_log.exists() and "CIRCUIT BREAKER TRIGGERED" in issues_log.read_text(),
        ))

        # ── Reset: after rollback, counter cleared ─────────────────────────────
        cb_state_file = SESSIONS_DIR / f"cb_{SESSION_ID}.json"
        if cb_state_file.exists():
            cb_state = json.loads(cb_state_file.read_text())
            results.append(check(
                "counter reset after rollback (file removed from state)",
                dummy_path not in cb_state.get("file_attempts", {}),
            ))

    finally:
        cleanup(repo, SESSION_ID)

    passed = sum(results)
    total = len(results)
    print(f"\n{'─'*40}")
    print(f"  Result: {passed}/{total} passed")
    if passed == total:
        print(f"  {PASS} All checks passed")
    else:
        print(f"  {FAIL} {total - passed} check(s) failed")
    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
