---
scope: global
applies-to: "**/*.tsx"
---

# React / Next.js — Patterns

## Component rules

- Functional components only — no class components
- One component per file — file name matches component name
- Props typed with inline `interface` or `type` — never `any`
- Export component as named export, not default (better refactoring)

```typescript
interface UserCardProps {
  user: User
  onEdit?: (id: string) => void
}

export function UserCard({ user, onEdit }: UserCardProps) {
  return (
    <div>
      <span>{user.name}</span>
      {onEdit && <button onClick={() => onEdit(user.id)}>Edit</button>}
    </div>
  )
}
```

## Server Components (default)

Use Server Components unless you need:
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`window`, `localStorage`)
- React state or effects
- Third-party libraries that require client context

```typescript
// Server Component — no directive needed
export default async function OrdersPage() {
  const orders = await orderService.findAll()  // direct DB call
  return <OrderList orders={orders} />
}
```

## Client Components — minimize surface area

Push `'use client'` as deep as possible:

```typescript
// Bad — entire page becomes client component
"use client"
export default function OrdersPage() { ... }

// Good — only the interactive part is client
// OrdersPage.tsx (Server Component)
export default async function OrdersPage() {
  const orders = await orderService.findAll()
  return <OrderList orders={orders} />  // OrderList is a Server Component
  // Only the sort button inside is a Client Component
}
```

## Performance — avoid unnecessary re-renders

```typescript
// Memoize expensive components
const OrderRow = memo(function OrderRow({ order }: { order: Order }) { ... })

// Stable callback references
const handleDelete = useCallback((id: string) => {
  deleteOrder(id)
}, [])  // only recreates if deleteOrder changes

// Expensive calculations
const total = useMemo(() => orders.reduce((sum, o) => sum + o.total, 0), [orders])
```

Use these only when you can measure the performance problem.  
Do not add `memo`, `useCallback`, `useMemo` preemptively everywhere.

## Forms

Use React Hook Form for non-trivial forms:

```typescript
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"

export function CreateUserForm({ onSubmit }: { onSubmit: (data: CreateUserInput) => void }) {
  const { register, handleSubmit, formState: { errors } } = useForm<CreateUserInput>({
    resolver: zodResolver(CreateUserSchema),
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <span>{errors.email.message}</span>}
    </form>
  )
}
```

## Data fetching — Next.js App Router

```typescript
// Server Component — best for SEO and initial load
export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await productService.findById(params.id)
  if (!product) notFound()
  return <ProductDetail product={product} />
}

// Client-side fetching — only when data changes after interaction
"use client"
export function LivePriceDisplay({ productId }: { productId: string }) {
  const { data } = useSWR(`/api/prices/${productId}`, fetcher, { refreshInterval: 5000 })
  return <span>{data?.price}</span>
}
```

## Key rules for lists

```typescript
// Good — stable unique key
orders.map(order => <OrderRow key={order.id} order={order} />)

// Forbidden — index as key (causes re-render bugs on reorder/delete)
orders.map((order, i) => <OrderRow key={i} order={order} />)
```

## Loading and error states

```typescript
// app/users/loading.tsx — automatic Suspense boundary
export default function Loading() {
  return <UserListSkeleton />
}

// app/users/error.tsx — automatic error boundary
"use client"
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <div>Something went wrong. <button onClick={reset}>Retry</button></div>
}
```
