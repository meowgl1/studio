#!/usr/bin/env python3
"""
Studio Dashboard — quick overview of your studio and active project.
Uses `rich` for terminal output (pip install rich).

Usage:
  python3 ~/.studio/scripts/dashboard.py              # auto-detect project from cwd
  python3 ~/.studio/scripts/dashboard.py /path/to/project
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path.home() / ".studio" / "scripts"))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich import box
    from rich.text import Text
    from rich.rule import Rule
except ImportError:
    print("Install rich: pip install rich")
    sys.exit(1)

from lib.studio import (
    STUDIO_DIR,
    SESSIONS_DIR,
    get_project_name,
    get_project_root,
    get_project_studio_dir,
    estimate_cost,
)

console = Console()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_project_from_args() -> Path | None:
    if len(sys.argv) > 1:
        p = Path(sys.argv[1]).resolve()
        if p.exists():
            return p
    return None


def read_tasks(studio_dir: Path) -> dict:
    tasks_file = studio_dir / "tasks.md"
    if not tasks_file.exists():
        return {}
    content = tasks_file.read_text()
    result = {"doing": [], "next": [], "blocked": []}
    current = None
    for line in content.splitlines():
        if "## Doing" in line:
            current = "doing"
        elif "## Next" in line:
            current = "next"
        elif "## Blocked" in line:
            current = "blocked"
        elif "## Done" in line:
            current = None
        elif current and line.strip().startswith("- "):
            result[current].append(line.strip()[2:])
    return result


def read_recent_changelog(studio_dir: Path, limit: int = 3) -> list[tuple[str, str]]:
    changelog_dir = studio_dir / "changelog"
    if not changelog_dir.exists():
        return []
    files = sorted(changelog_dir.glob("*.md"), reverse=True)[:limit]
    entries = []
    for f in files:
        content = f.read_text().strip()
        # Take first non-empty line as summary
        first_line = next((l for l in content.splitlines() if l.strip()), "")
        entries.append((f.stem, first_line[:80] + "…" if len(first_line) > 80 else first_line))
    return entries


def get_recent_sessions(project: str, limit: int = 5) -> list[dict]:
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


def list_global_skills() -> list[str]:
    skills_dir = STUDIO_DIR / "skills"
    if not skills_dir.exists():
        return []
    return [d.name for d in sorted(skills_dir.iterdir()) if d.is_dir() and (d / "SKILL.md").exists()]


def list_global_agents() -> list[str]:
    agents_dir = STUDIO_DIR / "agents"
    if not agents_dir.exists():
        return []
    return [f.stem for f in sorted(agents_dir.glob("*.md"))]


def check_hooks_active() -> bool:
    settings_file = Path.home() / ".claude" / "settings.json"
    if not settings_file.exists():
        return False
    try:
        data = json.loads(settings_file.read_text())
        return "hooks" in data
    except Exception:
        return False


# ─── Render sections ──────────────────────────────────────────────────────────

def render_header(project_name: str, project_root: Path | None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subtitle = str(project_root) if project_root else "no project detected"
    console.print(
        Panel(
            f"[bold cyan]{project_name}[/bold cyan]  [dim]{subtitle}[/dim]\n[dim]{now}[/dim]",
            title="[bold]Studio Dashboard[/bold]",
            border_style="cyan",
        )
    )


def render_tasks(tasks: dict):
    if not any(tasks.values()):
        console.print("[dim]  No tasks.md found[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Status", style="bold", width=10)
    table.add_column("Task")

    for item in tasks.get("doing", []):
        status = "[green]● doing[/green]" if "[ ]" in item else "[green]✓ done[/green]"
        table.add_row(status, item.replace("[ ] ", "").replace("[x] ", ""))

    for item in tasks.get("next", []):
        table.add_row("[yellow]○ next[/yellow]", item.replace("[ ] ", ""))

    for item in tasks.get("blocked", []):
        if item.strip():
            table.add_row("[red]✗ blocked[/red]", item)

    console.print(Panel(table, title="Tasks", border_style="yellow"))


def render_sessions(sessions: list[dict]):
    if not sessions:
        console.print("[dim]  No sessions recorded[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Files", width=6)
    table.add_column("Cost", width=8)
    table.add_column("Session ID", style="dim", width=20)

    for s in sessions:
        date = s.get("started_at", "")[:10]
        files = str(len(s.get("files_edited", [])))
        cost = f"${s.get('estimated_cost_usd', 0):.3f}"
        sid = s.get("session_id", "")[:18]
        table.add_row(date, files, cost, sid)

    console.print(Panel(table, title="Recent Sessions", border_style="blue"))


def render_changelog(entries: list[tuple[str, str]]):
    if not entries:
        console.print("[dim]  No changelog entries[/dim]")
        return
    text = Text()
    for date, summary in entries:
        text.append(f"  {date}  ", style="cyan")
        text.append(f"{summary}\n", style="dim")
    console.print(Panel(text, title="Changelog (last 3)", border_style="dim"))


def render_skills_and_agents(skills: list[str], agents: list[str]):
    skills_text = "  " + "  ".join(f"[cyan]{s}[/cyan]" for s in skills) if skills else "[dim]  none[/dim]"
    agents_text = "  " + "  ".join(f"[green]{a}[/green]" for a in agents) if agents else "[dim]  none[/dim]"
    console.print(Panel(skills_text, title=f"Global Skills ({len(skills)})", border_style="cyan"))
    console.print(Panel(agents_text, title=f"Global Agents ({len(agents)})", border_style="green"))


def render_hooks_status(active: bool):
    status = "[green]✓ active[/green]" if active else "[yellow]○ not activated[/yellow]"
    hint = "" if active else "\n  [dim]Run: python3 ~/.studio/scripts/activate-hooks.py[/dim]"
    console.print(Panel(f"  Hooks: {status}{hint}", title="Automation", border_style="dim"))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Resolve project
    override = get_project_from_args()
    if override:
        os.chdir(override)

    project_name = get_project_name()
    project_root = get_project_root()
    studio_dir = get_project_studio_dir()

    render_header(project_name, project_root)

    # Tasks
    if studio_dir:
        tasks = read_tasks(studio_dir)
        render_tasks(tasks)
        changelog = read_recent_changelog(studio_dir)
        render_changelog(changelog)
    else:
        console.print("[dim]  No local .studio/ found for this project[/dim]")

    # Sessions
    sessions = get_recent_sessions(project_name)
    render_sessions(sessions)

    # Global skills and agents
    skills = list_global_skills()
    agents = list_global_agents()
    render_skills_and_agents(skills, agents)

    # Hooks
    hooks_active = check_hooks_active()
    render_hooks_status(hooks_active)

    console.print()


if __name__ == "__main__":
    main()
