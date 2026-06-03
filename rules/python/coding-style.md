---
scope: global
applies-to: "**/*.py"
---

# Python — Coding Style

## Base standard

PEP 8 + enforced by `black` (formatting) + `isort` (imports) + `ruff` (linting).  
Run all three before committing — no exceptions.

## Type annotations

- Required on **all** public function signatures — no `Any`
- Use `X | None` over `Optional[X]` (Python 3.10+)
- Use `list[X]`, `dict[K, V]` over `List[X]`, `Dict[K, V]` (Python 3.9+)

```python
def find_user(user_id: str, active_only: bool = True) -> User | None:
    ...
```

## Immutability

Prefer immutable structures:

```python
@dataclass(frozen=True)
class User:
    id: str
    email: str
    role: str

class Point(NamedTuple):
    x: float
    y: float
```

- Never use mutable default arguments: `def f(items=[])` → **forbidden**
- Use `None` as default, create inside function body

## Data models

- **Always** Pydantic v2 for external-facing data (HTTP, queue, LLM output)
- `@dataclass(frozen=True)` for internal domain objects
- No raw `dict` as a data container — always a typed model

## Imports

```python
# 1. stdlib
import os
from pathlib import Path

# 2. third-party
from pydantic import BaseModel
import httpx

# 3. local
from app.models import User
```

isort handles ordering automatically. Never use `*` imports.

## Async

- Use `async/await` for all I/O — no blocking calls in async functions
- `asyncio.gather` for concurrent tasks + `asyncio.Semaphore(N)` to cap concurrency
- Never `time.sleep()` in async code — use `asyncio.sleep()`

## File conventions

- snake_case for all file names
- One module = one clear responsibility
- `__all__` in modules that export public API

## Docstrings

Only on public functions/classes in library code.  
Skip for internal implementation details.  
Use one-line docstring for obvious functions.
