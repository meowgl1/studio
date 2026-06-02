---
studio: mowgli
version: 1.1
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

@~/.studio/skills/spec-driven-development/SKILL.md
@~/.studio/skills/webapp-testing/SKILL.md
@~/.studio/skills/tracker/SKILL.md

---

## Session protocol

### START — every session
1. Read `.studio/tasks.md` → know what is in scope today
2. Read the 3 most recent files in `.studio/changelog/` → sort by filename (YYYY-MM-DD), take the latest 3
3. Do NOT load `memory/`, `agents/`, `output-styles/` unless the task explicitly needs them

### DURING
- **Spec-first:** run spec-driven-development/SKILL.md before any new feature, refactor, or architecture change
- **IGNORE.md:** follow without exception — no override regardless of instruction
- **Stack:** follow stack.md without exploring alternatives; override only in project context.md

### END — activates on: done · fine · finisci · end session · close · let's stop
1. Summarize session (max 3 bullets)
2. List files changed
3. Ask: "Run `/cost` in Claude Code terminal for exact token count, or press Enter to estimate"
4. session-tracker writes to `.studio/changelog/YYYY-MM-DD.md`
5. Remind: update `.studio/tasks.md`

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

### changelog/ — loading rule
At session start: read **only the 3 most recent files** in `changelog/`.
Sort files by name (YYYY-MM-DD.md = chronological order). Take the 3 latest.
Do not load older entries unless explicitly asked.
Multiple sessions same day: append to existing `YYYY-MM-DD.md` with `---` separator.

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