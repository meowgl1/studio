from __future__ import annotations
import os
import select
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Callable

try:
    import termios
    import tty as _tty
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False

from rich.console import Console
from rich.markup import escape
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

from .config import ModelSpec, load_config
from .providers import get_provider
from .providers.base import StreamState, StreamEvent
from .branding import print_banner, print_slash_help
from .router import RouterConfig, ClassifyResult, classify
from .pii_scrubber import scrub
from .reasoning_bank import record as bank_record, stats as bank_stats

HISTORY_FILE = Path.home() / ".studio" / "mowgli" / "history"

# Injected into every headless call to suppress sycophantic prose at the source.
_TONE_SYSTEM_PROMPT = (
    "Tone rules (non-negotiable): "
    "Never open with affirmations (Certainly, Absolutely, Of course, Sure, Great question, Happy to help). "
    "No trailing summaries, sign-offs, or 'I hope this helps'. "
    "No hollow filler phrases (I'd be happy to, feel free to ask, don't hesitate to reach out). "
    "No emoji unless the user explicitly requests them. "
    "Start directly with the answer. Be concise."
)

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
        self.router = RouterConfig()
        self._last_response: str = ""
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ─── Input ─────────────────────────────────────────────────────────────────

    def _make_prompt_session(self) -> PromptSession:
        kb = KeyBindings()

        @kb.add("enter")
        def _submit(event) -> None:
            event.current_buffer.validate_and_handle()

        @kb.add("escape", "enter")  # Alt+Enter — insert newline
        def _newline(event) -> None:
            event.current_buffer.insert_text("\n")

        return PromptSession(
            history=FileHistory(str(HISTORY_FILE)),
            multiline=True,
            key_bindings=kb,
            prompt_continuation="  ╰ ",
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
            self.session_id = str(uuid.uuid4())
            self.turn = 0
            self.console.print("[dim]Context compacted. New session started with summary.[/dim]")
            return True

        if name == "/game":
            from .game import launch
            launch()
            return True

        if name == "/refine":
            self._handle_refine(arg)
            return True

        if name == "/mcp":
            self._handle_mcp(arg)
            return True

        if name == "/router":
            self._handle_router(arg)
            return True

        if name == "/swarm":
            self._handle_swarm_cmd(arg)
            return True

        if name == "/bank":
            self._handle_bank()
            return True

        self.console.print(f"[yellow]Unknown command {name!r}. Type /help for help.[/yellow]")
        return True

    def _handle_refine(self, arg: str) -> None:
        """Iteratively refine the last response. /refine [N=1]"""
        try:
            iterations = max(1, int(arg.strip())) if arg.strip() else 1
        except ValueError:
            self.console.print("[yellow]Usage: /refine [N]  — N iterations (default 1)[/yellow]")
            return

        if not self._last_response:
            self.console.print("[dim]No previous response to refine.[/dim]")
            return

        refine_prompt = (
            "Review your previous response. Improve it: remove any unnecessary prose, "
            "tighten the language, and ensure the answer is as direct and concise as possible "
            "without losing information. Output only the improved response."
        )

        for i in range(iterations):
            if iterations > 1:
                self.console.rule(f"[dim]Refinement {i + 1}/{iterations}[/dim]")
            self._execute_turn(refine_prompt)

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
            servers = list_servers()
            self.console.print()
            self.console.print("[bold]MCP Servers[/bold]")
            for s in servers:
                status = "[green]● on [/green]" if s.enabled else "[dim red]○ off[/dim red]"
                self.console.print(f"  {status}  [cyan]{s.name}[/cyan]  [dim]{s.command}[/dim]")
            self.console.print()

    def _handle_swarm_cmd(self, arg: str) -> None:
        """/swarm [N] <prompt>"""
        from .swarm import swarm_execute
        parts = arg.strip().split(maxsplit=1)
        n_workers = None
        prompt = arg.strip()

        if parts and parts[0].isdigit():
            n_workers = int(parts[0])
            prompt = parts[1] if len(parts) > 1 else ""

        if not prompt:
            self.console.print("[yellow]Usage: /swarm [N] <prompt>[/yellow]")
            return

        self._echo_input(prompt)
        cost = swarm_execute(
            task=prompt,
            config=self.config,
            router=self.router,
            console=self.console,
            tone_prompt=_TONE_SYSTEM_PROMPT,
            n_workers=n_workers,
        )
        self.total_cost += cost
        if cost > 0:
            self.console.print(f"  [dim]↳ swarm total: ${cost:.4f}[/dim]")
        self.turn += 1

    def _handle_bank(self) -> None:
        """/bank — show ReasoningBank stats."""
        s = bank_stats()
        if s.get("total", 0) == 0:
            self.console.print("[dim]ReasoningBank is empty. It fills as you use Mowgli.[/dim]")
            return
        self.console.print()
        self.console.print(f"[bold]ReasoningBank[/bold]  [dim]{s['total']} records · ${s.get('total_cost_usd', 0):.4f} logged[/dim]")
        for model, count in s.get("by_model", {}).items():
            self.console.print(f"  [cyan]{model:<14}[/cyan]  {count} calls")
        self.console.print()
        for route, count in s.get("by_route", {}).items():
            self.console.print(f"  [magenta]{route:<10}[/magenta]  {count} queries")
        self.console.print()

    # ─── Router ───────────────────────────────────────────────────────────────

    def _handle_router(self, arg: str) -> None:
        sub = arg.strip().lower()
        if sub == "on":
            self.router.enabled = True
            r = self.router
            self.console.print(
                f"  [green]Router on[/green]  "
                f"[dim]simple→{r.simple_alias}  "
                f"complex→plan:{r.complex_plan_alias} execute:{r.complex_execute_alias}  "
                f"swarm→{r.swarm_workers}×{r.swarm_worker_alias}→{r.swarm_merge_alias}[/dim]"
            )
        elif sub == "off":
            self.router.enabled = False
            self.console.print("  [dim]Router off[/dim]")
        else:
            r = self.router
            state = "[green]on[/green]" if r.enabled else "[dim]off[/dim]"
            self.console.print(
                f"  Router {state}  "
                f"[dim]simple→{r.simple_alias}  "
                f"complex→plan:{r.complex_plan_alias} execute:{r.complex_execute_alias}  "
                f"swarm→{r.swarm_workers}×{r.swarm_worker_alias}→{r.swarm_merge_alias}[/dim]"
            )
            self.console.print("  [dim]Usage: /router on|off[/dim]")

    # ─── ESC watcher ──────────────────────────────────────────────────────────

    def _watch_esc(
        self,
        proc: subprocess.Popen,
        pre_output: threading.Event,
        cancelled: threading.Event,
        stop: threading.Event,
    ) -> None:
        """Background thread: detect standalone ESC and terminate proc."""
        if not _HAS_TERMIOS or not sys.stdin.isatty():
            return
        fd = sys.stdin.fileno()
        try:
            old = termios.tcgetattr(fd)
        except termios.error:
            return
        try:
            _tty.setraw(fd)
            while not stop.is_set() and not cancelled.is_set():
                r, _, _ = select.select([fd], [], [], 0.05)
                if not r:
                    continue
                b = os.read(fd, 1)
                if b != b"\x1b":
                    continue
                r2, _, _ = select.select([fd], [], [], 0.01)
                if r2:
                    os.read(fd, 8)
                    continue
                cancelled.set()
                try:
                    proc.terminate()
                except Exception:
                    pass
                return
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass

    # ─── Turn execution ────────────────────────────────────────────────────────

    def _echo_input(self, prompt: str) -> None:
        lines = prompt.strip().split("\n")
        self.console.print(
            f"  [bold #7c3aed]▌[/bold #7c3aed] [white]{escape(lines[0])}[/white]"
        )
        for line in lines[1:]:
            self.console.print(
                f"  [#7c3aed]│[/#7c3aed] [white]{escape(line)}[/white]"
            )
        self.console.print()

    def _execute_pipe(self, prompt: str, plan_alias: str, execute_alias: str) -> float:
        """Run a two-step plan→execute pipeline across two models. Returns total cost."""
        steps = [("plan", plan_alias), ("execute", execute_alias)]
        current_prompt = prompt
        total = 0.0

        for role, alias in steps:
            spec = self.config.resolve_model(alias)
            provider = get_provider(spec.provider)
            label = "Planning" if role == "plan" else "Executing"

            self.console.rule(
                f"[bold]{label}[/bold]  [dim]{spec.alias} ({spec.provider})[/dim]"
            )

            role_prompts = {
                "plan": (
                    "Create a detailed implementation plan for the following task. "
                    "Be specific and actionable:\n\n" + current_prompt
                ),
                "execute": (
                    "Execute the following plan precisely:\n\n" + current_prompt
                ),
            }

            args = provider.build_headless_args(
                prompt=role_prompts[role],
                model_id=spec.model_id,
                session_id=str(uuid.uuid4()),
                resume=False,
                include_partial=True,
                system_prompt=_TONE_SYSTEM_PROMPT,
            )

            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            state = StreamState()
            spinner = self.console.status(
                f"[dim cyan]{spec.alias} thinking…[/dim cyan]",
                spinner="aesthetic",
                spinner_style="cyan",
            )
            spinner.start()
            result_text = ""

            def _stream_pipe(proc: subprocess.Popen, state: StreamState, on_first: Callable[[], None] | None = None) -> float:
                cost = 0.0
                first_called = False
                nonlocal result_text
                assert proc.stdout is not None
                for raw_line in proc.stdout:
                    line = raw_line.rstrip("\n")
                    if not line:
                        continue
                    event: StreamEvent | None = provider.parse_stream_line(line, state)
                    if event is None:
                        continue
                    if not first_called and event.type in ("text_delta", "tool_use"):
                        if on_first:
                            on_first()
                        first_called = True
                    if event.type == "text_delta":
                        print(event.content, end="", flush=True)
                        result_text += event.content
                    elif event.type == "tool_use":
                        if not state.last_char_newline:
                            print()
                        icon = _tool_icon(event.tool_name or "")
                        detail = _format_tool_input(event.tool_name or "", event.tool_input or {})
                        detail_str = f" [dim]{escape(detail)}[/dim]" if detail else ""
                        self.console.print(f"  {icon} [bold dim]{event.tool_name}[/bold dim]{detail_str}")
                        state.last_char_newline = True
                    elif event.type == "cost":
                        cost = event.cost_usd
                proc.wait()
                return cost

            cost = _stream_pipe(proc, state, on_first=spinner.stop)
            spinner.stop()
            total += cost

            if not state.last_char_newline:
                print()
            if cost > 0:
                self.console.print(f"  [dim]↳ ${cost:.4f}[/dim]")

            if role == "plan" and result_text.strip():
                current_prompt = result_text.strip()

        return total

    def _execute_turn(self, prompt: str) -> str | None:
        """
        Run a turn. Returns original prompt if cancelled before output, else None.

        Routing flow (when router.enabled):
          simple  → router's simple_alias model (cheap, fresh session)
          swarm   → parallel fan-out via swarm_execute()
          complex → plan:complex_plan_alias → execute:complex_execute_alias
        """
        # PII scrub before dispatch
        clean_prompt, redactions = scrub(prompt)
        if redactions:
            self.console.print(
                f"  [dim yellow]⚠ PII redacted: {', '.join(redactions)}[/dim yellow]"
            )

        self._echo_input(prompt)  # echo original (pre-scrub) to user

        # Auto-compact check
        if (
            self.router.auto_compact_turns > 0
            and self.turn > 0
            and self.turn % self.router.auto_compact_turns == 0
        ):
            self.console.print(
                f"  [dim]↺ auto-compact at turn {self.turn}[/dim]"
            )
            self._execute_turn(
                "Summarise our conversation so far: key decisions, files touched, current task state. "
                "Be concise — this summary replaces the full context."
            )
            self.session_id = str(uuid.uuid4())
            self.turn = 0

        # ── Router dispatch ──────────────────────────────────────────────────
        classify_result: ClassifyResult | None = None

        if self.router.enabled:
            classify_result = classify(clean_prompt, self.config, self.router.classifier_alias)

            route_color = {
                "simple": "cyan",
                "complex": "yellow",
                "swarm": "magenta",
            }.get(classify_result.route, "white")

            self.console.print(
                f"  [dim {route_color}]⎇ {classify_result.route}[/dim {route_color}]"
                f"  [dim]effort:{classify_result.effort} tools:{classify_result.tools}"
                f" domain:{classify_result.domain}"
                + (" parallel" if classify_result.parallel else "")
                + "[/dim]"
            )

            # ── Swarm ────────────────────────────────────────────────────────
            if classify_result.route == "swarm":
                from .swarm import swarm_execute
                cost = swarm_execute(
                    task=clean_prompt,
                    config=self.config,
                    router=self.router,
                    console=self.console,
                    tone_prompt=_TONE_SYSTEM_PROMPT,
                )
                self.total_cost += cost
                if cost > 0:
                    self.console.print(f"  [dim]↳ swarm total: ${cost:.4f}[/dim]")
                self.turn += 1
                bank_record(
                    domain=classify_result.domain,
                    effort=classify_result.effort,
                    tools=classify_result.tools,
                    parallel=classify_result.parallel,
                    route="swarm",
                    model=self.router.swarm_merge_alias,
                    cost_usd=cost,
                )
                return None

            # ── Complex pipeline ─────────────────────────────────────────────
            if classify_result.route == "complex":
                cost = self._execute_pipe(
                    clean_prompt,
                    self.router.complex_plan_alias,
                    self.router.complex_execute_alias,
                )
                self.total_cost += cost
                self.turn += 1
                bank_record(
                    domain=classify_result.domain,
                    effort=classify_result.effort,
                    tools=classify_result.tools,
                    parallel=classify_result.parallel,
                    route="complex",
                    model=self.router.complex_execute_alias,
                    cost_usd=cost,
                )
                return None

            # ── Simple: use router's simple_alias model ───────────────────────
            # FIX: was falling through to self.model_spec — now uses simple_alias
            simple_spec = self.config.resolve_model(self.router.simple_alias)
            simple_provider = get_provider(simple_spec.provider)

            args = simple_provider.build_headless_args(
                prompt=clean_prompt,
                model_id=simple_spec.model_id,
                session_id=str(uuid.uuid4()),  # simple queries are stateless
                resume=False,
                system_prompt=_TONE_SYSTEM_PROMPT,
            )

            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            state = StreamState()
            pre_output = threading.Event()
            cancelled = threading.Event()
            stop_watcher = threading.Event()

            watcher = threading.Thread(
                target=self._watch_esc,
                args=(proc, pre_output, cancelled, stop_watcher),
                daemon=True,
            )
            watcher.start()

            spinner = self.console.status(
                f"[dim cyan]{simple_spec.alias} thinking…[/dim cyan]",
                spinner="aesthetic",
                spinner_style="cyan",
            )
            spinner.start()

            def _on_first_simple() -> None:
                pre_output.set()
                spinner.stop()

            cost = self._stream_response(proc, state, on_first_output=_on_first_simple)

            stop_watcher.set()
            watcher.join(timeout=0.3)
            spinner.stop()

            if cancelled.is_set() and not pre_output.is_set():
                self.console.print("[dim]↩ cancelled[/dim]")
                return prompt

            self.total_cost += cost
            self.turn += 1

            if not state.last_char_newline:
                print()
            if cost > 0:
                self.console.print(f"  [dim]↳ ${cost:.4f}[/dim]")

            bank_record(
                domain=classify_result.domain,
                effort=classify_result.effort,
                tools=classify_result.tools,
                parallel=classify_result.parallel,
                route="simple",
                model=simple_spec.alias,
                cost_usd=cost,
            )
            return None

        # ── Router disabled: use session model directly ──────────────────────
        args = self.provider.build_headless_args(
            prompt=clean_prompt,
            model_id=self.model_spec.model_id,
            session_id=self.session_id,
            resume=(self.turn > 0),
            system_prompt=_TONE_SYSTEM_PROMPT if self.turn == 0 else None,
        )

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        state = StreamState()
        pre_output = threading.Event()
        cancelled = threading.Event()
        stop_watcher = threading.Event()

        watcher = threading.Thread(
            target=self._watch_esc,
            args=(proc, pre_output, cancelled, stop_watcher),
            daemon=True,
        )
        watcher.start()

        spinner = self.console.status(
            f"[dim cyan]{self.model_spec.alias} thinking…[/dim cyan]",
            spinner="aesthetic",
            spinner_style="cyan",
        )
        spinner.start()

        def _on_first_output() -> None:
            pre_output.set()
            spinner.stop()

        cost = self._stream_response(proc, state, on_first_output=_on_first_output)

        stop_watcher.set()
        watcher.join(timeout=0.3)
        spinner.stop()

        if cancelled.is_set() and not pre_output.is_set():
            self.console.print("[dim]↩ cancelled[/dim]")
            return prompt

        self.total_cost += cost
        self.turn += 1

        if not state.last_char_newline:
            print()
        if cost > 0:
            self.console.print(f"  [dim]↳ ${cost:.4f}[/dim]")

        stderr = proc.stderr.read() if proc.stderr else ""
        if proc.returncode not in (0, None) and stderr:
            self.console.print(f"[dim red]{escape(stderr[:300])}[/dim red]")

        return None

    def _stream_response(
        self,
        proc: subprocess.Popen,
        state: StreamState,
        on_first_output: Callable[[], None] | None = None,
    ) -> float:
        cost = 0.0
        first_called = False
        assert proc.stdout is not None
        response_text = ""

        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            if not line:
                continue

            event: StreamEvent | None = self.provider.parse_stream_line(line, state)
            if event is None:
                continue

            if not first_called and event.type in ("text_delta", "tool_use"):
                if on_first_output:
                    on_first_output()
                first_called = True

            if event.type == "text_delta":
                print(event.content, end="", flush=True)
                response_text += event.content

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
        if response_text:
            self._last_response = response_text
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
        cancelled_prompt: str = ""

        while True:
            try:
                user_input: str = session.prompt(
                    self._input_prompt(),
                    default=cancelled_prompt,
                )
                cancelled_prompt = ""
            except KeyboardInterrupt:
                cancelled_prompt = ""
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

            restored = self._execute_turn(text)
            if restored is not None:
                cancelled_prompt = restored
