---
scope: global
applies-to: "**/*.py"
---

# Python — Patterns

## Pydantic v2 — data validation

```python
from pydantic import BaseModel, field_validator, model_validator

class CreateUserInput(BaseModel):
    email: str
    password: str
    role: str = "user"

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("invalid email")
        return v.lower()
```

Always validate LLM output with Pydantic — never trust raw string parsing.

## Repository pattern

```python
class UserRepository:
    def __init__(self, db: SupabaseClient):
        self._db = db

    async def find_by_id(self, user_id: str) -> User | None:
        result = await self._db.table("users").select("*").eq("id", user_id).maybe_single().execute()
        return User(**result.data) if result.data else None

    async def create(self, data: CreateUserInput) -> User:
        result = await self._db.table("users").insert(data.model_dump()).execute()
        return User(**result.data[0])
```

## Context managers for resources

```python
@asynccontextmanager
async def get_db_connection():
    client = create_client(url, key)
    try:
        yield client
    finally:
        await client.close()
```

## Concurrent I/O with Semaphore

```python
sem = asyncio.Semaphore(10)

async def fetch_with_limit(url: str) -> dict:
    async with sem:
        async with httpx.AsyncClient() as client:
            return (await client.get(url)).json()

results = await asyncio.gather(*[fetch_with_limit(url) for url in urls])
```

## Result pattern (no exceptions for expected failures)

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err:
    message: str
    code: str

Result = Ok[T] | Err
```

Use for operations where failure is a valid outcome (auth, validation).  
Reserve exceptions for truly unexpected errors.

## Generator pattern for large datasets

```python
async def iter_users(filters: UserFilters):
    page = 0
    while True:
        batch = await repo.find_paginated(filters, page=page, limit=100)
        if not batch:
            break
        for user in batch:
            yield user
        page += 1
```

## Dependency injection

```python
# main.py / startup
db = create_supabase_client()
user_repo = UserRepository(db)
user_service = UserService(user_repo)

# router
@router.post("/users")
async def create_user(
    data: CreateUserInput,
    service: UserService = Depends(get_user_service),
):
    return await service.create(data)
```

Never import singletons inside functions — inject at module/app level.
