---
scope: global
applies-to: "**/*.ts, **/*.tsx, **/*.js"
---

# JavaScript / TypeScript — Coding Style

## TypeScript — mandatory settings

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

No `any`. No `@ts-ignore`. No `as unknown as X` casts without a comment explaining why.

## Naming

- Variables, functions: `camelCase`
- Components, classes, types, interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components
- Boolean variables: `is`, `has`, `can`, `should` prefix

## Immutability

```typescript
// Good
const user = { ...existingUser, email: newEmail }
const items = [...cart.items, newItem]

// Forbidden
existingUser.email = newEmail
cart.items.push(newItem)
```

Use `readonly` on types where mutation is not expected.

## Functions

- Arrow functions for callbacks and lambdas
- Named functions for top-level declarations (better stack traces)
- Async/await over `.then()` chains — always
- Max 50 lines per function

## Null safety

```typescript
// Good — explicit null check
if (user === null) return null

// Good — optional chaining
const email = user?.profile?.email

// Good — nullish coalescing
const name = user?.name ?? "Anonymous"

// Forbidden — loose equality
if (user == null) ...
```

## Imports

```typescript
// 1. Node built-ins
import { readFile } from "fs/promises"

// 2. Third-party
import { z } from "zod"
import { NextRequest } from "next/server"

// 3. Local — absolute paths
import { UserService } from "@/services/user"

// 4. Local — relative (only within same module)
import { formatDate } from "./utils"
```

- No barrel files (`index.ts` re-exporting everything) — causes circular deps
- Use absolute imports with `@/` alias

## Formatting

Prettier handles all formatting — do not manually format.  
ESLint handles linting — fix linting errors, do not disable rules.

## Error handling

```typescript
// Good — typed errors
class AppError extends Error {
  constructor(public message: string, public code: string, public status: number) {
    super(message)
  }
}

// Forbidden — swallowing errors
try {
  await doSomething()
} catch (_) {}
```
