---
scope: global
applies-to: all projects
---

# Performance — Common Rules

## Query discipline

- **No N+1 queries** — batch-load related data, use joins or `IN (...)` clauses
- Select only needed columns — never `SELECT *` in production code
- Add indexes on columns used in WHERE, JOIN, ORDER BY
- Use pagination on any list endpoint — never return unbounded sets
- Use transactions for multi-step operations — both for correctness and speed

## Async / concurrency

- Never sequential loops on I/O — use `asyncio.gather` + `Semaphore` (Python) or `Promise.all` (JS)
- Cap concurrency — `Semaphore(10)` for API calls, `Semaphore(5)` for DB writes
- No unbounded parallel calls — always set a limit

## Caching

- Cache expensive reads that change rarely (TTL-based)
- Cache-aside pattern: read from cache → miss → read DB → write cache
- Never cache user-specific data globally
- Invalidate on write — not on timer alone when data freshness matters
- Use Redis only when rate limiting or shared cache across instances is required

## Frontend targets (Vercel / Next.js)

| Metric | Target |
|--------|--------|
| LCP | < 2.5s |
| TTI | < 3.8s |
| Bundle (gzip) | < 200KB |
| TBT | < 200ms |

- Server Components by default — no unnecessary `'use client'`
- Lazy-load routes and heavy components
- `next/image` for all images — never raw `<img>`

## Profiling rule

**Profile before optimizing.** Do not guess bottlenecks.  
Measure: slow query logs, `EXPLAIN ANALYZE`, Lighthouse, bundle analyzer.  
Fix the actual bottleneck, not the assumed one.

## Background work

- Never block an HTTP response for non-critical work (email sending, analytics)
- Offload to a queue or background task
- Design background jobs to be idempotent (safe to retry)
