from __future__ import annotations
import json
import os
import shutil

from .base import Provider, StreamEvent, StreamState

GEMINI_BINARY = shutil.which("gemini") or "/opt/homebrew/bin/gemini"


class GeminiProvider:
    name = "gemini"

    def build_headless_args(
        self,
        prompt: str,
        model_id: str,
        session_id: str,
        resume: bool = False,
        include_partial: bool = True,
    ) -> list[str]:
        args = [
            GEMINI_BINARY,
            "-p", prompt,
            "-o", "stream-json",
            "-m", model_id,
        ]
        if resume:
            # Gemini doesn't support --resume <uuid>, use latest
            args += ["--resume", "latest"]
        else:
            args += ["--session-id", session_id]

        return args

    def parse_stream_line(self, line: str, state: StreamState) -> StreamEvent | None:
        """
        Parse Gemini stream-json events.
        Gemini's format mirrors Claude's but field names may differ slightly.
        """
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None

        etype = event.get("type", "")

        # Gemini mirrors Claude's format in recent versions
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
                        return StreamEvent(
                            type="tool_use",
                            tool_name=block.get("name"),
                            tool_input=block.get("input", {}),
                        )
            return None

        # Gemini may also emit top-level text events
        if etype == "text":
            text = event.get("text", "") or event.get("content", "")
            if text and len(text) > state.printed_text_len:
                delta = text[state.printed_text_len:]
                state.printed_text_len = len(text)
                return StreamEvent(type="text_delta", content=delta)
            return None

        if etype == "result":
            cost = event.get("total_cost_usd", 0.0)
            return StreamEvent(type="cost", cost_usd=cost)

        return None

    def run_interactive(self, model_id: str) -> None:
        args = [GEMINI_BINARY, "-m", model_id]
        os.execvp(GEMINI_BINARY, args)
