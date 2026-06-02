# .studio

An AI-agnostic context management system for software projects.

---

## What it is

`.studio` is a structured folder of markdown files that gives any AI coding assistant — Claude Code, Gemini CLI, Cursor, or anything else — a consistent, layered understanding of how you work before it writes a single line of code.

It is not a plugin. It is not a framework. It is a set of files.

---

## How it works

Every AI session in a project begins with a cascade:

```
project/CLAUDE.md (or GEMINI.md)
  └── @.studio/STUDIO.md          ← project-level context
        └── @~/.studio/STUDIO.md  ← global standards
              ├── harness.md       ← engineering rules
              ├── stack.md         ← technology decisions
              ├── persona.md       ← communication style
              ├── IGNORE.md        ← files never to touch
              ├── evals.md         ← agent success metrics
              └── skills/          ← reusable procedures
```

The AI tool reads the entry file, which expands all `@` references in sequence. By the time the model reads your first message, it already knows your engineering standards, your tech stack, what files to never touch, and how you prefer to communicate.

The global `~/.studio/` applies to every project on your machine. Each project's `.studio/` inherits from the global and adds its own context — architecture, current sprint, known traps.

---

## File reference

### Global (`~/.studio/`)

| File | Purpose |
|------|---------|
| `STUDIO.md` | Entry point. References all global files. Defines session protocol and extension points. |
| `harness.md` | Engineering standards. Five absolute rules: schema-first, evals-driven, context engineering, failure-aware design, observability. |
| `stack.md` | Technology decisions — final, not suggestions. Python, TypeScript, Next.js, Supabase, Claude, Ollama. No LangChain. |
| `persona.md` | Communication contract. Direct answers, code before explanation, no pleasantries, Italian or English per session — not mixed. |
| `IGNORE.md` | Files and folders the AI must never modify: `.env*`, `.git/`, build artifacts, migrations. |
| `evals.md` | How to know if agents are succeeding. Required fields for every agent file. Session logging rules. |
| `skills/` | Reusable procedures. `spec-kit/SKILL.md` for spec-driven development. `webapp-testing/SKILL.md` for Playwright. `tracker/SKILL.md` for session cost logging. |

### Project-level (`.studio/` in each repo)

| File | Purpose |
|------|---------|
| `STUDIO.md` | Opens with `@~/.studio/STUDIO.md`. Adds project-specific overrides and loads local files. |
| `context.md` | Lean operational state: architecture, data sources, hard constraints, current feature status. Not documentation — what the AI needs to act correctly. |
| `tasks.md` | Current sprint. Doing / Next / Blocked. Updated every session. |
| `changelog/` | One file per session (`YYYY-MM-DD.md`). What was done, files changed, token cost. Only the 3 most recent files are loaded at session start. |
| `gotchas.md` | Known traps in this specific codebase. Read by agents before executing. Written to when a new recurring issue is discovered. |
| `memory/` | Facts that persist across sessions: archived topic index, pending queue, trusted sources. |

---

## Why AI-agnostic

Claude Code reads `CLAUDE.md`. Gemini CLI reads `GEMINI.md`. Cursor reads `.cursorrules`. Each tool has its own entry file and its own format quirks.

`.studio/` sits underneath all of them. The entry files become thin wrappers:

```markdown
# CLAUDE.md
@.studio/STUDIO.md
```

When you switch AI tools, you update one line. Your engineering standards, tech decisions, and project context stay exactly as they are.

---

## Token cost

Loading the full global context at session start costs approximately **8,000 tokens** — around 4% of a 200K context window.

The design keeps this low by:
- Using imperatives, not prose (rules load fast, explanations don't)
- Loading skills on-demand where possible
- Limiting changelog to 3 most recent files, not the full history
- Keeping `context.md` focused on operational state, not documentation

---

## The session protocol

Every session follows three phases:

**START** — Load `tasks.md` + 3 most recent `changelog/` files. Know what is in scope before touching anything.

**DURING** — Spec-first: no code without an approved spec. IGNORE.md: no exceptions. Stack: follow decisions, don't explore alternatives.

**END** — Summary of what was done, files changed, token cost. Session tracker writes to `changelog/YYYY-MM-DD.md`.

---

## Harness Engineering

The five rules in `harness.md` encode what separates production AI systems from demos:

1. **Schema-first** — LLM output is validated with Pydantic or Zod before any operation. Always.
2. **Evals-driven** — No prompt ships without running against a golden dataset.
3. **Context engineering** — Raw HTML and unprocessed text never reach the LLM. Filter first.
4. **Failure-aware design** — Exception chaining, retry with backoff, partial result recovery.
5. **Observability** — Every LLM call logged: model, tokens, latency, cost.

---

## Personal opinion

I built this because I kept losing context.

Every new Claude Code session started from zero. I re-explained the stack, re-stated the constraints, re-described the architecture. The AI produced technically correct code that violated decisions I had made three sessions earlier — not because the model was bad, but because I never gave it the memory it needed to act consistently.

The standard advice is "just write a good CLAUDE.md." I tried that. The problem is that a good CLAUDE.md for one project becomes a different document from a good CLAUDE.md for another project, and neither of them survives tool changes. When Claude Code improved, I updated my CLAUDE.md. When I tried Cursor, I rewrote it. Every update was a tax.

`.studio` solves this by separating what is stable (engineering standards, technology decisions, communication preferences) from what changes (current tasks, recent sessions, project state). The stable parts live globally and never need to be rewritten. The changing parts are updated automatically at the end of every session.

The other thing I got wrong before: I thought the AI needed documentation. It doesn't. It needs rules. Long explanations about why we use Pydantic are wasted tokens. "ALWAYS validate LLM output with Pydantic before any DB operation" is not. The shift from documentation to imperatives cut my session start context by roughly 40% while making the AI's behavior more consistent, not less.

On the agent side: the `memory/` folder and the changelog structure came from realizing that agents in production need the same thing good engineers need — a record of what was decided, what was tried, and what is known to break. Without that record, every agent session is a fresh start with no institutional knowledge. With it, the pipeline gets better over time instead of repeating the same mistakes.

This is a living system. I add a gotcha when I hit a recurring bug. I add a memory file when agents start losing important state. I add a skill when I find myself repeating the same instruction across sessions. The overhead of maintaining it is lower than the overhead of not having it.

---

## Usage

```bash
# Clone to your home directory
git clone https://github.com/me-mowgli/studio ~/.studio

# Create your project entry file
echo "@.studio/STUDIO.md" > your-project/CLAUDE.md

# Copy and customize the project template
cp -r .studio/templates/project your-project/.studio
```

Edit `~/.studio/stack.md` to match your actual tech decisions.  
Edit `~/.studio/persona.md` to match how you want to communicate.  
Create `your-project/.studio/context.md` with your project's current state.

---

## License
MIT. Use it, adapt it, break it into pieces and take what's useful.