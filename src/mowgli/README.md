# Mowgli CLI

**A multi-provider, routing-aware CLI for Claude and Gemini — built for developers who think in terminals.**

Mowgli wraps Claude Code and Gemini CLI behind a unified interface with automatic model routing, parallel swarm execution, and a lightweight learning store that improves routing over time.

```
███╗   ███╗ ██████╗ ██╗    ██╗ ██████╗ ██╗     ██╗
████╗ ████║██╔═══██╗██║    ██║██╔════╝ ██║     ██║
██╔████╔██║██║   ██║██║ █╗ ██║██║  ███╗██║     ██║
██║╚██╔╝██║██║   ██║██║███╗██║██║   ██║██║     ██║
██║ ╚═╝ ██║╚██████╔╝╚███╔███╔╝╚██████╔╝███████╗██║
╚═╝     ╚═╝ ╚═════╝  ╚══╝╚══╝  ╚═════╝ ╚══════╝╚═╝
```

---

## Features

| Feature | Description |
|---|---|
| **Multi-provider** | Claude (Opus / Sonnet / Haiku) + Gemini (Pro / Flash) unified under one REPL |
| **Smart router** | Multi-dimensional classifier scores every query on effort, tool count, domain, and parallelism — then dispatches to the right model automatically |
| **Swarm fan-out** | Complex parallelisable tasks are split across N concurrent workers then merged — inspired by Ruflo's swarm coordination patterns |
| **ReasoningBank** | JSONL learning store records every turn (model used, cost, domain, route). Builds routing suggestions from your own history |
| **PII scrubber** | API keys, JWTs, emails, AWS credentials redacted before any provider dispatch |
| **ESC cancellation** | Press ESC mid-response to interrupt; prompt is restored for editing |
| **Session continuity** | `--resume` keeps conversation context across turns; `/clear` starts fresh |
| **Auto-compact** | Configurable turn threshold triggers automatic context compression |
| **MCP server control** | `/mcp on|off <name>` toggle MCP servers at runtime |
| **Cost tracking** | Per-turn and session-total cost shown inline |

---

## Installation

Mowgli requires [Claude Code CLI](https://claude.ai/code) and optionally [Gemini CLI](https://github.com/google-gemini/gemini-cli).

```bash
# From the studio repo root
pip install -e src/mowgli

# Or with uv
uv pip install -e src/mowgli
```

Then:

```bash
mowgli          # interactive REPL
mowgli -m opus  # start with a specific model
mowgli -p "explain this codebase"  # headless / pipe mode
```

---

## Supported models

| Alias | Provider | Model ID | Best for |
|---|---|---|---|
| `opus` | Claude | claude-opus-4-6 | Architecture, deep reasoning, planning |
| `sonnet` | Claude | claude-sonnet-4-6 | Code execution, multi-file edits |
| `haiku` | Claude | claude-haiku-4-5 | Fast answers, classification, simple tasks |
| `gemini-pro` | Gemini | gemini-2.5-pro | Long context, analysis |
| `gemini-lite` | Gemini | gemini-2.5-flash | Cheap, fast — great as `simple_alias` in router |

Override defaults in `~/.studio/mowgli/models.json`:

```json
{
  "default_model": "sonnet",
  "models": {
    "my-local": {
      "alias": "my-local",
      "provider": "gemini",
      "model_id": "gemini-2.5-flash",
      "cli_binary": "/usr/local/bin/gemini"
    }
  }
}
```

---

## Router

Every query is classified before dispatch. The classifier (Haiku by default) returns a JSON score:

```json
{ "effort": 7, "tools": 4, "domain": "architectural", "parallel": true, "route": "swarm" }
```

### Routing rules

```
effort ≤ 4 AND tools ≤ 1        →  simple   →  haiku (or gemini-lite)
effort ≥ 7 AND parallel == true  →  swarm    →  N × haiku fan-out → sonnet merge
everything else                  →  complex  →  plan:opus → execute:sonnet
```

### Router controls

```
/router          show current config
/router on       enable auto-routing
/router off      use session model directly (no routing)
```

To use Gemini Flash for simple queries (much cheaper):

```python
# In ~/.studio/mowgli/models.json, set default simple_alias
# Or at runtime via code: router.simple_alias = "gemini-lite"
```

---

## Swarm

Swarm distributes a task across N parallel agents then merges results with a synthesis model. Designed for tasks that can be decomposed into independent subtasks: writing tests for multiple modules, translating a codebase, reviewing different files.

```
/swarm write tests for every public function in src/mowgli/
/swarm 5 translate all UI strings to French
```

Automatic swarm routing triggers when the classifier returns `parallel: true` and `effort >= 7`.

### How it works

```
Task
 │
 ├─ Decomposer (haiku)  →  ["sub-task 1", "sub-task 2", "sub-task 3"]
 │
 ├─ Worker 1 (haiku) ─┐
 ├─ Worker 2 (haiku) ─┼─ parallel threads
 └─ Worker 3 (haiku) ─┘
                       │
                 Merge (sonnet)  →  final output
```

Worker count defaults to 3. Override:

```
/swarm 5 <prompt>    — 5 workers
```

---

## ReasoningBank

Every completed turn is logged to `~/.studio/mowgli/reasoning_bank.jsonl`:

```jsonl
{"ts": "2026-06-12T...", "domain": "code", "effort": 3, "tools": 0, "parallel": false, "route": "simple", "model": "haiku", "cost_usd": 0.0002}
{"ts": "2026-06-12T...", "domain": "architectural", "effort": 8, "tools": 5, "parallel": true, "route": "swarm", "model": "sonnet", "cost_usd": 0.0089}
```

View stats:

```
/bank
```

When ≥5 records exist for a given domain+effort pair, the bank suggests the historically best-performing model for that profile — automatically fed into future routing decisions.

---

## PII Scrubber

All prompts pass through a redaction pipeline before reaching any provider. Patterns covered:

- OpenAI / Anthropic / Google API keys
- AWS Access Key ID + Secret
- GitHub tokens (`ghp_`, `gho_`, `github_pat_`)
- Bearer tokens + JWTs
- PEM private key blocks
- Email addresses
- High-entropy hex secrets (32+ chars)

Redactions are shown inline:

```
  ⚠ PII redacted: anthropic_key, email
```

---

## Slash commands

| Command | Description |
|---|---|
| `/model <alias>` | Switch model (starts new session) |
| `/models` | List all available models |
| `/clear` | Start new session (clears context) |
| `/cost` | Show session total cost |
| `/compact` | Summarise context, reset session with summary |
| `/router [on\|off]` | Toggle or inspect auto-routing |
| `/swarm [N] <prompt>` | Fan-out to N workers then merge |
| `/bank` | ReasoningBank stats |
| `/refine [N]` | Iteratively refine last response |
| `/mcp` | List MCP servers |
| `/mcp on\|off <name>` | Toggle MCP server at runtime |
| `/game` | Pixel dino game (SPACE to jump) |
| `/exit` or `/quit` | End session |

**Input tips:** `Enter` to submit · `Alt+Enter` for newline · `↑↓` navigate within text · `ESC` cancel mid-response

---

## Architecture

```
mowgli/
├── cli.py            — Click entry point, headless/pipe mode
├── repl.py           — MowgliREPL main loop, turn execution, slash commands
├── router.py         — Multi-dimensional classifier, RouterConfig
├── swarm.py          — Parallel fan-out + merge (Ruflo-inspired)
├── reasoning_bank.py — JSONL learning store
├── pii_scrubber.py   — Regex redaction pipeline
├── config.py         — ModelSpec, MowgliConfig, model registry
├── branding.py       — Logo, banner, /help output
├── game.py           — Pixel dino easter egg
├── mcp_manager.py    — MCP server enable/disable
└── providers/
    ├── base.py       — Provider protocol, StreamState, StreamEvent
    ├── claude.py     — ClaudeProvider (Claude Code CLI wrapper)
    └── gemini.py     — GeminiProvider (Gemini CLI wrapper)
```

---

## Comparison with Ruflo

[Ruflo](https://github.com/ruvnet/ruflo) is an enterprise-grade multi-agent swarm framework. Mowgli is a personal developer CLI. They solve different problems at different scales — but Ruflo's architecture contains several patterns that informed Mowgli v2.4.

| Aspect | Ruflo | Mowgli |
|---|---|---|
| **Target** | Enterprise distributed systems | Single developer / small team |
| **Swarm** | Hierarchical / Mesh / Adaptive topologies, Byzantine consensus, Raft | Threaded fan-out + merge (lightweight) |
| **Routing** | SONA self-organizing neural patterns, HNSW vector search | Multi-dimensional JSON classifier + JSONL history |
| **Memory** | AgentDB (vector DB), ReasoningBank (trajectory learning) | JSONL ReasoningBank (zero infrastructure) |
| **Context** | Semantic compression distributed across agents | `/compact` + auto-compact at configurable turn threshold |
| **Security** | mTLS, ed25519 identity, PII pipeline, zero-trust | Regex PII scrubber before dispatch |
| **Provider support** | 33+ MCP plugins, OpenAI / Claude / Gemini / Cohere / Ollama | Claude Code CLI + Gemini CLI |
| **Operational overhead** | High (vector DB, background workers, dashboards) | Zero (JSONL files, no daemon) |
| **Setup** | Infrastructure required | `pip install -e .` |
| **Streaming** | Event-driven | Direct subprocess streaming to terminal |

### What Mowgli borrowed from Ruflo

1. **Swarm fan-out pattern** — the decompose → parallel workers → merge topology comes directly from Ruflo's swarm coordination research. Mowgli's implementation drops the consensus layer (not needed for single-node use) but keeps the core fan-out structure.

2. **Multi-dimensional task scoring** — Ruflo's routing evaluates tasks on multiple axes before model selection. Mowgli's classifier prompt was redesigned around this insight: effort, tool count, domain, and parallelism replace the old binary SIMPLE/COMPLEX classification.

3. **ReasoningBank** — Ruflo stores reasoning trajectories to improve future routing. Mowgli's JSONL bank is the same concept without the vector DB dependency: log what worked, surface it as a suggestion when the same profile recurs.

4. **PII pipeline** — Ruflo runs redaction before every agent dispatch. Copied directly into Mowgli's scrubber.

### What Mowgli deliberately did not adopt

- **Distributed consensus (Raft/BFT)** — correct for multi-node systems; unnecessary overhead for a single terminal session.
- **HNSW vector DB** — powerful for semantic agent search at scale; overkill when you have 5 models and flat config files.
- **Background workers** — Ruflo runs 12 continuous optimization tasks. Mowgli is a CLI: it should start fast, do work, exit. No daemons.
- **Web dashboard** — Ruflo provides real-time swarm monitoring UI. Mowgli's monitoring is inline in the terminal.

---

## Credits

- **[Ruflo](https://github.com/ruvnet/ruflo)** by [@ruvnet](https://github.com/ruvnet) — swarm coordination architecture, multi-dimensional routing, ReasoningBank concept, and PII pipeline pattern. Substantial inspiration for Mowgli v2.4.
- **[Claude Code](https://claude.ai/code)** — the underlying engine for Claude provider calls.
- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)** — Gemini provider subprocess.
- **[Rich](https://github.com/Textualize/rich)** + **[prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)** — terminal UI.

---

## License

Part of [mowgli.studio](https://mowgli.studio). See root `LICENSE`.
