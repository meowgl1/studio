---
scope: global
applies-to: "**/*.ts, **/*.tsx"
---

# JavaScript / TypeScript — Security

## XSS prevention

```typescript
// Forbidden — raw HTML injection
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// Safe — let React escape it
<div>{userContent}</div>

// If HTML is needed — sanitize first
import DOMPurify from "dompurify"
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userContent) }} />
```

## CSRF

- SameSite cookies: always set `SameSite=Strict` or `SameSite=Lax`
- For mutation APIs: verify `Origin` header matches expected domain
- Supabase handles this via JWT — no additional CSRF token needed if using auth header

## Authentication

```typescript
// Middleware — Next.js
import { NextRequest, NextResponse } from "next/server"
import { verifyToken } from "@/lib/auth"

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value
  if (!token) return NextResponse.redirect(new URL("/login", request.url))

  try {
    verifyToken(token)
    return NextResponse.next()
  } catch {
    return NextResponse.redirect(new URL("/login", request.url))
  }
}
```

## Environment variables

```typescript
// Forbidden — no validation
const key = process.env.API_KEY

// Good — validated at startup
import { z } from "zod"

const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
})

export const env = EnvSchema.parse(process.env)
```

Server-side secrets must never be prefixed with `NEXT_PUBLIC_` — they will be exposed to the client.

## SQL injection (Supabase / raw queries)

```typescript
// Safe — Supabase query builder
const { data } = await supabase.from("users").select("*").eq("id", userId)

// Safe — parameterized if using raw SQL
await db.query("SELECT * FROM users WHERE id = $1", [userId])

// Forbidden — string interpolation
await db.query(`SELECT * FROM users WHERE id = '${userId}'`)
```

## Dependency security

```bash
npm audit --audit-level=high  # in CI — block on high/critical
```

## Prototype pollution

```typescript
// Forbidden — merging untrusted objects
Object.assign(target, userInput)

// Safe — validate shape with Zod first, then spread
const validated = Schema.parse(userInput)
Object.assign(target, validated)
```

## Logging — never log sensitive data

```typescript
// Forbidden
logger.info("user login", { password: body.password, token })

// Good
logger.info("user login", { userId: user.id, email: user.email })
```
