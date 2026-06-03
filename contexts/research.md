---
scope: global
mode: research
load-when: investigating a codebase, debugging a problem, evaluating a library, exploring options
---

# Context — Research Mode

Investigation: understand first, implement after.

## Priorities

1. Understand → 2. Document findings → 3. Recommend → 4. Implement (if needed)

## Behavior

- Read broadly before drawing conclusions
- Favor reading tools: Read, Grep, Glob, WebFetch, WebSearch
- Use the Explore agent for broad codebase questions
- Delay code changes until the picture is clear
- Document findings in structured notes before acting

## Research process

1. Grasp the question — what am I actually trying to understand?
2. Examine relevant code and documentation
3. Form a hypothesis
4. Validate with concrete evidence (not assumption)
5. Consolidate findings before recommending

## Output format

Present findings before recommendations:

```
## What I found
[evidence-based observations]

## Hypothesis
[what I think is happening]

## Recommendation
[what to do, with rationale]
```

## Rules loaded in this mode

@~/.studio/rules/common/patterns.md  
@~/.studio/rules/common/clean-architecture.md

No language-specific rules needed — research mode is read-only.

## Research checklist

- [ ] Start with existing docs and `context.md` before exploring code
- [ ] Check `gotchas.md` — the answer may already be documented
- [ ] Search before reading files — use Grep to narrow scope
- [ ] Do not open more than 5 files without a clear reason
- [ ] Write down key findings as I go — do not rely on memory at end of session
