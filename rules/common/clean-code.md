---
scope: global
applies-to: all languages
---

# Clean Code — Common Rules

## Core principles

**KISS** — Simplest solution that works. No clever tricks.  
**DRY** — Eliminate real repetition. Don't abstract prematurely.  
**YAGNI** — Build only what's needed now. No speculative features.  
**Immutability** — Create new objects, never mutate existing ones.

## Naming

- Variables and functions: descriptive, verb-noun (`fetchUser`, `isActive`)
- No abbreviations except universally understood (`id`, `url`, `api`, `db`)
- Boolean variables: `is`, `has`, `can`, `should` prefix
- Constants: `UPPER_SNAKE_CASE`
- Types / classes: `PascalCase`

## Functions

- Max 50 lines per function — if longer, extract
- One responsibility per function
- No side effects unless the function name signals them
- Max 3 parameters — use an object/dataclass beyond that
- Return early to avoid nesting

## Files

- 200–400 lines typical, 800 max
- Organize by feature, not by file type
- One primary export per file

## Structural rules

- Max nesting depth: 4 levels
- No magic numbers — use named constants
- No commented-out code — use git history
- No `TODO` left in committed code — create a task instead

## Error handling

- Never swallow exceptions silently
- User-facing errors: human-readable message
- Server-side errors: structured log with context (user id, request id, operation)
- Fail fast at system boundaries — validate inputs immediately

## Input validation

- Validate at every system boundary (HTTP, CLI, queue consumer)
- Use schema validation (Pydantic / Zod) — no manual if-chains
- Reject and log invalid inputs with enough context to debug
