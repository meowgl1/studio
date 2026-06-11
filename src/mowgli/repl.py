from __future__ import annotations
import subprocess
import uuid
from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.markup import escape
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from .config import ModelSpec, load_config
from .providers import get_provider
from .providers.base import StreamState, StreamEvent
from .branding import print_banner, print_slash_help

HISTORY_FILE = Path.home() / ".studio" / "mowgli" / "history"

# Tool display names + icons
_TOOL_ICONS: dict[str, str] = {
    "Read": "📄",
    "Write": "✏️",
    "Edit": "🔧",
    "Bash": "⚡",
    "Glob": "🔍",
    "Grep": "🔎",
    "WebFetch": "🌐",
    "WebSearch": "🔎",
    "TodoWrite": "📝",
    "Agent": "🤖",
}


def _tool_icon(name: str) -> str:
    return _TOOL_ICONS.get(name, "⚙")


def _format_tool_input(tool_name: str, tool_input: dict) -> str:
    """Return a short human-readable summary of tool inputs."""
    if not tool_input:
        return ""
    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:80] + ("…" if len(cmd) > 80 else "")
    if tool_name in ("Glob",):
        return tool_input.get("pattern", "")
    if tool_name == "Grep":
        return f"{tool_input.get('pattern', '')} in {tool_input.get('path', '.')}"
    if tool_name in ("WebFetch", "WebSearch"):
        return tool_input.get("url", tool_input.get("query", ""))
    # Fallback: first value
    first_val = next(iter(tool_input.values()), "")
    return str(first_val)[:80]


class MowgliREPL:
    def __init__(self, model_alias: str | None = None) -> None:
        self.console = Console()
        self.config = load_config()
        alias = model_alias or self.config.default_model
        self.model_spec: ModelSpec = self.config.resolve_model(alias)
        self.provider = get_provider(self.model_spec.provider)
        self.session_id = str(uuid.uuid4())
        self.turn = 0
        self.total_cost = 0.0
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ─── Input ─────────────────────────────────────────────────────────────────

    def _make_prompt_session(self) -> PromptSession:
        return PromptSession(
            history=FileHistory(str(HISTORY_FILE)),
            multiline=False,
        )

    def _input_prompt(self) -> str:
        model = self.model_spec.alias
        provider = self.model_spec.provider
        return f"[{provider}:{model}] › "

    # ─── Slash commands ────────────────────────────────────────────────────────

    def _handle_slash(self, cmd: str) -> bool:
        """Returns True if we should continue the loop, False to exit."""
        parts = cmd.strip().split(maxsplit=1)
        name = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if name in ("/exit", "/quit"):
            return False

        if name == "/help":
            print_slash_help(self.console)
            return True

        if name == "/models":
            self.console.print()
            self.console.print("[bold]Available models[/bold]")
            for alias, spec in self.config.models.items():
                marker = " [green]◀ active[/green]" if alias == self.model_spec.alias else ""
                self.console.print(
                    f"  [cyan]{alias:<14}[/cyan]  [dim]{spec.provider}[/dim]  {spec.model_id}{marker}"
                )
            self.console.print()
            return True

        if name == "/model":
            if not arg:
                self.console.print("[yellow]Usage: /model <alias>[/yellow]")
                return True
            try:
                new_spec = self.config.resolve_model(arg)
            except ValueError as e:
                self.console.print(f"[red]{e}[/red]")
                return True
            self.model_spec = new_spec
            self.provider = get_provider(new_spec.provider)
            self.session_id = str(uuid.uuid4())
            self.turn = 0
            self.console.print(
                f"[green]Switched to[/green] [cyan]{new_spec.alias}[/cyan]"
                f" [dim]({new_spec.provider} / {new_spec.model_id})[/dim]"
                f" [dim]— new session started[/dim]"
            )
            return True

        if name == "/clear":
            self.session_id = str(uuid.uuid4())
            self.turn = 0
            self.console.print("[dim]Session cleared. New context started.[/dim]")
            return True

        if name == "/cost":
            self.console.print(
                f"[dim]Session total:[/dim] [bold green]${self.total_cost:.4f}[/bold green]"
            )
            return True

        if name == "/compact":
            compact_prompt = (
                "Please summarize our conversation so far, including the key decisions, "
                "files we've worked on, and the current state of the task. "
                "This will serve as the compressed context going forward."
            )
            self._execute_turn(compact_prompt)
            return True

        if name == "/mcp":
            self._handle_mcp(arg)
            return True

        self.console.print(f"[yellow]Unknown command {name!r}. Type /help for help.[/yellow]")
        return True

    def _handle_mcp(self, arg: str) -> None:
        from .mcp_manager import list_servers, enable_server, disable_server
        parts = arg.strip().split(maxsplit=1)
        sub = parts[0].lower() if parts else ""
        target = parts[1] if len(parts) > 1 else ""

        if sub == "on" and target:
            self.console.print(f"  {enable_server(target)}")
        elif sub == "off" and target:
            self.console.print(f"  {disable_server(target)}")
        else:
            # List
            servers = list_servers()
            self.console.print()
            self.console.print("[bold]MCP Servers[/bold]")
            for s in servers:
                status = "[green]● on [/green]" if s.enabled else "[dim red]○ off[/dim red]"
                self.console.print(f"  {status}  [cyan]{s.name}[/cyan]  [dim]{s.command}[/dim]")
            self.console.print()

    # ─── Turn execution ────────────────────────────────────────────────────────

    def _execute_turn(self, prompt: str) -> None:
        args = self.provider.build_headless_args(
            prompt=prompt,
            model_id=self.model_spec.model_id,
            session_id=self.session_id,
            resume=(self.turn > 0),
        )

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        state = StreamState()

        # Show spinner until the first real output arrives
        spinner = self.console.status(
            f"[dim]{self.model_spec.alias} thinking...[/dim]",
            spinner="dots",
        )
        spinner.start()

        def _stop_spinner() -> None:
            spinner.stop()

        cost = self._stream_response(proc, state, on_first_output=_stop_spinner)

        # Ensure spinner is stopped even if no output came
        spinner.stop()

        self.total_cost += cost
        self.turn += 1

        if not state.last_char_newline:
            print()

        if cost > 0:
            self.console.print(f"  [dim]↳ ${cost:.4f}[/dim]")

        stderr = proc.stderr.read() if proc.stderr else ""
        if proc.returncode not in (0, None) and stderr:
            self.console.print(f"[dim red]{escape(stderr[:300])}[/dim red]")

    def _stream_response(
        self,
        proc: subprocess.Popen,
        state: StreamState,
        on_first_output: Callable[[], None] | None = None,
    ) -> float:
        cost = 0.0
        first_called = False
        assert proc.stdout is not None

        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            if not line:
                continue

            event: StreamEvent | None = self.provider.parse_stream_line(line, state)
            if event is None:
                continue

            # Stop spinner on first meaningful event
            if not first_called and event.type in ("text_delta", "tool_use"):
                if on_first_output:
                    on_first_output()
                first_called = True

            if event.type == "text_delta":
                print(event.content, end="", flush=True)

            elif event.type == "tool_use":
                if not state.last_char_newline:
                    print()
                icon = _tool_icon(event.tool_name or "")
                detail = _format_tool_input(event.tool_name or "", event.tool_input or {})
                detail_str = f" [dim]{escape(detail)}[/dim]" if detail else ""
                self.console.print(
                    f"  {icon} [bold dim]{event.tool_name}[/bold dim]{detail_str}"
                )
                state.last_char_newline = True

            elif event.type == "tool_result":
                pass

            elif event.type == "cost":
                cost = event.cost_usd

        proc.wait()
        return cost

    # ─── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        print_banner(
            self.console,
            model_alias=self.model_spec.alias,
            provider=self.model_spec.provider,
            model_id=self.model_spec.model_id,
        )
        self.console.print("[dim]Type /help for commands  ·  Ctrl+C or /exit to quit[/dim]")
        self.console.print()

        session = self._make_prompt_session()

        while True:
            try:
                user_input: str = session.prompt(self._input_prompt())
            except KeyboardInterrupt:
                self.console.print("\n[dim](Ctrl+C — type /exit to quit)[/dim]")
                continue
            except EOFError:
                self.console.print("\n[dim]Bye.[/dim]")
                break

            text = user_input.strip()

            if not text:
                continue

            if text.startswith("/"):
                should_continue = self._handle_slash(text)
                if not should_continue:
                    self.console.print(
                        f"[dim]Session ended. Total cost: ${self.total_cost:.4f}[/dim]"
                    )
                    break
                continue

            self._execute_turn(text)
