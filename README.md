# Mowgli Studio

> A personal AI operating system — context management, unified CLI, and tool ecosystem for software projects.

🌍 [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)

![License](https://img.shields.io/github/license/meowgl1/studio)
![Last Commit](https://img.shields.io/github/last-commit/meowgl1/studio)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Code-D4A827?logo=anthropic&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-CLI-4285F4?logo=google&logoColor=white)

<p align="center">
  <img src=".github/assets/hero.png" width="100%" alt="Mowgli Studio">
</p>

---

## What it is

Mowgli Studio is two things that work together:

**`.studio/`** — A structured folder of markdown files that gives any AI coding assistant a consistent, layered understanding of how you work before it writes a single line of code. Engineering standards, tech decisions, skills, agents, and session protocol — all in one place, inherited by every project.

**`mowgli`** — A unified CLI that wraps Claude Code, Gemini CLI, and future providers behind a single interactive REPL. Switch models mid-session, chain providers in pipelines, manage MCP servers, and track session cost — all from one interface.

Neither is a framework. Neither requires a running service. Both are files and scripts you own entirely.

---

## What's new in v2.3

- **Mowgli CLI** — full interactive REPL with multi-provider support, cross-model pipelines, and MCP management
- **Graphify skill** — build and query codebase knowledge graphs (71x fewer tokens per query)
- **Obsidian MCP** — read and write your vault directly from any AI session
- **`mowgli mcp on/off`** — toggle MCP servers at runtime without touching config files
- **Waiting spinner** — visual feedback while the model is thinking

---

## The `.studio` context system

Every AI session begins with a cascade:

```
project/CLAUDE.md  (or GEMINI.md, .cursorrules)
  └── @.studio/STUDIO.md              ← project-level context
        └── @~/.studio/STUDIO.md      ← global standards
              ├── harness.md           ← 5 engineering absolutes
              ├── stack.md             ← technology decisions (final)
              ├── persona.md           ← communication contract
              ├── IGNORE.md            ← files never to touch
              ├── rules/               ← language and common rules
              ├── contexts/            ← mode-specific behavior
              ├── skills/              ← reusable procedures
              └── agents/              ← specialized subagents
```

The AI tool reads the entry file, expands all `@` references in sequence, and arrives at your first message already knowing your engineering standards, tech stack, active rules, and session protocol.

The global `~/.studio/` applies to every project. Each project's `.studio/` inherits from the global and adds its own context — architecture, current sprint, known traps.

---

## The `mowgli` CLI

```bash
mowgli                          # open interactive REPL
mowgli -m opus                  # start with a specific model
mowgli -p "explain this code"   # headless, single prompt

mowgli models                   # list available models
mowgli mcp                      # list MCP servers (on/off)
mowgli mcp on obsidian          # enable a server
mowgli mcp off notebooklm       # disable a server
```

Inside the REPL, slash commands control the session:

```
/model gemini-pro     switch model mid-session (new context)
/models               list all models
/mcp                  list MCP servers
/mcp on <name>        enable a server
/cost                 show session spend
/compact              summarize and compress context
/clear                start a new session
/help                 all commands
/exit                 quit
```

### Multi-model pipelines

Chain providers to optimize cost and quality — use the expensive model only where it matters:

```bash
# Plan with Opus, execute with Gemini (~70% cheaper on execution)
mowgli pipe --plan opus --execute gemini-pro "build a REST API for user auth"

# Plan → Execute → Review
mowgli pipe --plan opus --execute gemini-pro --review sonnet "refactor the payment service"
```

### Models

| Alias | Provider | Best for |
|-------|----------|----------|
| `opus` | Claude | Architecture, complex reasoning, security review |
| `sonnet` | Claude | General coding, balanced cost/quality |
| `haiku` | Claude | Fast edits, simple questions |
| `gemini-pro` | Gemini | Execution, long context, lower cost |
| `gemini-lite` | Gemini | Bulk tasks, draft generation |

---

## Tool ecosystem

Three tools that address different layers of the coding workflow:

| Tool | Integration | Layer | When to use |
|------|------------|-------|-------------|
| **Graphify** | Skill (`/graphify`) | Code understanding | "How does auth work?", onboarding a new codebase, PR impact analysis |
| **Obsidian** | MCP server | Human knowledge | Read specs, write decision logs, query meeting notes |
| **Higgsfield** | Claude plugin | Media generation | Demo videos, product images, marketing clips |

Workflow: **Obsidian** (read the spec) → **Graphify** (understand the code) → implement → **Higgsfield** (make the demo) → **Obsidian** (write the decision log).

### Graphify

Scans any codebase — code, docs, PDFs, images — and builds a persistent JSON knowledge graph with community detection. Subsequent queries use the graph instead of raw files (71x fewer tokens).

```bash
/graphify                           # build graph for current directory
/graphify query "how does X work"   # query an existing graph
/graphify path "AuthModule" "DB"    # shortest path between two concepts
/graphify --obsidian                # export graph as Obsidian vault
/graphify --update                  # incremental rebuild on changed files
```

### Obsidian MCP (MCPVault)

Reads and writes markdown files directly from your vault without Obsidian open. Available in every Claude Code and Gemini session.

```bash
mowgli mcp on obsidian    # enable
mowgli mcp off obsidian   # disable
```

---

## Skills

Reusable procedures invoked by name. Loaded on demand, not at startup.

| Skill | Purpose |
|-------|---------|
| `spec-driven-development` | Spec-first workflow — mandatory before any new feature |
| `graphify` | Build and query codebase knowledge graphs |
| `readme-craft` | Create, audit, or improve README files |
| `webapp-testing` | Playwright E2E testing setup and patterns |
| `backend-patterns` | API design, service layer, repository, auth, caching |
| `frontend-patterns` | Next.js App Router, Server Components, data fetching |
| `docker-patterns` | Multi-stage builds, Compose, security hardening |
| `api-design` | REST conventions, response format, pagination, versioning |
| `coding-standards` | Linting setup, pre-commit hooks, CI enforcement |
| `git-workflow` | Branching strategy, commit discipline, PR process |
| `security-review` | OWASP checklist — run before merging auth/payment code |
| `eval-harness` | Build evaluation harnesses for AI/LLM features |
| `multi-agent-patterns` | When and how to spawn subagents |
| `caveman` | Minimal, dependency-free scripting patterns |
| `tracker` | Session cost and token logging |

---

## Agents

Specialized subagents invoked by name:

| Agent | Purpose |
|-------|---------|
| `architect` | System design, ADRs, trade-off analysis |
| `planner` | Break requirements into phased implementation plans |
| `tdd-guide` | Test-first enforcement |
| `performance-optimizer` | N+1 queries, slow endpoints, bundle bloat |
| `security-reviewer` | Security audits and incident response |
| `refactor-cleaner` | Improve structure without changing behavior |
| `code-explorer` | Map unfamiliar codebases |
| `code-simplifier` | Remove premature abstractions |
| `doc-updater` | Keep context.md, gotchas.md, and README in sync |

---

## Hooks

Automation managed via `hooks/hooks.json`, applied with `activate.py`:

| Hook | Trigger | What it does |
|------|---------|-------------|
| `quality-gate` | After Edit/Write | Runs ruff or tsc on edited file |
| `gateguard` | Before Edit/Write | Blocks blind edits — forces Read first |
| `cost-tracker` | After each response | Tracks token usage |
| `desktop-notify` | After each response | macOS notification on completion |
| `read-tracker` | After Read | Records files read for gateguard |

---

## Project structure

### Global (`~/.studio/`)

| File / Folder | Purpose |
|--------------|---------|
| `STUDIO.md` | Entry point — references all global files, defines session protocol |
| `harness.md` | Five engineering absolutes |
| `stack.md` | Technology decisions — final, not suggestions |
| `persona.md` | Communication contract |
| `IGNORE.md` | Files the AI must never modify |
| `rules/` | Enforceable coding standards by language and scope |
| `contexts/` | Mode-specific behavior: `dev`, `research`, `review` |
| `skills/` | Global skills |
| `agents/` | Global agents |
| `hooks/` | Hook definitions |
| `mcp/` | MCP server config (`global.json` is source of truth) |
| `src/mowgli/` | The Mowgli CLI package |

### Per-project (`.studio/` in each repo)

| File / Folder | Purpose | Required |
|--------------|---------|---------|
| `STUDIO.md` | Inherits global, adds project overrides | ✅ |
| `context.md` | Architecture, constraints, active feature status | ✅ |
| `tasks.md` | Current sprint: Doing / Next / Blocked | ✅ |
| `changelog/` | One file per session (`YYYY-MM-DD.md`) | ✅ |
| `gotchas.md` | Known traps in this codebase | 🔶 |
| `mcp.md` | MCP servers active for this project | 🔶 |
| `memory/` | Facts that persist across sessions | 🔶 |

---

## Why AI-agnostic

Claude Code reads `CLAUDE.md`. Gemini CLI reads `GEMINI.md`. Cursor reads `.cursorrules`.

`.studio/` sits underneath all of them:

```markdown
# CLAUDE.md
@.studio/STUDIO.md
```

When you switch AI tools, you update one line. Standards, decisions, and project context stay exactly as they are.

---

## The vision

The real problem isn't picking the right AI tool. It's that every tool treats you as a new user every session. You re-explain the stack, re-state the constraints, re-describe the architecture. The AI produces technically correct code that violates decisions you made three sessions ago — not because the model is bad, but because you never gave it the memory to act consistently.

Mowgli Studio addresses this at three layers:

- **Context** (`.studio/`) — the AI knows your standards and current state before you say a word
- **Interface** (`mowgli`) — one entry point regardless of which provider you use today
- **Tools** (skills + MCP) — code knowledge, personal knowledge, and creative output available in every session

This turns a collection of AI tools into a coherent system you control. Not a product you adapt to — a system you own.

---

## Token cost

Global context at session start: approximately **8,000–10,000 tokens** (~4–5% of a 200K window).

Kept low by: imperative rules over prose, on-demand skill loading, 3-file changelog limit, operational `context.md` instead of documentation.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/meowgl1/studio ~/.studio
pip install rich

# Install the mowgli CLI
pip install -e ~/.studio
```

### 2. Configure

```bash
nano ~/.studio/stack.md    # set your technology decisions
nano ~/.studio/persona.md  # set communication preferences
```

### 3. Activate hooks and MCP

```bash
python3 ~/.studio/scripts/activate.py

# Check status
python3 ~/.studio/scripts/activate.py --status
```

### 4. Wire up a project

```bash
mkdir your-project/.studio

echo "@~/.studio/STUDIO.md" > your-project/.studio/STUDIO.md
echo "@.studio/STUDIO.md"   > your-project/CLAUDE.md

touch your-project/.studio/context.md
touch your-project/.studio/tasks.md
mkdir  your-project/.studio/changelog
```

Fill `context.md` with architecture, stack overrides, and constraints.

### 5. Run

```bash
# Dashboard
python3 ~/.studio/scripts/dashboard.py

# Interactive AI session
mowgli

# With a specific model
mowgli -m gemini-pro
```

---

## Harness Engineering

The five rules in `harness.md` that separate production AI systems from demos:

1. **Schema-first** — LLM output validated with Pydantic or Zod before any operation
2. **Evals-driven** — no prompt ships without a golden dataset
3. **Context engineering** — raw unprocessed content never reaches the LLM
4. **Failure-aware design** — exception chaining, retry with backoff, partial result recovery
5. **Observability** — every LLM call logged: model, tokens, latency, cost

---

## Acknowledgment

The context system was informed by **[ECC](https://github.com/affaan-m/ECC)** by [@affaan-m](https://github.com/affaan-m), which demonstrated what a fully operational AI context system looks like at scale. This project took a leaner, more personal direction, but ECC's architecture shaped the rules system, context modes, and agent design.

---

## License

MIT
