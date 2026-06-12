from __future__ import annotations
from pathlib import Path
from rich.console import Console
from rich.text import Text
import os

STUDIO_VERSION = "1.0.0"

LOGO = """
███╗   ███╗ ██████╗ ██╗    ██╗ ██████╗ ██╗     ██╗
████╗ ████║██╔═══██╗██║    ██║██╔════╝ ██║     ██║
██╔████╔██║██║   ██║██║ █╗ ██║██║  ███╗██║     ██║
██║╚██╔╝██║██║   ██║██║███╗██║██║   ██║██║     ██║
██║ ╚═╝ ██║╚██████╔╝╚███╔███╔╝╚██████╔╝███████╗██║
╚═╝     ╚═╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ ╚══════╝╚═╝
""".strip()


def _get_project_name() -> str:
    cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
    for parent in [cwd, *cwd.parents]:
        if (parent / ".studio").exists():
            return parent.name
    return cwd.name


def print_banner(console: Console, model_alias: str, provider: str, model_id: str) -> None:
    project = _get_project_name()

    console.print()
    console.print(Text(LOGO, style="bold green"))
    console.print("  [bold white]── STUDIO[/bold white]  "
                  f"[dim]v{STUDIO_VERSION}[/dim]")
    console.print()
    console.print(
        f"  [dim]model[/dim] [bold cyan]{model_alias}[/bold cyan]  "
        f"[dim]via[/dim] [yellow]{provider}[/yellow]  "
        f"[dim]project[/dim] [green]{project}[/green]"
    )
    console.print()
    console.rule(style="dim #7c3aed")
    console.print()


def print_slash_help(console: Console) -> None:
    console.print()
    console.print("[bold]Commands[/bold]")
    console.print("  [cyan]/model[/cyan] [dim]<alias>[/dim]   switch model  [dim](opus, sonnet, haiku, gemini-pro, gemini-lite)[/dim]")
    console.print("  [cyan]/models[/cyan]          list available models")
    console.print("  [cyan]/clear[/cyan]            start a new session (clears context)")
    console.print("  [cyan]/cost[/cyan]             show total cost this session")
    console.print("  [cyan]/compact[/cyan]          ask the model to summarize and compress context")
    console.print("  [cyan]/router[/cyan]           show router status")
    console.print("  [cyan]/router on|off[/cyan]   enable / disable auto-routing")
    console.print("  [cyan]/swarm[/cyan] [dim][N] <prompt>[/dim]  fan-out to N parallel agents then merge")
    console.print("  [cyan]/bank[/cyan]             ReasoningBank stats (routing history)")
    console.print("  [cyan]/refine[/cyan] [dim][N][/dim]       refine last response N times")
    console.print("  [cyan]/mcp[/cyan]              list MCP servers")
    console.print("  [cyan]/mcp on[/cyan] [dim]<name>[/dim]   enable an MCP server")
    console.print("  [cyan]/mcp off[/cyan] [dim]<name>[/dim]  disable an MCP server")
    console.print("  [cyan]/help[/cyan]             show this help")
    console.print("  [cyan]/game[/cyan]             pixel dino — SPACE to jump, Q to quit")
    console.print("  [cyan]/exit[/cyan] [dim]or[/dim] [cyan]/quit[/cyan]   exit mowgli")
    console.print()
    console.print("[dim]Tip: Alt+Enter for new line  ·  ↑↓ to navigate within text  ·  Alt+↑↓ for history[/dim]")
    console.print()
