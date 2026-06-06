#!/usr/bin/env python3
"""
Studio Activation Script — manages tool-specific configuration on behalf of the studio.

The studio (~/.studio/) is the source of truth.
This script applies studio config to the active AI tool — you never touch tool configs manually.

Usage:
  python3 ~/.studio/scripts/activate.py            # activate hooks in Claude Code
  python3 ~/.studio/scripts/activate.py --status   # show what's active
  python3 ~/.studio/scripts/activate.py --off       # remove studio hooks from Claude Code
  python3 ~/.studio/scripts/activate.py --dry-run  # preview changes without writing

Future:
  python3 ~/.studio/scripts/activate.py --tool=cursor
  python3 ~/.studio/scripts/activate.py --tool=codex
"""

import argparse
import json
import sys
from pathlib import Path

STUDIO_DIR = Path.home() / ".studio"
HOOKS_SOURCE = STUDIO_DIR / "hooks" / "hooks.json"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"

STUDIO_HOOKS_MARKER = "__studio_hooks__"


# ─── Claude Code adapter ──────────────────────────────────────────────────────

def build_claude_hooks() -> dict:
    """Read hooks.json and return Claude Code-compatible hooks section."""
    raw = json.loads(HOOKS_SOURCE.read_text())

    # Strip comment keys
    hooks = {k: v for k, v in raw.items() if not k.startswith("_")}

    return hooks


def read_claude_settings() -> dict:
    if CLAUDE_SETTINGS.exists():
        try:
            return json.loads(CLAUDE_SETTINGS.read_text())
        except json.JSONDecodeError:
            print(f"Warning: {CLAUDE_SETTINGS} is not valid JSON — creating fresh copy")
    return {}


def write_claude_settings(settings: dict, dry_run: bool = False) -> None:
    content = json.dumps(settings, indent=2)
    if dry_run:
        print(f"\nWould write to {CLAUDE_SETTINGS}:")
        print(content)
    else:
        CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        CLAUDE_SETTINGS.write_text(content)


def activate(dry_run: bool = False) -> None:
    settings = read_claude_settings()
    hooks = build_claude_hooks()

    if settings.get(STUDIO_HOOKS_MARKER):
        print("Studio hooks already active in Claude Code.")
        print("Run with --off then re-activate to refresh.")
        return

    settings["hooks"] = hooks
    settings[STUDIO_HOOKS_MARKER] = True
    write_claude_settings(settings, dry_run)

    if not dry_run:
        print(f"✓ Studio hooks activated in {CLAUDE_SETTINGS}")
        _print_hook_summary(hooks)


def deactivate(dry_run: bool = False) -> None:
    settings = read_claude_settings()

    if "hooks" not in settings:
        print("No hooks found in Claude Code settings.")
        return

    if not settings.get(STUDIO_HOOKS_MARKER):
        print("Current hooks were not installed by studio — not removing.")
        print("Remove manually if needed.")
        return

    del settings["hooks"]
    settings.pop(STUDIO_HOOKS_MARKER, None)
    write_claude_settings(settings, dry_run)

    if not dry_run:
        print(f"✓ Studio hooks removed from {CLAUDE_SETTINGS}")


def status() -> None:
    print("── Studio Hooks Status ──────────────────────────────\n")

    # Source
    if HOOKS_SOURCE.exists():
        raw = json.loads(HOOKS_SOURCE.read_text())
        hook_events = [k for k in raw if not k.startswith("_")]
        print(f"Source:  {HOOKS_SOURCE}")
        print(f"Events:  {', '.join(hook_events)}\n")
    else:
        print(f"Source:  {HOOKS_SOURCE} — NOT FOUND\n")

    # Claude Code
    settings = read_claude_settings()
    hooks = settings.get("hooks", {})
    if hooks:
        if settings.get(STUDIO_HOOKS_MARKER):
            print(f"Claude:  ✓ Active (studio-managed)")
            _print_hook_summary(hooks)
        else:
            print(f"Claude:  ⚠ Hooks exist but not studio-managed")
    else:
        print(f"Claude:  ○ Not activated")

    print()


def _print_hook_summary(hooks: dict) -> None:
    skip = {STUDIO_HOOKS_MARKER}
    for event, entries in hooks.items():
        if event in skip:
            continue
        if isinstance(entries, list):
            for entry in entries:
                for h in entry.get("hooks", []):
                    cmd = h.get("command", "")
                    script = Path(cmd.split()[-1]).name if cmd else "?"
                    print(f"  {event:20s} → {script}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Activate studio hooks in AI tools")
    parser.add_argument("--off", action="store_true", help="Remove studio hooks")
    parser.add_argument("--status", action="store_true", help="Show hook status")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--tool", default="claude", choices=["claude"], help="Target tool (default: claude)")
    args = parser.parse_args()

    if args.tool != "claude":
        print(f"Tool '{args.tool}' adapter not yet implemented.")
        sys.exit(1)

    if args.status:
        status()
    elif args.off:
        deactivate(dry_run=args.dry_run)
    else:
        activate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
