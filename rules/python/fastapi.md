---
scope: global
applies-to: FastAPI projects
---

# Python — FastAPI Patterns

## App setup with lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.db = create_supabase_client()
    yield
    # shutdown
    await app.state.db.close()

app = FastAPI(lifespan=lifespan)
```

Never use deprecated `@app.on_event("startup")` — use `lifespan`.

## Request / response with Pydantic

```python
class CreateOrderRequest(BaseModel):
    user_id: str
    items: list[OrderItem]
    notes: str | None = None

class OrderResponse(BaseModel):
    id: str
    status: str
    total: float
    created_at: datetime

@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(body: CreateOrderRequest, service: OrderService = Depends(get_order_service)):
    return await service.create(body)
```

- Always declare `response_model` — it strips extra fields and validates output
- Use `status_code` on the decorator, not inside the handler

## Dependency injection

```python
def get_db(request: Request) -> SupabaseClient:
    return request.app.state.db

def get_user_service(db: SupabaseClient = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))
```

## Auth dependency

```python
async def require_auth(authorization: str = Header(...)) -> TokenPayload:
    token = authorization.removeprefix("Bearer ").strip()
    return verify_token(token)  # raises UnauthorizedError on failure

@router.get("/me")
async def get_me(payload: TokenPayload = Depends(require_auth)):
    ...
```

## Error handling — global exception handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content={"success": False, "data": None, "error": exc.message}
    )
```

## Router organization

```
app/
  routers/
    users.py      # APIRouter(prefix="/users", tags=["users"])
    orders.py
  services/
    user_service.py
  repositories/
    user_repository.py
  models/
    user.py
  main.py
```

## Background tasks

```python
from fastapi import BackgroundTasks

@router.post("/orders")
async def create_order(body: CreateOrderRequest, background_tasks: BackgroundTasks):
    order = await order_service.create(body)
    background_tasks.add_task(email_service.send_confirmation, order.id)
    return order
```

Use `BackgroundTasks` for fire-and-forget. For reliable async work (retries, monitoring) → use a proper queue.

## Middleware order

1. CORS
2. Authentication (if applied globally)
3. Request logging
4. Rate limiting
5. Custom business middleware

```python
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, ...)
```
