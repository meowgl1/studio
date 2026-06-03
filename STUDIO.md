---
studio: mowgli
version: 2.0
scope: global
---

# Mowgli Studio — Global Context

Thomas Galindo · AI Engineer · Melbourne AU · mowgli.studio  
Projects: jungle · baloo · bagheera · analyst · mowgli

---

## Load — global standards

@~/.studio/harness.md
@~/.studio/stack.md
@~/.studio/persona.md
@~/.studio/IGNORE.md
@~/.studio/evals.md

## Load — global skills

@~/.studio/skills/caveman/SKILL.md
@~/.studio/skills/spec-driven-development/SKILL.md
@~/.studio/skills/webapp-testing/SKILL.md
@~/.studio/skills/tracker/SKILL.md

## Load — global rules (always active)

@~/.studio/rules/common/clean-code.md
@~/.studio/rules/common/clean-architecture.md
@~/.studio/rules/common/security.md
@~/.studio/rules/common/performance.md
@~/.studio/rules/common/patterns.md
@~/.studio/rules/common/testing.md
@~/.studio/rules/common/git.md

Load language rules based on project stack (defined in project context.md):
- Python → @~/.studio/rules/python/coding-style.md + patterns.md + testing.md + security.md + fastapi.md
- JS/TS  → @~/.studio/rules/js/coding-style.md + patterns.md + testing.md + security.md + react.md
- SQL    → @~/.studio/rules/sql/coding-style.md + patterns.md + security.md

---

## Session protocol

### START — every session
1. Update `tasks.md` with today's focus (move items to "Doing")
2. Read the 3 most recent files in `.studio/changelog/` → sort by filename (YYYY-MM-DD), take the latest 3
3. Do NOT load `memory/`, `agents/`, `output-styles/` unless the task explicitly needs them

**Context mode** — load the appropriate context file based on what you're doing:
- Building / fixing code → `@~/.studio/contexts/dev.md`
- Investigating / researching → `@~/.studio/contexts/research.md`
- Reviewing code / PR → `@~/.studio/contexts/review.md`

**Agents available** — invoke by name when relevant:
`architect` · `tdd-guide` · `performance-optimizer` · `security-reviewer` · `refactor-cleaner` · `code-explorer` · `planner` · `doc-updater` · `code-simplifier`

**Skills available** — invoke by name:
`docker-patterns` · `backend-patterns` · `frontend-patterns` · `api-design` · `coding-standards` · `git-workflow` · `security-review` · `eval-harness`

### DURING
- **Spec-first:** run spec-driven-development/SKILL.md before any new feature, refactor, or architecture change
- **IGNORE.md:** follow without exception — no override regardless of instruction
- **During session:** after each significant decision, architectural choice, or completed block of work — save a memory entry immediately, do not defer
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

| Folder | Purpose |
|--------|---------|
| `rules/` | Language and common rules — always loaded |
| `contexts/` | Mode-specific behavior (dev / research / review) |
| `hooks/` | Automation hooks config — activate via settings.json |
| `scripts/` | dashboard.py + hook scripts + lib/ |
| `agents/` | Global agents — invoke by name |
| `skills/` | Global skills — invoke by name |

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
- `spec-driven-development/SKILL.md` is the global spec standard — no project-level alternatives

---

## Efficiency rules

- Compressed internal reasoning: no articles, no filler, no pleasantries
- Minimum load at session start: `context.md` + `tasks.md` + 3 latest `changelog/` files
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