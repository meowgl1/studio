---
name: multi-agent-patterns
description: Patterns for spawning and coordinating subagents. Activate when a task requires parallel work, large-scale exploration, or isolation from the main context. Defines when to use subagents, how to structure handoffs, and how to avoid conflicts.
---

# Multi-Agent Patterns

---

## When to use a subagent

**Use a subagent when:**
- The task would pollute the main context with output you don't need long-term (exploration, mapping, research)
- Two or more independent work streams can run in parallel with no shared write targets
- A specialist agent (code-explorer, security-reviewer, etc.) is the right tool and its output is a discrete artifact
- Context utilization is above 40% and the task is large — preserve main context headroom

**Stay single-agent when:**
- The task is linear and sequential — no parallel benefit
- The task requires continuous back-and-forth with the user
- The subtask is small (< 5 minutes of work) — spawn overhead not worth it
- All steps depend on each other's output

---

## Handoff template

Every subagent invocation must include these four fields. No free-text briefings.

```
Role:    [which agent — code-explorer / security-reviewer / planner / etc.]
Task:    [one sentence — what to produce]
Scope:   [what files/dirs to touch — explicit list]
Output:  [exact format expected — summary / list / file / decision]
```

**Example — exploration handoff:**
```
Role:   code-explorer
Task:   Map the authentication flow in this codebase
Scope:  Read-only. src/auth/, src/middleware/, src/api/routes/ only.
Output: Entry point, main flow (numbered steps), gotchas list. Max 300 words.
```

**Example — parallel work handoff:**
```
Role:   tdd-guide
Task:   Write tests for the UserRepository class
Scope:  Write to tests/unit/test_user_repository.py only. Do not touch src/.
Output: Test file ready to run. Report: tests written, coverage scope.
```

---

## Parallel agent rules

When spawning multiple agents at the same time:

1. **One writer per file** — two agents must never have overlapping write targets. Assign file ownership explicitly in the Scope field.
2. **Readers can share** — multiple agents can read the same files simultaneously.
3. **Collect before acting** — wait for all parallel agents to complete before using their outputs in the main context. Never act on partial results.
4. **Max 3 parallel agents** — beyond this, coordination overhead exceeds the parallelism benefit.

---

## Output integration

When a subagent returns:

1. Extract only what you need — do not paste the full agent transcript into context
2. Synthesize into a compact summary before continuing — one paragraph or a list
3. Discard scaffolding: strip agent meta-commentary ("I have analyzed...", "As requested...")
4. If the output contradicts current context.md or gotchas.md — surface the conflict before proceeding

---

## Anti-patterns

- **Briefing by conversation** — do not summarize the current conversation for the subagent. Write a self-contained prompt using the handoff template.
- **Unbounded scope** — `Scope: entire codebase` produces noise. Always constrain to directories or files.
- **Chained blind handoffs** — do not pass agent A's raw output directly to agent B without reviewing it first.
- **Spawning for small tasks** — if the task fits in 3-5 tool calls, do it in the main context.
