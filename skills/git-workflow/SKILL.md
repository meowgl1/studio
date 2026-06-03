---
name: git-workflow
description: Git workflow — branching strategy, commit discipline, PR process, release management
triggers:
  - "git workflow"
  - "branching strategy"
  - "pull request"
  - "how to commit"
  - "release process"
---

# Skill — Git Workflow

## Branch strategy (trunk-based for small teams)

```
main          ← production-ready at all times
  └── feat/user-auth-refresh    ← short-lived feature branch
  └── fix/order-pagination-bug  ← short-lived fix
  └── chore/upgrade-deps        ← maintenance
```

- Branch from `main`, merge back to `main`
- Short-lived branches — max a few days
- No long-running `develop` branch unless team requires it
- Tags for releases: `v1.2.3`

## Commit format

```
type: short description (max 72 chars)

Optional body — explain WHY, not what (code shows what).
Close #123
```

Types: `feat` · `fix` · `refactor` · `test` · `docs` · `chore` · `perf`

```bash
# Good
git commit -m "feat: add JWT refresh token rotation"
git commit -m "fix: prevent N+1 on user orders query"
git commit -m "refactor: extract payment service from order handler"

# Bad
git commit -m "WIP"
git commit -m "updates"
git commit -m "fix stuff"
```

## Commit discipline

```bash
# Stage specific files — never blindly add everything
git add app/services/user_service.py tests/unit/test_user_service.py

# Review what you're committing
git diff --staged

# Commit
git commit -m "feat: add email verification on user registration"
```

Never: `git add .` in production repos. Never: `git commit --amend` on pushed commits.

## Feature branch workflow

```bash
# 1. Start from fresh main
git checkout main && git pull

# 2. Create feature branch
git checkout -b feat/user-email-verification

# 3. Work in small commits
git add -p  # stage hunks, not whole files
git commit -m "feat: add verification token generation"
git commit -m "test: add unit tests for token expiry"

# 4. Stay current with main
git fetch origin
git rebase origin/main  # rebase, not merge — keeps history clean

# 5. Push and open PR
git push -u origin feat/user-email-verification
```

## PR checklist

Before opening a PR:
- [ ] Tests pass locally
- [ ] No linting errors
- [ ] Self-reviewed the diff
- [ ] PR description explains what and why
- [ ] PR size: ~400 lines max (split if larger)

PR description template:
```markdown
## What
Short description of the change.

## Why
Why this change is needed.

## How to test
Steps to verify the change works.
```

## Merge strategy

- **Squash merge** for feature branches — clean main history
- **Merge commit** for release branches — preserves history
- Never force-push to `main`

## Hotfix process

```bash
git checkout main
git pull
git checkout -b fix/critical-auth-bypass
# make fix
git commit -m "fix: prevent auth bypass on expired tokens"
git push -u origin fix/critical-auth-bypass
# open PR → fast review → merge → deploy immediately
```

## Release tagging

```bash
git tag -a v1.2.3 -m "Release 1.2.3 — adds email verification"
git push origin v1.2.3
```

Follow semver: `MAJOR.MINOR.PATCH`
- MAJOR: breaking change
- MINOR: new feature, backwards compatible
- PATCH: bug fix

## Stash for context switching

```bash
# Save work in progress
git stash push -m "WIP: email verification flow"

# Switch context, do other work, come back
git stash pop
```

## Useful aliases

```bash
# ~/.gitconfig
[alias]
  st = status --short
  lg = log --oneline --graph --decorate -20
  undo = reset HEAD~1 --soft
  wip = commit -m "wip: checkpoint"
```
