---
scope: global
applies-to: all projects
---

# Clean Architecture — Common Rules

## Layer separation

```
HTTP / CLI layer      →  receives input, calls service, returns response
Service layer         →  business logic, orchestration, no I/O
Repository layer      →  data access only, no business logic
Domain / models       →  pure data structures, no dependencies
```

- **Never** put business logic in controllers/routes
- **Never** import HTTP/framework types inside service or repository layers
- Dependencies flow inward — outer layers depend on inner, never reverse

## Repository pattern

Every data source (DB, external API, file) sits behind a repository interface.

```
interface UserRepository:
    findById(id) → User | None
    findAll(filters) → list[User]
    create(data) → User
    update(id, data) → User
    delete(id) → void
```

- Repositories return domain models, not raw DB rows
- No SQL/ORM queries outside repository classes
- Test repositories against real DB, not mocks

## Service layer

- Services call repositories, not DB directly
- One service per domain entity (UserService, OrderService)
- Services are stateless — no instance-level mutable state
- Cross-cutting concerns (auth, logging) via middleware/decorator, not inside services

## Dependency injection

- Pass dependencies in (constructor or function params) — never import singletons inside functions
- Makes testing possible without patching globals
- Config values come from outside (env vars injected at startup), not read inside functions

## Module boundaries

- Each module owns its data — no reaching into another module's DB table
- Public API: explicit exports only
- Shared utilities in `lib/` or `utils/` — not business logic, only pure helpers

## Anti-patterns — never do this

- Fat controllers (more than 10 lines of logic in a route handler)
- God objects / God services (one class doing everything)
- Circular imports between modules
- Hard-coded config inside business logic
- Bypassing the repository to query DB directly from a service
