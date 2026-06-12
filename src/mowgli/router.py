"""
Mowgli router — multi-dimensional query classifier and dispatch config.

Classification returns a ClassifyResult with:
  effort   1-10   cognitive/engineering effort required
  tools    int    estimated tool calls needed (0 = pure text)
  domain   str    conversational | factual | code | architectural | creative
  parallel bool   whether subtasks can run concurrently (swarm candidate)
  route    str    simple | complex | swarm

Routing thresholds:
  simple   effort <= 4 and tools <= 1
  swarm    effort >= 7 and parallel == True
  complex  everything else → plan:opus → execute:sonnet pipeline
"""
from __future__ import annotations
import json
import subprocess
import uuid
from dataclasses import dataclass
from typing import Literal

from .config import MowgliConfig
from .providers import get_provider
from .providers.base import StreamState

RouteType = Literal["simple", "complex", "swarm"]

_CLASSIFY_PROMPT = """\
Analyse the following user query and return a JSON object — nothing else, no prose.

Fields:
  effort   (int 1-10): cognitive/engineering effort required to answer well
  tools    (int 0-N):  estimated number of tool calls needed (0 = pure text reply)
  domain   (str):      one of: conversational | factual | code | architectural | creative
  parallel (bool):     true if the task contains independent subtasks that could run concurrently
  route    (str):      one of: simple | complex | swarm

Routing rules you must follow:
  simple  → effort ≤ 4 AND tools ≤ 1  (use cheap/fast model, no pipeline)
  swarm   → effort ≥ 7 AND parallel is true  (fan-out to parallel agents then merge)
  complex → everything else  (sequential plan→execute pipeline)

Example output:
{"effort": 3, "tools": 0, "domain": "factual", "parallel": false, "route": "simple"}

Query: {query}"""


@dataclass
class ClassifyResult:
    effort: int = 5
    tools: int = 0
    domain: str = "code"
    parallel: bool = False
    route: RouteType = "complex"

    @classmethod
    def fallback(cls) -> "ClassifyResult":
        """Safe default when classification fails."""
        return cls(effort=5, tools=0, domain="code", parallel=False, route="complex")

    @classmethod
    def from_dict(cls, d: dict) -> "ClassifyResult":
        route = d.get("route", "complex")
        if route not in ("simple", "complex", "swarm"):
            route = "complex"
        return cls(
            effort=int(d.get("effort", 5)),
            tools=int(d.get("tools", 0)),
            domain=str(d.get("domain", "code")),
            parallel=bool(d.get("parallel", False)),
            route=route,  # type: ignore[arg-type]
        )


@dataclass
class RouterConfig:
    enabled: bool = True
    classifier_alias: str = "haiku"
    simple_alias: str = "haiku"           # cheapest model for simple queries
    complex_plan_alias: str = "opus"      # planner for complex pipeline
    complex_execute_alias: str = "sonnet" # executor for complex pipeline
    swarm_worker_alias: str = "haiku"     # each parallel swarm worker
    swarm_merge_alias: str = "sonnet"     # merges swarm outputs
    swarm_workers: int = 3                # parallel agents in a swarm call
    auto_compact_turns: int = 20          # trigger /compact after N turns (0 = off)


def classify(
    query: str,
    config: MowgliConfig,
    classifier_alias: str = "haiku",
) -> ClassifyResult:
    """
    Call the classifier model to score the query.

    Returns ClassifyResult.fallback() on any error (timeout, parse failure).
    """
    spec = config.resolve_model(classifier_alias)
    provider = get_provider(spec.provider)

    args = provider.build_headless_args(
        prompt=_CLASSIFY_PROMPT.format(query=query[:600]),
        model_id=spec.model_id,
        session_id=str(uuid.uuid4()),
        resume=False,
        include_partial=False,
    )

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=20)
        state = StreamState()
        raw_text = ""
        for line in result.stdout.splitlines():
            event = provider.parse_stream_line(line, state)
            if event and event.type == "text_delta":
                raw_text += event.content

        # Extract first JSON object from the response
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw_text[start:end])
            return ClassifyResult.from_dict(data)

        return ClassifyResult.fallback()

    except Exception:
        return ClassifyResult.fallback()
