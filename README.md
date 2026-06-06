# .studio

> An AI-agnostic context management system for software projects.

🌍 [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)

---

## 🧠 What it is

`.studio` is a structured folder of markdown files that gives any AI coding assistant — Claude Code, Gemini CLI, Cursor, or anything else — a consistent, layered understanding of how you work before it writes a single line of code.

It is not a plugin. It is not a framework. It is a set of files.

---

## 🙏 Acknowledgment

The v2.0 expansion of this system was informed by **[ECC](https://github.com/affaan-m/ECC)** by [@affaan-m](https://github.com/affaan-m), winner of the Claude hackathon. ECC demonstrated what a fully operational AI context system looks like at scale — 97 agents, 300+ skills, 20+ hooks, and cross-tool support across 7 AI platforms.

This project took a different direction: instead of a large, CLI-heavy system, `.studio` adapts ECC's most valuable patterns into a lean, Python-native, AI-agnostic layer. The rules architecture, context modes, hook infrastructure, and agent design were all shaped by studying ECC's approach.

---

## ⚙️ How it works

Every AI session in a project begins with a cascade:

```
project/CLAUDE.md (or GEMINI.md, .cursorrules, etc.)
  └── @.studio/STUDIO.md              ← project-level context
        └── @~/.studio/STUDIO.md      ← global standards
              ├── harness.md           ← engineering rules
              ├── stack.md             ← technology decisions
              ├── persona.md           ← communication style
              ├── IGNORE.md            ← files never to touch
              ├── evals.md             ← agent success metrics
              ├── rules/               ← language and common rules
              ├── contexts/            ← mode-specific behavior
              ├── skills/              ← reusable procedures
              └── agents/              ← specialized subagents
```

The AI tool reads the entry file, which expands all `@` references in sequence. By the time the model reads your first message, it already knows your engineering standards, tech stack, active rules, and how you prefer to communicate.

The global `~/.studio/` applies to every project on your machine. Each project's `.studio/` inherits from the global and adds its own context — architecture, current sprint, known traps.

---

## 🗂️ Structure

### Global (`~/.studio/`)

#### 📌 Standards

| File | Purpose |
|------|---------|
| `STUDIO.md` | Entry point. References all global files. Defines session protocol, extension points, available agents and skills. |
| `harness.md` | Five engineering absolutes: schema-first, evals-driven, context engineering, failure-aware, observability. |
| `stack.md` | Technology decisions — final, not suggestions. Python, TypeScript, Next.js, Supabase. No LangChain. |
| `persona.md` | Communication contract. Direct, code-first, no pleasantries, Italian or English per session. |
| `IGNORE.md` | Files the AI must never modify: `.env*`, `.git/`, build artifacts, migrations. |
| `evals.md` | How to know if agents are succeeding. Session logging rules. |

#### 📏 Rules (`rules/`)

Enforceable coding standards loaded every session. Organized by scope:

| Folder | Contents |
|--------|---------|
| `rules/common/` | `clean-code` · `clean-architecture` · `testing` · `performance` · `patterns` · `security` · `llm-security` · `git` · `hooks` |
| `rules/python/` | `coding-style` · `patterns` · `testing` · `security` · `fastapi` |
| `rules/js/` | `coding-style` · `patterns` · `testing` · `security` · `react` |
| `rules/sql/` | `coding-style` · `patterns` · `security` |

#### 🎭 Contexts (`contexts/`)

Mode-specific behavior files. Load the one that matches your current activity:

| File | When to use |
|------|------------|
| `contexts/dev.md` | Actively building or fixing code |
| `contexts/research.md` | Investigating a codebase or problem |
| `contexts/review.md` | Reviewing a PR or auditing code |

Each context file activates the relevant rules and defines the appropriate behavior for that mode.

#### 🛠️ Skills (`skills/`)

Reusable procedures invoked by name during sessions:

| Skill | Purpose |
|-------|---------|
| `spec-driven-development` | Spec-first workflow — mandatory before any new feature |
| `webapp-testing` | Playwright E2E testing setup and patterns |
| `backend-patterns` | API design, service layer, repository, auth, caching |
| `frontend-patterns` | Next.js App Router, Server Components, data fetching |
| `docker-patterns` | Multi-stage builds, Compose for local dev, security hardening |
| `api-design` | REST conventions, response format, pagination, versioning |
| `coding-standards` | Linting setup, pre-commit hooks, CI enforcement |
| `git-workflow` | Branching strategy, commit discipline, PR process |
| `security-review` | OWASP checklist — run before merging auth/payment code |
| `eval-harness` | Build evaluation harnesses for AI/LLM features |
| `tracker` | Session cost and token logging |
| `caveman` | Minimal, dependency-free scripting patterns |
| `multi-agent-patterns` | When and how to spawn subagents — handoff templates, parallel rules, anti-patterns |

#### 🤖 Agents (`agents/`)

Specialized subagents invoked by name. Each has a defined role and output format:

| Agent | Purpose |
|-------|---------|
| `architect` | System design, ADRs, trade-off analysis, scalability planning |
| `planner` | Break requirements into phased implementation plans |
| `tdd-guide` | Test-first enforcement — writes tests before implementation |
| `performance-optimizer` | Find and fix N+1 queries, slow endpoints, bundle bloat |
| `security-reviewer` | Security incident response and deep audits |
| `refactor-cleaner` | Improve structure without changing behavior |
| `code-explorer` | Map unfamiliar codebases — entry points, patterns, gotchas |
| `code-simplifier` | Remove premature abstractions and unnecessary complexity |
| `doc-updater` | Keep context.md, gotchas.md, and README in sync with code |

#### 🪝 Hooks (`hooks/`, `scripts/`)

Automation that runs around your AI sessions:

| Hook | Trigger | What it does |
|------|---------|-------------|
| `session-start` | Session opens | Detects active project, loads prior state |
| `pre-compact` | Before context compaction | Saves session state — nothing lost |
| `session-end` | After each response | Persists edited files and session data |
| `cost-tracker` | After each response | Tracks token usage and context window utilization |
| `desktop-notify` | After each response | macOS notification when Claude finishes |
| `read-tracker` | After Read | Records every file read — gateguard uses this to allow subsequent edits |
| `quality-gate` | After Edit/Write | Runs ruff or tsc on the file just edited |
| `gateguard` | Before Edit/Write | Blocks blind edits — forces Read first |

All hooks are defined in `hooks/hooks.json` (studio source of truth) and applied to AI tools via the activation script — never by editing tool configs manually.

#### 📊 Dashboard (`scripts/dashboard.py`)

Terminal overview of your studio and active project:

```
╭──────────────── Studio Dashboard ────────────────╮
│ jungle  /Projects/jungle  2026-06-03 21:00       │
╰──────────────────────────────────────────────────╯
  Tasks: 2 doing · 3 next
  Changelog: last 3 sessions
  Sessions: cost tracking per project
  Skills: 13 loaded
  Agents: 9 available
  Hooks: ✓ active
```

### Project-level (`.studio/` in each repo)

| File / Folder | Purpose | Required |
|---------------|---------|---------|
| `STUDIO.md` | Opens with `@~/.studio/STUDIO.md`. Adds project overrides. | ✅ Yes |
| `context.md` | Architecture, constraints, active feature status. Not documentation — what the AI needs to act correctly. | ✅ Yes |
| `tasks.md` | Current sprint: Doing / Next / Blocked. Updated every session. | ✅ Yes |
| `changelog/` | One file per session (`YYYY-MM-DD.md`). What was done, files changed, token cost. 3 most recent loaded at start. | ✅ Yes |
| `gotchas.md` | Known traps in this codebase. Read before executing. | 🔶 As needed |
| `memory/` | Facts that persist across sessions. | 🔶 As needed |
| `agents/` | Project-specific agent overrides. | 🔶 As needed |
| `skills/` | Project-specific skill overrides. | 🔶 As needed |
| `mcp.md` | MCP servers active for this project. | 🔶 As needed |

---

## 🌐 Why AI-agnostic

Claude Code reads `CLAUDE.md`. Gemini CLI reads `GEMINI.md`. Cursor reads `.cursorrules`. Each tool has its own entry file.

`.studio/` sits underneath all of them. The entry files are thin wrappers:

```markdown
# CLAUDE.md
@.studio/STUDIO.md
```

When you switch AI tools, you update one line. Your engineering standards, tech decisions, and project context stay exactly as they are.

The hooks and dashboard are currently adapted for Claude Code. The architecture is designed for additional adapters — see `scripts/activate.py --tool=`.

---

## 💰 Token cost

Loading the full global context at session start costs approximately **8,000–10,000 tokens** — around 4–5% of a 200K context window.

The design keeps this low by:
- Using imperatives, not prose — rules load fast, explanations don't
- Loading skills on-demand, not at startup
- Limiting changelog to 3 most recent files
- Keeping `context.md` focused on operational state, not documentation

---

## 🔄 The session protocol

Every session follows three phases:

**▶ START** — Load `tasks.md` + 3 most recent `changelog/` files. Load context mode (dev / research / review). Know scope before touching anything.

**⚡ DURING** — Spec-first: no new feature without an approved spec. IGNORE.md: no exceptions. Stack: follow decisions, don't explore alternatives. Rules: enforced by context mode.

**⏹ END** — Summary, files changed, token cost. Changelog entry written. Tasks updated.

---

## 🏗️ Harness Engineering

The five rules in `harness.md` encode what separates production AI systems from demos:

1. **🔷 Schema-first** — LLM output validated with Pydantic or Zod before any operation.
2. **🔷 Evals-driven** — No prompt ships without running against a golden dataset.
3. **🔷 Context engineering** — Raw unprocessed content never reaches the LLM. Filter first.
4. **🔷 Failure-aware design** — Exception chaining, retry with backoff, partial result recovery.
5. **🔷 Observability** — Every LLM call logged: model, tokens, latency, cost.

---

## 🚀 Setup

### 1. Install global studio

```bash
git clone https://github.com/meowgl1/studio ~/.studio
pip install rich   # for the dashboard
```

### 2. Configure for your stack

```bash
# Edit tech decisions
nano ~/.studio/stack.md

# Edit communication preferences  
nano ~/.studio/persona.md
```

### 3. Activate hooks (Claude Code)

```bash
python3 ~/.studio/scripts/activate.py

# Check status
python3 ~/.studio/scripts/activate.py --status

# Remove hooks
python3 ~/.studio/scripts/activate.py --off
```

### 4. Wire up a project

```bash
mkdir your-project/.studio

# Entry file — one line
echo "@~/.studio/STUDIO.md" > your-project/.studio/STUDIO.md

# Project entry for Claude Code — one line  
echo "@.studio/STUDIO.md" > your-project/CLAUDE.md

# Create required files
touch your-project/.studio/context.md
touch your-project/.studio/tasks.md
mkdir your-project/.studio/changelog
```

Fill `context.md` with your project's architecture, stack overrides, and constraints.  
Fill `tasks.md` with current sprint items.

### 5. Run the dashboard

```bash
# From your project directory
python3 ~/.studio/scripts/dashboard.py

# Or from anywhere
python3 ~/.studio/scripts/dashboard.py /path/to/project
```

---

## 💬 Personal opinion

I built this because I kept losing context.

Every new Claude Code session started from zero. I re-explained the stack, re-stated the constraints, re-described the architecture. The AI produced technically correct code that violated decisions I had made three sessions earlier — not because the model was bad, but because I never gave it the memory it needed to act consistently.

The standard advice is "just write a good CLAUDE.md." I tried that. The problem is that a good CLAUDE.md for one project becomes a different document from a good CLAUDE.md for another project, and neither survives tool changes. Every update was a tax.

`.studio` solves this by separating what is stable (engineering standards, technology decisions, communication preferences) from what changes (current tasks, recent sessions, project state). The stable parts live globally and never need to be rewritten.

The other thing I got wrong before: I thought the AI needed documentation. It doesn't. It needs rules. Long explanations about why we use Pydantic are wasted tokens. "ALWAYS validate LLM output with Pydantic before any DB operation" is not. The shift from documentation to imperatives cut my session start context by roughly 40% while making the AI's behavior more consistent, not less.

This is a living system. I add a gotcha when I hit a recurring bug. I add a memory file when agents start losing important state. I add a skill when I find myself repeating the same instruction across sessions. The overhead of maintaining it is lower than the overhead of not having it.

---

## 📜 License

MIT. Use it, adapt it, break it into pieces and take what's useful.
