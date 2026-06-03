---
name: backend-patterns
description: Backend architecture patterns — API design, service layer, repositories, auth, caching, background jobs
triggers:
  - "backend"
  - "api endpoint"
  - "service layer"
  - "repository"
  - "backend patterns"
---

# Skill — Backend Patterns

## API structure

```
app/
  routers/          # HTTP layer only — routes, request parsing, response formatting
  services/         # Business logic
  repositories/     # Data access
  models/           # Domain models (Pydantic / dataclasses)
  lib/              # Pure helpers with no dependencies
  main.py
```

## Request → Service → Repository flow

```python
# Router — thin, no business logic
@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    body: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
):
    return await service.create(body)

# Service — business logic
class OrderService:
    async def create(self, input: CreateOrderRequest) -> Order:
        user = await self.user_repo.find_by_id(input.user_id)
        if not user:
            raise NotFoundError("user")
        if not user.is_active:
            raise ForbiddenError("account is suspended")
        order = await self.order_repo.create(input)
        await self.email_service.send_confirmation(order)
        return order

# Repository — data access only
class OrderRepository:
    async def create(self, data: CreateOrderRequest) -> Order:
        result = await self.db.table("orders").insert(data.model_dump()).execute()
        return Order(**result.data[0])
```

## Authentication middleware

```python
async def require_auth(
    authorization: str = Header(...),
    repo: UserRepository = Depends(get_user_repo),
) -> User:
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token)
    user = await repo.find_by_id(payload["sub"])
    if not user:
        raise UnauthorizedError("user not found")
    return user
```

## RBAC

```python
def require_role(*roles: str):
    async def check(current_user: User = Depends(require_auth)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("insufficient permissions")
        return current_user
    return check

@router.delete("/users/{id}")
async def delete_user(id: str, user: User = Depends(require_role("admin"))):
    ...
```

## Caching — cache-aside pattern

```python
class CachedUserRepository:
    def __init__(self, repo: UserRepository, redis: Redis):
        self._repo = repo
        self._redis = redis

    async def find_by_id(self, user_id: str) -> User | None:
        cache_key = f"user:{user_id}"

        cached = await self._redis.get(cache_key)
        if cached:
            return User(**json.loads(cached))

        user = await self._repo.find_by_id(user_id)
        if user:
            await self._redis.setex(cache_key, 300, user.model_dump_json())  # 5 min TTL
        return user

    async def update(self, user_id: str, data: UpdateUserInput) -> User:
        user = await self._repo.update(user_id, data)
        await self._redis.delete(f"user:{user_id}")  # invalidate on write
        return user
```

Only use Redis if you have multiple instances. Single-process cache: `functools.lru_cache` or `cachetools`.

## Background jobs

```python
from fastapi import BackgroundTasks

# For fire-and-forget (no retry needed)
@router.post("/orders")
async def create_order(body: CreateOrderRequest, bg: BackgroundTasks):
    order = await order_service.create(body)
    bg.add_task(send_confirmation_email, order.id)
    return order

# For reliable jobs with retry — use a queue (Celery, ARQ, or similar)
async def enqueue_email(order_id: str):
    await redis.lpush("email_queue", json.dumps({"order_id": order_id}))
```

## Structured logging

```python
import structlog

log = structlog.get_logger()

async def create_order(input: CreateOrderRequest, user: User) -> Order:
    log.info("order.creating", user_id=user.id, item_count=len(input.items))
    order = await repo.create(input)
    log.info("order.created", order_id=order.id, total=order.total)
    return order
```

Always include: operation name, entity IDs, user context. Never include: passwords, tokens, PII.

## Rate limiting

```python
# Use slowapi (Starlette-compatible)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    ...
```

Use platform-level rate limiting (Vercel, Cloudflare) for production — not in-process counters.

## Pagination

```python
class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    error: str | None = None
    meta: PaginationMeta

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    has_next: bool

@router.get("/orders")
async def list_orders(page: int = 1, limit: int = Query(20, le=100)) -> PaginatedResponse[Order]:
    orders, total = await order_repo.find_paginated(page=page, limit=limit)
    return PaginatedResponse(
        data=orders,
        meta=PaginationMeta(total=total, page=page, limit=limit, has_next=(page * limit) < total),
    )
```
