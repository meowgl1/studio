---
scope: global
applies-to: all projects
---

# Git — Common Rules

## Commit messages

Format: `type: short description` (max 72 chars)

Types: `feat` · `fix` · `refactor` · `test` · `docs` · `chore` · `perf`

```
feat: add JWT refresh token rotation
fix: prevent N+1 on user orders query
refactor: extract payment service from order handler
test: add edge cases for empty cart checkout
```

- Present tense, imperative mood ("add" not "added")
- No "WIP", "misc", "updates" — be specific
- One logical change per commit

## Branch naming

```
feat/user-auth-refresh
fix/order-pagination-bug
refactor/payment-service-extract
chore/upgrade-pydantic-v2
```

## PR rules

- Max ~400 lines changed per PR — split if larger
- PR description: what changed + why + how to test
- All tests passing before requesting review
- No force-push to main/master

## What never goes in git

- `.env` files or any secrets
- Generated files that can be reproduced (build artifacts, `__pycache__`, `node_modules`)
- Large binary files — use storage/CDN

## Commit discipline

- Commit early and often during development
- Do not commit broken code to shared branches
- Squash noise commits before merging (optional — check project convention)
