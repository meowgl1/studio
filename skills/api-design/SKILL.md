---
name: api-design
description: REST API design principles — resource naming, versioning, error formats, pagination, documentation
triggers:
  - "design api"
  - "api design"
  - "rest api"
  - "api endpoints"
  - "api structure"
---

# Skill — API Design

## Resource naming

- Plural nouns for collections: `/users`, `/orders`, `/products`
- Nested for ownership: `/users/{id}/orders`
- Actions as sub-resources: `/orders/{id}/cancel`, `/users/{id}/verify-email`
- No verbs in paths: `/orders` not `/getOrders`

```
GET    /users              → list users
POST   /users              → create user
GET    /users/{id}         → get user
PATCH  /users/{id}         → partial update
DELETE /users/{id}         → delete user
POST   /users/{id}/suspend → action on resource
```

## HTTP methods and status codes

| Method | Purpose | Success |
|--------|---------|---------|
| GET | Read | 200 |
| POST | Create | 201 |
| PATCH | Partial update | 200 |
| PUT | Full replace | 200 |
| DELETE | Delete | 204 |

Error codes:
- `400` Bad Request — validation error
- `401` Unauthorized — missing/invalid auth
- `403` Forbidden — authenticated but not allowed
- `404` Not Found
- `409` Conflict — duplicate, state conflict
- `422` Unprocessable Entity — semantic validation failure
- `429` Too Many Requests
- `500` Internal Server Error

## Response envelope

```json
{
  "success": true,
  "data": { "id": "abc", "email": "user@test.com" },
  "error": null
}
```

Paginated:
```json
{
  "success": true,
  "data": [...],
  "error": null,
  "meta": {
    "total": 250,
    "page": 2,
    "limit": 20,
    "has_next": true
  }
}
```

Error:
```json
{
  "success": false,
  "data": null,
  "error": "email already in use",
  "code": "CONFLICT"
}
```

## Query parameters — conventions

```
GET /orders?status=pending          → filter
GET /orders?page=2&limit=20         → pagination
GET /orders?sort=created_at&dir=desc → sorting
GET /orders?q=coffee                → search
GET /orders?include=user,items      → eager loading
```

## Versioning

- URL versioning: `/api/v1/users` — most explicit, cache-friendly
- Add `/v2` only when breaking changes are required
- Maintain v1 for at least one migration cycle

## Input validation

Always validate request body, path params, and query params:

```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    role: Literal["admin", "user"] = "user"

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Literal["active", "inactive"] | None = None,
):
```

## Documentation with FastAPI

FastAPI auto-generates OpenAPI docs. Enhance with:

```python
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user",
    responses={
        409: {"description": "Email already in use"},
        422: {"description": "Validation error"},
    },
)
async def create_user(body: CreateUserRequest):
    """
    Create a new user account.
    
    Sends a verification email on success.
    """
```

## Idempotency

For POST endpoints that should be safe to retry:

```python
@router.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
):
    # Check if we've seen this key before
    cached = await redis.get(f"idempotency:{idempotency_key}")
    if cached:
        return json.loads(cached)

    order = await order_service.create(body)
    await redis.setex(f"idempotency:{idempotency_key}", 86400, order.model_dump_json())
    return order
```

## Webhooks (outbound)

```python
async def dispatch_webhook(event_type: str, payload: dict, subscribers: list[WebhookSubscriber]):
    for sub in subscribers:
        if event_type in sub.events:
            signature = hmac.new(sub.secret.encode(), json.dumps(payload).encode(), "sha256").hexdigest()
            await httpx.post(
                sub.url,
                json={"event": event_type, "data": payload},
                headers={"X-Signature": f"sha256={signature}"},
            )
```

Always sign webhook payloads. Document the signature verification process for consumers.
