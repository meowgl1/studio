from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()
STUDIO_DIR = Path.home() / ".studio"


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-m", "--model", default=None, help="Model alias (opus, sonnet, haiku, gemini-pro, gemini-lite)")
@click.option("-p", "--prompt", "headless_prompt", default=None, help="Run headless with a prompt (non-interactive)")
@click.option("-o", "--output-format", type=click.Choice(["text", "json"]), default="text", help="Output format for --prompt mode")
@click.pass_context
def main(ctx: click.Context, model: str | None, headless_prompt: str | None, output_format: str) -> None:
    """Mowgli Studio — unified AI coding CLI."""
    if ctx.invoked_subcommand is not None:
        return

    if headless_prompt:
        _run_headless(headless_prompt, model, output_format)
        return

    from .repl import MowgliREPL
    try:
        MowgliREPL(model_alias=model).run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _run_headless(prompt: str, model_alias: str | None, output_format: str) -> None:
    from .config import load_config
    from .providers import get_provider
    import uuid
    import json as _json
    from .providers.base import StreamState

    config = load_config()
    alias = model_alias or config.default_model
    spec = config.resolve_model(alias)
    provider = get_provider(spec.provider)

    args = provider.build_headless_args(
        prompt=prompt,
        model_id=spec.model_id,
        session_id=str(uuid.uuid4()),
        resume=False,
        include_partial=False,
    )

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    state = StreamState()
    result_text = ""

    assert proc.stdout
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        if not line:
            continue
        event = provider.parse_stream_line(line, state)
        if event and event.type == "text_delta":
            result_text += event.content

    proc.wait()

    if output_format == "json":
        print(_json.dumps({"result": result_text}))
    else:
        print(result_text)


# ─── MCP group ────────────────────────────────────────────────────────────────

@main.group(invoke_without_command=True)
@click.pass_context
def mcp(ctx: click.Context) -> None:
    """Manage MCP servers (list / enable / disable)."""
    if ctx.invoked_subcommand is None:
        _mcp_list()


def _mcp_list() -> None:
    from .mcp_manager import list_servers
    servers = list_servers()
    console.print()
    console.print("[bold]MCP Servers[/bold]  [dim](source: ~/.studio/mcp/global.json)[/dim]")
    if not servers:
        console.print("  [dim]No servers configured.[/dim]")
    for s in servers:
        if s.enabled:
            status = "[green]● on [/green]"
        else:
            status = "[dim red]○ off[/dim red]"
        cmd_str = f"[dim]{s.command} {' '.join(s.args)}[/dim]"
        console.print(f"  {status}  [cyan]{s.name:<16}[/cyan]  {cmd_str}")
    console.print()


@mcp.command(name="on")
@click.argument("name")
def mcp_on(name: str) -> None:
    """Enable an MCP server."""
    from .mcp_manager import enable_server
    msg = enable_server(name)
    console.print(f"  {msg}")


@mcp.command(name="off")
@click.argument("name")
def mcp_off(name: str) -> None:
    """Disable an MCP server."""
    from .mcp_manager import disable_server
    msg = disable_server(name)
    console.print(f"  {msg}")


# ─── Other subcommands ────────────────────────────────────────────────────────

@main.command()
def models() -> None:
    """List all available models."""
    from .config import load_config
    config = load_config()
    console.print()
    console.print("[bold]Available models[/bold]")
    for alias, spec in config.models.items():
        status = "[green]ready[/green]"
        default_marker = " [green](default)[/green]" if alias == config.default_model else ""
        console.print(
            f"  [cyan]{alias:<14}[/cyan]  {status:<10} [dim]{spec.provider:<8}[/dim]  {spec.model_id}{default_marker}"
        )
    console.print()


@main.command()
def status() -> None:
    """Show Studio hooks and MCP activation status."""
    activate = STUDIO_DIR / "scripts" / "activate.py"
    if not activate.exists():
        console.print("[red]activate.py not found[/red]")
        return
    subprocess.run(["python3", str(activate), "--status"])


@main.command()
def activate() -> None:
    """Activate Studio hooks and MCP servers."""
    activate_script = STUDIO_DIR / "scripts" / "activate.py"
    subprocess.run(["python3", str(activate_script)])


@main.command()
def deactivate() -> None:
    """Deactivate Studio hooks and MCP servers."""
    activate_script = STUDIO_DIR / "scripts" / "activate.py"
    subprocess.run(["python3", str(activate_script), "--off"])


@main.command(name="pipe")
@click.option("--plan", required=True, help="Model alias for planning step")
@click.option("--execute", required=True, help="Model alias for execution step")
@click.option("--review", default=None, help="Optional model alias for review step")
@click.argument("task")
def pipe_cmd(plan: str, execute: str, review: str | None, task: str) -> None:
    """Chain providers: plan with one model, execute with another.

    Example: mowgli pipe --plan opus --execute gemini-pro "Build a REST API"
    """
    from .config import load_config
    from .providers import get_provider
    from .providers.base import StreamState, StreamEvent
    import uuid

    config = load_config()
    console.print()

    steps = [("plan", plan), ("execute", execute)]
    if review:
        steps.insert(-1, ("review", review))

    current_prompt = task

    for role, alias in steps:
        spec = config.resolve_model(alias)
        provider = get_provider(spec.provider)

        label = {"plan": "Planning", "execute": "Executing", "review": "Reviewing"}[role]
        console.rule(f"[bold]{label}[/bold]  [dim]{spec.alias} ({spec.provider})[/dim]")

        role_prompts = {
            "plan": f"Create a detailed implementation plan for the following task. Be specific and actionable:\n\n{current_prompt}",
            "execute": f"Execute the following plan precisely:\n\n{current_prompt}",
            "review": f"Review the following output for correctness, security issues, and improvements:\n\n{current_prompt}",
        }

        args = provider.build_headless_args(
            prompt=role_prompts[role],
            model_id=spec.model_id,
            session_id=str(uuid.uuid4()),
            resume=False,
            include_partial=True,
        )

        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        state = StreamState()
        result_text = ""

        assert proc.stdout
        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            if not line:
                continue
            event: StreamEvent | None = provider.parse_stream_line(line, state)
            if event is None:
                continue
            if event.type == "text_delta":
                print(event.content, end="", flush=True)
                result_text += event.content
            elif event.type == "tool_use":
                if not state.last_char_newline:
                    print()
                console.print(f"  ⚙ [dim]{event.tool_name}[/dim]")
                state.last_char_newline = True

        proc.wait()
        if not state.last_char_newline:
            print()
        console.print()

        current_prompt = result_text

    console.rule("[green]Done[/green]")
