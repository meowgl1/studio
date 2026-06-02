---
name: spec-driven-development
description: Spec-driven development. 5 steps before any non-trivial implementation. Activate when user says new feature, refactor, implement, add, or fix (non-trivial). Replaces spec-writer. No code without approved spec.
---

# Spec Kit

No code without approved spec. Activate on: new feature, refactor, architecture change, new agent/skill.
Run each step in sequence. Stop after each step and wait for explicit "ok" / "approved" / "next".

---

## /speckit.specify — What must it do (not how)

Produce a single-screen spec using this format:

```
## Spec: [feature name]

Problem: [what breaks or is missing without this — 1 sentence]
Input:   [concrete example — what goes in]
Output:  [concrete example — what comes out]
Scope:   [what this feature does NOT do]
```

Rules:
- Describe behavior, not implementation
- No technical choices in this step (no "we'll use X library")
- If scope is unclear: list assumptions explicitly
- Wait for approval before proceeding

---

## /speckit.clarify — Resolve ambiguities

Read the spec from `.specify`. For each unclear point, ask one question at a time.
Do not ask questions that are answerable from context.md, gotchas.md, or the existing codebase.

Produce a final "Resolved spec" block that incorporates all answers.
No unanswered questions may remain before proceeding.

---

## /speckit.plan — Architecture and approach

Produce a plan block:

```
## Plan: [feature name]

Approach: [how it will work — one paragraph]
Files touched: [list with reason for each]
New files: [list with purpose]
Dependencies: [new packages needed — none if possible]
Risks: [what could go wrong]
```

Rules:
- Follow stack.md — no new dependencies without justification
- Follow existing architecture (domain → application → infrastructure)
- One approach only — recommend, do not present alternatives
- Wait for approval

---

## /speckit.tasks — Discrete actionable tasks

Break the plan into tasks. Each task must be:
- Completable in one implementation step
- Independently testable
- Described with: what to do + acceptance criterion

```
## Tasks: [feature name]

[ ] Task 1: [action] — AC: [how we know it's done]
[ ] Task 2: [action] — AC: [how we know it's done]
[ ] Task 3: write test for Task 1 and Task 2
...
```

Rules:
- Tests are always their own tasks, never bundled with implementation
- Security check (if feature touches DB or auth) is a standalone task
- Multi-language content (Baloo): translation task is always last
- Maximum 8 tasks — if more: split the feature

---

## /speckit.implement — Execute one task at a time

Take the task list. Execute tasks in order, one at a time.

Before each task:
- State which task you're executing
- Confirm it does not violate IGNORE.md or hard constraints

After each task:
- Show what changed
- Confirm the acceptance criterion is met
- Ask: "Task [N] done. Proceed to Task [N+1]?"

Rules:
- Never execute multiple tasks in one step
- If a task fails: stop, report what failed, wait for instruction
- If a task reveals a new constraint: surface it before continuing (do not silently adapt)

---

## Additional steps for LLM / AI features

Before `/speckit.implement` begins, if the feature involves LLM calls:

**Required additions to the spec (add to .specify output):**

```
Eval criteria:  [measurable — what makes output good vs bad]
Golden examples: [minimum 3 × (input → expected output)]
Output schema:  [Pydantic/Zod model — define before prompt]
Failure modes:  [what does a bad LLM output look like]
```

Rule: golden examples must be written to `golden_dataset.json` before any prompt is written.
Rule: output schema is defined before `.plan`. No schema = no implementation.

---

## Spec gate (for agents and supervisors)

Any agent receiving a task that has no approved spec must run spec-kit first.
The supervisor verifies spec approval before delegating to sub-agents.
"Approved" means: user has explicitly said "approved", "ok proceed", or "next" after `.tasks`.