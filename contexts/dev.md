---
scope: global
mode: development
load-when: actively building features, fixing bugs, refactoring
---

# Context — Development Mode

Active development: write code first, explain after.

## Priorities

1. Working → 2. Correct → 3. Polished

## Behavior

- Use Edit and Write tools for code changes
- Run tests immediately after implementation
- Use Bash for builds, tests, and CLI operations
- Use Grep and Glob for code discovery before editing
- Commit frequently with focused commits (one logical change each)

## Rules loaded in this mode

@~/.studio/rules/common/clean-code.md  
@~/.studio/rules/common/clean-architecture.md  
@~/.studio/rules/common/patterns.md  
@~/.studio/rules/common/testing.md  
@~/.studio/rules/common/performance.md  
@~/.studio/rules/common/security.md  
@~/.studio/rules/common/git.md

Load language-specific rules based on the active project stack (from `context.md`):
- Python project → `@~/.studio/rules/python/`
- JS/TS project → `@~/.studio/rules/js/`
- Has SQL/Supabase → `@~/.studio/rules/sql/`

## Session checklist

- [ ] Read `context.md` before touching any code
- [ ] Check `gotchas.md` for known traps
- [ ] Run existing tests before making changes
- [ ] Run tests again after changes
- [ ] Save memory entry after each significant decision

## Done criteria

- Feature works end-to-end
- Tests pass (unit + integration for the changed area)
- No new linting errors
- Changelog entry written
