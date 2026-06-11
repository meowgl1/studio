---
studio: mowgli
version: 3.0
scope: global
---

# Mowgli Studio — Global Context

Thomas Galindo · AI Engineer · Melbourne AU · mowgli.studio  
Projects: jungle · baloo · bagheera · analyst · mowgli

---

## Core — always loaded

@~/.studio/harness.md
@~/.studio/stack.md
@~/.studio/persona.md
@~/.studio/IGNORE.md

---

## Session protocol

### START — every session
1. **Query RAG** — call `query_studio` MCP tool (Akela) with the current task. Returns relevant rules, skills, stack constraints (~400 tokens instead of ~9000 static lines):
   - `query_studio(task="<describe what you're building or fixing>", project="<project name>")`
   - Fallback (Akela offline): read `~/.studio/rules/` and `~/.studio/skills/` directly.
2. Update `tasks.md` with today's focus (move items to "Doing")
3. Read the 3 most recent files in `.studio/changelog/` → sort by filename (YYYY-MM-DD), take the latest 3
4. Do NOT load `memory/`, `agents/`, `output-styles/` unless the task explicitly needs them

**Agents available** — invoke by name (full specs in RAG):  
`architect` · `tdd-guide` · `performance-optimizer` · `security-reviewer` · `refactor-cleaner` · `code-explorer` · `planner` · `doc-updater` · `code-simplifier`

**Skills available** — invoke by name (full specs in RAG):  
`caveman` · `spec-driven-development` · `webapp-testing` · `tracker` · `multi-agent-patterns` · `docker-patterns` · `backend-patterns` · `frontend-patterns` · `api-design` · `coding-standards` · `git-workflow` · `security-review` · `eval-harness` · `graphify`

### DURING
- **Spec-first:** run `spec-driven-development` skill (query RAG) before any new feature, refactor, or architecture change
- **IGNORE.md:** follow without exception — no override regardless of instruction
- **During session:** after each significant decision, save a memory entry immediately, do not defer
- **Stack:** follow stack.md without exploring alternatives; override only in project context.md

### END — activates on: done · fine · finisci · end session · close · let's stop
1. Summarize session (max 3 bullets)
2. List files changed
3. Ask: "Run `/cost` in Claude Code terminal for exact token count, or press Enter to estimate"
4. Write a `changelog/YYYY-MM-DD.md` entry summarising what was done
5. Move completed tasks in `tasks.md` to "Done" with date

---

## Extension points — local .studio/ structure

Each project's `.studio/STUDIO.md` opens with `@~/.studio/STUDIO.md` to inherit this base.

| File / Folder      | Structure                                       | Purpose                                 | Required      |
|--------------------|-------------------------------------------------|-----------------------------------------|---------------|
| `context.md`       | single file                                     | Identity · architecture · constraints   | **YES**       |
| `tasks.md`         | single file                                     | Current sprint — updated every session  | **YES**       |
| `changelog/`       | folder — one file per session: `YYYY-MM-DD.md` | Session log · cost tracking             | **YES**       |
| `gotchas.md`       | single file                                     | Known traps in this codebase            | add as needed |
| `memory/`          | folder                                          | Facts that persist across sessions      | add as needed |
| `output-styles/`   | folder                                          | Response format preferences             | add as needed |
| `agents/`          | folder                                          | Project-specific subagents              | add as needed |
| `skills/`          | folder                                          | Project-specific skill overrides        | add as needed |
| `mcp.md`           | single file                                     | MCP servers active for this project     | add as needed |

**Global folders** (in `~/.studio/`, shared across all projects):

| Folder / File | Purpose |
|---------------|---------|
| `rules/` | Language and common rules — **in Akela RAG**, query via `query_studio` |
| `contexts/` | Mode-specific behavior — **in Akela RAG**, query via `query_studio` |
| `skills/` | Global skills — **in Akela RAG**, invoke by name |
| `agents/` | Global agents — **in Akela RAG**, invoke by name |
| `hooks/` | Automation hooks config — source: `hooks/hooks.json` |
| `mcp/` | Global MCP connections — source: `mcp/global.json` |
| `mcp.md` | Global MCP reference doc |
| `scripts/` | dashboard.py + hook scripts + lib/ |

### changelog/ — loading rule
At session start: read **only the 3 most recent files** in `changelog/`.
Sort files by name (YYYY-MM-DD.md = chronological order). Take the 3 latest.
Do not load older entries unless explicitly asked.
Multiple sessions same day: append to existing `YYYY-MM-DD.md` with `---` separator.

### mcp.md — structure and setup

`mcp.md` declares which MCP servers this project actively uses. It is a reference doc — not executable config.

```markdown
## MCP — [project name]

| Server   | Why used                        |
|----------|---------------------------------|
| vercel   | deploy + env var management     |
| figma    | design ↔ code sync              |
| supabase | DB inspection during dev        |
```

**Activation:** MCP servers are enabled at the Claude Code level, not here.  
To activate for a project, add to the project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "vercel": { "command": "npx", "args": ["@vercel/mcp-adapter"] }
  }
}
```

See `~/.studio/stack.md` → `## MCP Servers` for the full catalog of available servers and their activation commands.

---

### tasks.md — structure
```
## Doing
- [ ] active item

## Next
- [ ] queued item

## Blocked
- reason if any

## Done — [month]
- [x] completed item
```
Clear "Done" monthly. Archive to `tasks.archive.md` if historical record needed.

---

## Rules for extension points

- Add a folder/file only when there is a real recurring need
- Document each addition in the project's `.studio/STUDIO.md`
- Never create folders outside this list without updating both STUDIO.md files
- `spec-driven-development` skill is the global spec standard — no project-level alternatives

---

## Efficiency rules

- Compressed internal reasoning: no articles, no filler, no pleasantries
- Minimum load at session start: `context.md` + `tasks.md` + 3 latest `changelog/` + **RAG query**
- Check `context.md` and `gotchas.md` before asking clarifying questions
- One task at a time — do not preemptively solve adjacent problems
- Token ceiling: if a task needs more than 3 clarifying turns, ask all questions upfront

---

## Dashboard

```bash
# Show studio state for current project
python3 ~/.studio/scripts/dashboard.py

# Show state for a specific project
python3 ~/.studio/scripts/dashboard.py /path/to/project
```

Requires: `pip install rich`

---

## Hooks — activation

Hooks are defined in `~/.studio/hooks/hooks.json` (studio source of truth).  
The studio manages tool configuration — you never edit tool configs manually.

```bash
# Activate hooks in Claude Code
python3 ~/.studio/scripts/activate.py

# Check status
python3 ~/.studio/scripts/activate.py --status

# Deactivate
python3 ~/.studio/scripts/activate.py --off

# Preview without writing
python3 ~/.studio/scripts/activate.py --dry-run
```

**Architecture:** `activate.py` is the adapter between the studio and the AI tool.  
Future tools (Cursor, Codex, etc.) get their own adapter via `--tool=` flag.  
You configure the studio — the script handles the rest.

---

## Permissions

Enforced by `@~/.studio/settings.json` at tool level — these rules cannot be overridden by instructions.

**Deny (absolute):** `.env*`, `*.pem`, `*.key`, `.git/config`, `secrets/`, `credentials/`  
**Allow (no prompt):** npm · npx · node · git (add/commit/checkout/diff/log) · python · pytest · vitest · tsc · eslint · mkdir · cp · mv  
**Ask (always confirm):** `git push` · `vercel` · `rm -rf`

Once spec and tasks are approved, all allowed operations run without confirmation.
