---
scope: global
applies-to: all projects
---

# Patterns — Common Rules

## API response format

Every endpoint returns a consistent envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { "total": 100, "page": 1, "limit": 20 }
}
```

- `data` is null on error, `error` is null on success
- `meta` only present on paginated responses
- HTTP status codes are authoritative — do not return 200 with `success: false`

## Repository pattern

```python
class UserRepository:
    def find_by_id(self, id: str) -> User | None: ...
    def find_all(self, filters: UserFilters) -> list[User]: ...
    def create(self, data: CreateUserInput) -> User: ...
    def update(self, id: str, data: UpdateUserInput) -> User: ...
    def delete(self, id: str) -> None: ...
```

## Service pattern

```python
class UserService:
    def __init__(self, repo: UserRepository): ...  # inject dependency
    
    async def register(self, input: RegisterInput) -> User:
        # validate → check business rules → persist → return
```

## Error handling

Centralized error classes — never raise generic `Exception`:

```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status: int = 500): ...

class NotFoundError(AppError): ...
class ValidationError(AppError): ...
class UnauthorizedError(AppError): ...
```

## Retry with exponential backoff

For external calls that may fail transiently:

```python
async def with_retry(fn, max_attempts=3, base_delay=1.0):
    for attempt in range(max_attempts):
        try:
            return await fn()
        except TransientError:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(base_delay * (2 ** attempt))
```

## Event / queue pattern

For non-blocking operations:

```
HTTP handler → validates → enqueues job → returns 202 Accepted
Worker       → dequeues  → executes     → updates status
```

## Skeleton-first approach

For new features: search for an established pattern or skeleton before building from scratch.  
Evaluate security, extensibility, relevance — then adapt the best option.

## Anti-patterns — avoid

- **God object** — one class with 10+ responsibilities
- **Anemic domain model** — models with no behavior, all logic in services
- **Primitive obsession** — passing raw strings/ints where a typed object should be used
- **Shotgun surgery** — a single change requires editing 10 files
- **Premature abstraction** — interface/base class with only one implementation
