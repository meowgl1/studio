---
scope: global
applies-to: "**/*.ts, **/*.tsx"
---

# JavaScript / TypeScript — Patterns

## Schema validation with Zod

Every request body and every LLM output must be validated with Zod:

```typescript
import { z } from "zod"

const CreateUserSchema = z.object({
  email: z.string().email(),
  role: z.enum(["admin", "user"]).default("user"),
  name: z.string().min(1).max(100),
})

type CreateUserInput = z.infer<typeof CreateUserSchema>

// In route handler:
const body = CreateUserSchema.parse(await request.json())
```

Never trust `request.json()` directly — always parse through Zod.

## Repository pattern

```typescript
interface UserRepository {
  findById(id: string): Promise<User | null>
  findAll(filters: UserFilters): Promise<User[]>
  create(data: CreateUserInput): Promise<User>
  update(id: string, data: Partial<User>): Promise<User>
  delete(id: string): Promise<void>
}

class SupabaseUserRepository implements UserRepository {
  constructor(private readonly db: SupabaseClient) {}

  async findById(id: string): Promise<User | null> {
    const { data } = await this.db.from("users").select("*").eq("id", id).maybeSingle()
    return data ? UserSchema.parse(data) : null
  }
}
```

## Service pattern

```typescript
class UserService {
  constructor(private readonly repo: UserRepository) {}

  async register(input: CreateUserInput): Promise<User> {
    const existing = await this.repo.findByEmail(input.email)
    if (existing) throw new ConflictError("email already in use")
    return this.repo.create(input)
  }
}
```

## Concurrent async operations

```typescript
// Good — parallel independent calls
const [user, orders] = await Promise.all([
  userRepo.findById(userId),
  orderRepo.findByUserId(userId),
])

// Good — bounded concurrency for large arrays
import pLimit from "p-limit"
const limit = pLimit(10)
const results = await Promise.all(ids.map(id => limit(() => fetch(id))))

// Forbidden — sequential I/O
for (const id of ids) {
  await fetch(id)  // one at a time
}
```

## Error handling

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number = 500,
  ) {
    super(message)
    this.name = "AppError"
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, "NOT_FOUND", 404)
  }
}
```

## Next.js — server vs client components

```typescript
// Default — Server Component (no directive needed)
export default async function UserProfile({ userId }: { userId: string }) {
  const user = await userService.findById(userId)  // direct async call
  return <div>{user.name}</div>
}

// Only when needed — Client Component
"use client"
export function LikeButton({ postId }: { postId: string }) {
  const [liked, setLiked] = useState(false)
  // ...
}
```

Rules for `'use client'`:
- Only for interactivity (click handlers, state, effects)
- Never just to use a hook that could be server-safe
- Push `'use client'` as deep as possible in the tree

## API route handlers (Next.js App Router)

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const body = CreateUserSchema.parse(await request.json())
  const user = await userService.create(body)
  return NextResponse.json({ success: true, data: user }, { status: 201 })
}
```
