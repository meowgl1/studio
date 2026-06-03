---
scope: global
mode: review
load-when: reviewing a PR, auditing code quality, security review, pre-merge check
---

# Context — Review Mode

Code review: read thoroughly before commenting.

## Priorities

1. Understand the change → 2. Find issues → 3. Prioritize by severity → 4. Suggest fixes

## Behavior

- Read all changed files before commenting on any
- Organize findings by severity: Critical → High → Medium → Low
- Suggest fixes, do not just point out problems
- Do not nitpick style that a linter would catch
- Focus on: logic errors, security, performance, architecture violations, test gaps

## Review checklist

**Correctness**
- [ ] Logic errors or wrong assumptions
- [ ] Edge cases not handled (null, empty, boundary values)
- [ ] Error paths handled correctly
- [ ] Race conditions (async code)

**Security**
- [ ] Injection vulnerabilities (SQL, command, XSS)
- [ ] Authentication and authorization checks present
- [ ] No hardcoded secrets or credentials
- [ ] Input validated at boundaries

**Architecture**
- [ ] Business logic not leaking into controllers/routes
- [ ] No circular dependencies introduced
- [ ] New code follows existing patterns in the codebase
- [ ] No unnecessary complexity added

**Performance**
- [ ] No N+1 queries introduced
- [ ] No blocking I/O in async context
- [ ] No unbounded loops or queries

**Tests**
- [ ] New functionality has tests
- [ ] Edge cases tested
- [ ] No tests removed or weakened

## Output format

```
## Critical
- [file:line] Issue — Suggested fix

## High
- [file:line] Issue — Suggested fix

## Medium
- [file:line] Issue — Suggested fix

## Low (optional)
- [file:line] Minor note

## Approved
[what looks good — specific, not generic praise]
```

## Rules loaded in this mode

@~/.studio/rules/common/clean-code.md  
@~/.studio/rules/common/clean-architecture.md  
@~/.studio/rules/common/security.md  
@~/.studio/rules/common/performance.md  
@~/.studio/rules/common/testing.md
