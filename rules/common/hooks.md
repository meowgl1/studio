---
scope: global
applies-to: all projects
---

# Hooks — Common Rules

Hooks here means **code-level lifecycle hooks** (framework events, not Claude Code automation hooks).  
For Claude Code automation hooks → see `~/.studio/hooks/hooks.json`.

## When to use hooks

Use hooks for cross-cutting concerns that don't belong in business logic:

- Authentication checks
- Request/response logging
- Rate limiting enforcement
- Input transformation / normalization
- Audit trail recording

## Hook design rules

- Hooks are **pure middleware** — they observe or transform, they don't own business logic
- Each hook does one thing
- Hooks must be composable and order-independent where possible
- Hooks must not have hidden state between requests (use request-scoped context)
- Async hooks must handle errors explicitly — unhandled rejections in hooks are silent killers

## FastAPI / Python hooks pattern

```python
@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("request", path=request.url.path, status=response.status_code, ms=round(duration * 1000))
    return response
```

## React / Next.js hooks rules

- Custom hooks must start with `use`
- Do not put business logic in hooks — hooks manage state and side effects only
- One concern per custom hook (`useAuth`, `useCart`, not `useAuthAndCart`)
- `useEffect` cleanup: always return cleanup function for subscriptions and timers

## Anti-patterns

- Hook that calls another hook directly (bypass the framework)
- Hooks with side effects that run on every render without dependency array
- Mutating shared state inside a hook instead of returning new state
