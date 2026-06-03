---
scope: global
applies-to: "**/*.ts, **/*.tsx"
---

# JavaScript / TypeScript — Testing

## Stack

`Jest` + `Supertest` for API tests.  
`Playwright` for E2E.  
`@testing-library/react` for component tests.

## Jest config

```typescript
// jest.config.ts
export default {
  preset: "ts-jest",
  testEnvironment: "node",  // "jsdom" for frontend
  coverageThreshold: { global: { lines: 80 } },
  moduleNameMapper: { "^@/(.*)$": "<rootDir>/src/$1" },
}
```

## Unit test example

```typescript
describe("UserService.register", () => {
  it("throws ConflictError when email already exists", async () => {
    const mockRepo = { findByEmail: jest.fn().mockResolvedValue({ id: "1" }) } as any
    const service = new UserService(mockRepo)

    await expect(service.register({ email: "taken@test.com" }))
      .rejects.toThrow(ConflictError)
  })

  it("creates user when email is available", async () => {
    const mockRepo = {
      findByEmail: jest.fn().mockResolvedValue(null),
      create: jest.fn().mockResolvedValue({ id: "new", email: "new@test.com" }),
    } as any
    const service = new UserService(mockRepo)

    const result = await service.register({ email: "new@test.com" })

    expect(result.id).toBe("new")
    expect(mockRepo.create).toHaveBeenCalledWith({ email: "new@test.com" })
  })
})
```

## API integration test

```typescript
import request from "supertest"
import { app } from "@/app"

describe("POST /users", () => {
  it("returns 201 with created user", async () => {
    const res = await request(app)
      .post("/users")
      .send({ email: "test@test.com", name: "Test" })

    expect(res.status).toBe(201)
    expect(res.body.data.email).toBe("test@test.com")
  })

  it("returns 422 for invalid email", async () => {
    const res = await request(app).post("/users").send({ email: "not-an-email" })
    expect(res.status).toBe(422)
  })
})
```

## Component test

```typescript
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { LoginForm } from "@/components/LoginForm"

it("calls onSubmit with email and password when form is submitted", async () => {
  const onSubmit = jest.fn()
  render(<LoginForm onSubmit={onSubmit} />)

  await userEvent.type(screen.getByLabelText("Email"), "test@test.com")
  await userEvent.type(screen.getByLabelText("Password"), "secret123")
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(onSubmit).toHaveBeenCalledWith({ email: "test@test.com", password: "secret123" })
})
```

## Mocking

```typescript
// Mock module
jest.mock("@/lib/email", () => ({ sendEmail: jest.fn() }))

// Mock fetch
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ data: [] }),
})
```

Never mock Supabase in integration tests — use a real test project.

## Coverage

```bash
jest --coverage --coverageThreshold='{"global":{"lines":80}}'
```

Run coverage in CI — fail build if below threshold.
