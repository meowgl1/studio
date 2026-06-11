from __future__ import annotations
import json
import os
import shutil
from pathlib import Path

from .base import Provider, StreamEvent, StreamState

CLAUDE_BINARY = shutil.which("claude") or "/opt/homebrew/bin/claude"
STUDIO_SETTINGS = Path.home() / ".studio" / "settings.json"


class ClaudeProvider:
    name = "claude"

    def build_headless_args(
        self,
        prompt: str,
        model_id: str,
        session_id: str,
        resume: bool = False,
        include_partial: bool = True,
    ) -> list[str]:
        args = [
            CLAUDE_BINARY,
            "-p", prompt,
            "--output-format", "stream-json",
            "--model", model_id,
        ]
        if resume:
            args += ["--resume", session_id]
        else:
            args += ["--session-id", session_id]

        # stream-json requires --verbose in Claude Code
        args.append("--verbose")

        if include_partial:
            args.append("--include-partial-messages")

        if STUDIO_SETTINGS.exists():
            args += ["--settings", str(STUDIO_SETTINGS)]

        return args

    def parse_stream_line(self, line: str, state: StreamState) -> StreamEvent | None:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None

        etype = event.get("type", "")

        if etype == "system" and event.get("subtype") == "init":
            state.session_id = event.get("session_id")
            return None

        if etype == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content:
                btype = block.get("type", "")

                if btype == "text":
                    text = block.get("text", "")
                    if len(text) > state.printed_text_len:
                        delta = text[state.printed_text_len:]
                        state.printed_text_len = len(text)
                        state.last_char_newline = text.endswith("\n")
                        return StreamEvent(type="text_delta", content=delta)

                elif btype == "tool_use":
                    tid = block.get("id", "")
                    if tid not in state.seen_tool_ids:
                        state.seen_tool_ids.add(tid)
                        state.last_char_newline = True
                        return StreamEvent(
                            type="tool_use",
                            tool_name=block.get("name"),
                            tool_input=block.get("input", {}),
                            raw=block,
                        )
            return None

        if etype == "user":
            content = event.get("message", {}).get("content", [])
            for block in content:
                if block.get("type") == "tool_result":
                    result_content = block.get("content", [])
                    text = ""
                    if isinstance(result_content, list):
                        text = " ".join(
                            b.get("text", "") for b in result_content if b.get("type") == "text"
                        )
                    elif isinstance(result_content, str):
                        text = result_content
                    return StreamEvent(type="tool_result", content=text[:200])
            return None

        if etype == "result":
            cost = event.get("total_cost_usd", 0.0)
            state.last_char_newline = True
            return StreamEvent(type="cost", cost_usd=cost)

        return None

    def run_interactive(self, model_id: str) -> None:
        """Replace current process with claude interactive session."""
        args = [CLAUDE_BINARY, "--model", model_id]
        os.execvp(CLAUDE_BINARY, args)
