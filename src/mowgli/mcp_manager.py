from __future__ import annotations
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

GLOBAL_JSON = Path.home() / ".studio" / "mcp" / "global.json"
ACTIVATE_PY = Path.home() / ".studio" / "scripts" / "activate.py"


@dataclass
class MCPServer:
    name: str
    command: str
    args: list[str]
    enabled: bool


def list_servers() -> list[MCPServer]:
    """Return all known MCP servers (active + disabled)."""
    data = _read()
    result = []
    for name, spec in data.get("servers", {}).items():
        if name.startswith("_"):
            continue
        result.append(MCPServer(
            name=name,
            command=spec.get("command", ""),
            args=spec.get("args", []),
            enabled=True,
        ))
    for name, spec in data.get("_disabled_servers", {}).items():
        if name.startswith("_"):
            continue
        result.append(MCPServer(
            name=name,
            command=spec.get("command", ""),
            args=spec.get("args", []),
            enabled=False,
        ))
    return sorted(result, key=lambda s: s.name)


def enable_server(name: str) -> str:
    """Move server from _disabled_servers to servers. Returns status message."""
    data = _read()
    disabled = data.setdefault("_disabled_servers", {})
    servers = data.setdefault("servers", {})

    if name in servers:
        return f"'{name}' is already enabled."

    if name not in disabled:
        return f"Unknown server '{name}'. Known: {', '.join({**servers, **disabled})}."

    servers[name] = disabled.pop(name)
    _write(data)
    _sync()
    return f"✓ '{name}' enabled and synced."


def disable_server(name: str) -> str:
    """Move server from servers to _disabled_servers. Returns status message."""
    data = _read()
    disabled = data.setdefault("_disabled_servers", {})
    servers = data.setdefault("servers", {})

    if name in disabled:
        return f"'{name}' is already disabled."

    if name not in servers:
        return f"Unknown server '{name}'. Known: {', '.join({**servers, **disabled})}."

    disabled[name] = servers.pop(name)
    _write(data)
    _sync()
    return f"✓ '{name}' disabled and synced."


# ─── Internals ────────────────────────────────────────────────────────────────

def _read() -> dict:
    if not GLOBAL_JSON.exists():
        raise FileNotFoundError(f"MCP config not found: {GLOBAL_JSON}")
    return json.loads(GLOBAL_JSON.read_text())


def _write(data: dict) -> None:
    GLOBAL_JSON.write_text(json.dumps(data, indent=2))


def _sync() -> None:
    """Refresh Claude settings: deactivate then reactivate MCP."""
    if not ACTIVATE_PY.exists():
        return
    py = ["python3", str(ACTIVATE_PY)]
    subprocess.run(py + ["--off"], capture_output=True)
    subprocess.run(py + ["--mcp-only"], capture_output=True)
