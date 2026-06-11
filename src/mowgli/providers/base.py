from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ProviderResult:
    text: str
    cost_usd: float = 0.0
    session_id: str | None = None
    model: str | None = None


@dataclass
class StreamEvent:
    type: str           # "text_delta" | "tool_use" | "tool_result" | "cost" | "error"
    content: str = ""
    tool_name: str | None = None
    tool_input: dict | None = None
    cost_usd: float = 0.0
    raw: dict | None = None


class Provider(Protocol):
    name: str

    def build_headless_args(
        self,
        prompt: str,
        model_id: str,
        session_id: str,
        resume: bool = False,
        include_partial: bool = True,
    ) -> list[str]: ...

    def parse_stream_line(self, line: str, state: "StreamState") -> StreamEvent | None: ...

    def run_interactive(self, model_id: str) -> None: ...


class StreamState:
    """Mutable state shared across event parsing within one turn."""

    def __init__(self) -> None:
        self.printed_text_len: int = 0
        self.seen_tool_ids: set[str] = set()
        self.last_char_newline: bool = True
        self.session_id: str | None = None

    def reset(self) -> None:
        self.printed_text_len = 0
        self.seen_tool_ids = set()
        self.last_char_newline = True
