---
name: tracker
description: Track session work and costs. Activates when user signals session end. Writes a file to .studio/changelog/YYYY-MM-DD.md. Never creates files outside .studio/changelog/.
trigger: user says done · fine · finisci · end session · close · let's stop · commit
---

Activate on: "done", "fine", "finisci", "end session", "close", "let's stop", "commit".
Do not activate on partial signals: "done with this function", "commit this file".
When unsure: ask "Session done or just this task?"

---

## What to do — in order

**Step 1 — Detect project**
Read `.studio/context.md` first line, or use the current working directory name.
This is the [project] label.

**Step 2 — Summarize session**
1–3 bullet points, past tense, concise. What was built, changed, fixed, or decided.
Max 3 bullets. Group related items if needed.

**Step 3 — List files changed**
Relative paths from project root. Comma-separated.
Many files: group by type (e.g. "3 files in app/components/").

**Step 4 — Capture cost**
Prompt: *"Run `/cost` in Claude Code terminal and paste the result, or press Enter to skip."*
User provides result → use exact numbers.
User skips → estimate:
- Q&A / quick fix: ~5–15k tokens
- Feature implementation: ~20–50k tokens
- Architecture / large refactor: ~50–120k tokens

**Step 5 — Write to changelog/**
Determine today's date → `YYYY-MM-DD.md`.
Check if `.studio/changelog/YYYY-MM-DD.md` already exists:
- Does not exist → create it, write entry
- Already exists (multiple sessions today) → append with `---` separator

Show entry to user before writing. Wait 5 seconds for corrections.

---

## Entry format

```
## [HH:MM] [project] — [3-word session title]

- [what was done]
- [what was done]
- [what was done]

Files: path/to/file, path/to/other
Model: [model name]
Tokens: ~[N]k in / ~[N]k out · Cost: $[X] or est. [range]
```

---

## Changelog folder structure

```
.studio/changelog/
├── 2026-06-02.md    ← today (multiple sessions: appended with ---)
├── 2026-06-01.md
└── 2026-05-31.md
```

Loading rule (in STUDIO.md): Claude reads the 3 files with the most recent dates only.

---

## Hard rules

- Write ONLY to `.studio/changelog/YYYY-MM-DD.md`
- NEVER modify previous entries
- NEVER create a separate stats file
- NEVER create changelog entries outside the `.studio/changelog/` folder
- If `.studio/changelog/` does not exist: create the folder, then write the file
- Max 10 lines per session entry (including blank lines)
- After writing: remind user to update `.studio/tasks.md`

---

## Monthly summary (on request only)

User asks "summarize costs for [month]":
1. Read all files in `changelog/` matching `YYYY-MM-*.md` for that month
2. Sum token estimates and costs
3. Return: total sessions · total tokens · estimated cost · most expensive session
4. Do NOT write this summary to any file unless explicitly asked