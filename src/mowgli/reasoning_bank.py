"""
ReasoningBank — lightweight JSONL learning store.

Each turn appends one record:
  {"ts": "...", "domain": "code", "effort": 6, "tools": 3,
   "parallel": false, "route": "complex",
   "model": "sonnet", "cost_usd": 0.0042, "quality": null}

quality is left null at write-time; future tooling (e.g. /rate command) can
backfill it. The bank uses historical records to suggest better routing
thresholds without requiring a vector DB.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

BANK_FILE = Path.home() / ".studio" / "mowgli" / "reasoning_bank.jsonl"
_MAX_RECORDS = 500   # rolling window kept in memory for suggestions


def record(
    *,
    domain: str,
    effort: int,
    tools: int,
    parallel: bool,
    route: str,
    model: str,
    cost_usd: float,
    quality: float | None = None,
) -> None:
    """Append one reasoning record to the bank."""
    BANK_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "effort": effort,
        "tools": tools,
        "parallel": parallel,
        "route": route,
        "model": model,
        "cost_usd": cost_usd,
        "quality": quality,
    }
    with BANK_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def load(limit: int = _MAX_RECORDS) -> list[dict]:
    """Return the most recent *limit* records."""
    if not BANK_FILE.exists():
        return []
    lines = BANK_FILE.read_text().splitlines()
    records = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(records) >= limit:
            break
    return list(reversed(records))


def suggest_model(domain: str, effort: int, config_models: dict) -> str | None:
    """
    Given domain + effort, suggest the best model alias based on history.

    Returns None if insufficient data (< 5 matching records).
    Picks the alias with the highest mean quality (or lowest cost when quality=null).
    """
    history = load()
    matches = [
        r for r in history
        if r.get("domain") == domain and abs(r.get("effort", 0) - effort) <= 2
    ]
    if len(matches) < 5:
        return None

    # Aggregate by model
    scores: dict[str, list[float]] = {}
    for r in matches:
        m = r.get("model")
        if not m or m not in config_models:
            continue
        q = r.get("quality")
        c = r.get("cost_usd", 0.0)
        # Use quality if available, else invert-cost as proxy
        score = q if q is not None else max(0.0, 1.0 - c * 1000)
        scores.setdefault(m, []).append(score)

    if not scores:
        return None

    best = max(scores, key=lambda m: sum(scores[m]) / len(scores[m]))
    return best


def stats() -> dict:
    """Return summary stats for the /bank slash command."""
    records = load()
    if not records:
        return {"total": 0}
    total_cost = sum(r.get("cost_usd", 0.0) for r in records)
    by_model: dict[str, int] = {}
    by_route: dict[str, int] = {}
    for r in records:
        by_model[r.get("model", "?")] = by_model.get(r.get("model", "?"), 0) + 1
        by_route[r.get("route", "?")] = by_route.get(r.get("route", "?"), 0) + 1
    return {
        "total": len(records),
        "total_cost_usd": round(total_cost, 6),
        "by_model": by_model,
        "by_route": by_route,
    }
