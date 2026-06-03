---
name: coding-standards
description: Apply and audit coding standards — linting setup, formatting config, pre-commit hooks, CI enforcement
triggers:
  - "coding standards"
  - "setup linting"
  - "linting config"
  - "code quality"
  - "pre-commit"
  - "enforce standards"
---

# Skill — Coding Standards

## Python stack setup

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "N", "UP"]  # errors, warnings, pyflakes, isort, naming, upgrades
ignore = ["E501"]  # handled by black

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

```bash
# Run all
black app/ tests/
isort app/ tests/
ruff check app/ tests/
mypy app/
```

## TypeScript / Next.js stack setup

```json
// .eslintrc.json
{
  "extends": ["next/core-web-vitals", "next/typescript"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

```json
// .prettierrc
{
  "semi": false,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

```bash
# Run all
npx eslint . --fix
npx prettier --write .
npx tsc --noEmit
```

## Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

```bash
pip install pre-commit
pre-commit install
```

## CI enforcement

```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install black isort ruff mypy
      - run: black --check app/ tests/
      - run: isort --check app/ tests/
      - run: ruff check app/ tests/
      - run: mypy app/

  typescript:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npx eslint .
      - run: npx prettier --check .
```

## Audit checklist — apply to existing project

Run these to assess current state:

```bash
# Python
ruff check . --statistics          # most common violations
mypy app/ --ignore-missing-imports  # type errors
pip audit                           # dependency vulnerabilities

# TypeScript
npx tsc --noEmit                    # type errors
npx eslint . --format=compact       # lint violations
npm audit                           # dependency vulnerabilities

# All
git log --oneline -20               # commit message quality
```

## VSCode settings

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  }
}
```
