---
name: frontend-patterns
description: Next.js App Router patterns — Server Components, data fetching, forms, state management, performance
triggers:
  - "frontend"
  - "next.js"
  - "app router"
  - "react"
  - "server component"
  - "frontend patterns"
---

# Skill — Frontend Patterns (Next.js App Router)

## Folder structure

```
app/
  (auth)/
    login/
      page.tsx
  (dashboard)/
    layout.tsx          # shared layout for dashboard routes
    page.tsx            # dashboard home
    orders/
      page.tsx          # order list — Server Component
      [id]/
        page.tsx        # order detail
  api/
    orders/
      route.ts

components/
  ui/                   # pure presentational components (no data fetching)
  features/             # domain-aware components (may fetch data)
  layouts/              # structural components

lib/
  services/             # client-side service functions (fetch wrappers)
  hooks/                # custom React hooks
  utils/                # pure utilities
```

## Server Component — default pattern

```tsx
// app/orders/page.tsx
import { orderService } from "@/lib/services/orders"

export default async function OrdersPage() {
  const orders = await orderService.findAll()

  return (
    <main>
      <h1>Orders</h1>
      <OrderList orders={orders} />
    </main>
  )
}
```

No `useState`, no `useEffect`, no data fetching in client components unless necessary.

## Client Component — only when needed

```tsx
"use client"

import { useState } from "react"

export function OrderFilters({ onFilter }: { onFilter: (status: string) => void }) {
  const [status, setStatus] = useState("all")

  return (
    <select
      value={status}
      onChange={(e) => {
        setStatus(e.target.value)
        onFilter(e.target.value)
      }}
    >
      <option value="all">All</option>
      <option value="pending">Pending</option>
    </select>
  )
}
```

## Data fetching patterns

```tsx
// Server Component — direct call (no fetch needed)
const orders = await db.query("...")

// Server Component — via service
const orders = await orderService.findAll({ userId })

// Client Component — SWR for live data
"use client"
import useSWR from "swr"

export function LiveOrderStatus({ orderId }: { orderId: string }) {
  const { data } = useSWR(`/api/orders/${orderId}`, fetcher, {
    refreshInterval: 5000,
  })
  return <span>{data?.status ?? "loading..."}</span>
}

// Server Action — form submission
"use server"
export async function createOrder(formData: FormData) {
  const input = CreateOrderSchema.parse({
    userId: formData.get("userId"),
    items: JSON.parse(formData.get("items") as string),
  })
  return orderService.create(input)
}
```

## Loading and error boundaries

```
app/orders/
  page.tsx        # main content
  loading.tsx     # shown while page.tsx is suspended
  error.tsx       # shown when page.tsx throws
  not-found.tsx   # shown when notFound() is called
```

```tsx
// loading.tsx
export default function Loading() {
  return <OrderListSkeleton />
}

// error.tsx
"use client"
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p>Something went wrong</p>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

## Forms with React Hook Form + Zod

```tsx
"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { CreateOrderSchema, type CreateOrderInput } from "@/lib/schemas/order"

export function CreateOrderForm({ onSubmit }: { onSubmit: (data: CreateOrderInput) => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateOrderInput>({
    resolver: zodResolver(CreateOrderSchema),
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("notes")} placeholder="Notes" />
      {errors.notes && <p role="alert">{errors.notes.message}</p>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create Order"}
      </button>
    </form>
  )
}
```

## Shared layouts

```tsx
// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
```

## Performance rules

- Images: always `next/image` with explicit `width` and `height`
- Fonts: `next/font` — auto-optimization, no layout shift
- Icons: `lucide-react` — tree-shakeable
- Heavy components: `dynamic(() => import(...), { loading: () => <Skeleton /> })`
- Lists: stable `key` prop — never array index

## Metadata

```tsx
// app/orders/page.tsx
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Orders",
  description: "Manage your orders",
}
```
