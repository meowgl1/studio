---
scope: global
applies-to: all projects
---

# Stack — Mowgli Studio Tech Decisions

Final decisions. No exploration of alternatives during a session.  
Override: add `Stack override: [item] → [replacement] because [reason]` to project `context.md`.

---

## Python backend

| Decision | Value |
|----------|-------|
| Data models | Pydantic v2 — always, for all data structures |
| Async | asyncio — `asyncio.gather` + `Semaphore(N)`, never sequential loops on I/O |
| HTTP client | httpx (async) |
| DB client | supabase-py |
| Testing | pytest + pytest-asyncio |
| Formatter | black + isort |
| Type hints | required on all public functions — no `Any` |

## TypeScript / Node.js backend

| Decision | Value |
|----------|-------|
| TypeScript | strict mode always — `noImplicitAny: true`, no `any` |
| Schema validation | Zod — every request body, every LLM output |
| HTTP framework | Fastify (preferred) or Express |
| DB client | @supabase/supabase-js |
| Testing | Jest + Supertest |
| Formatter | Prettier + ESLint |

## Frontend

| Decision | Value |
|----------|-------|
| Framework | Next.js — App Router only, NOT pages router |
| Language | TypeScript strict |
| Images | next/image — always, with explicit width + height |
| CSS | CSS Modules or Tailwind — check project context.md |
| Icons | lucide-react |
| Server/Client split | Server Components by default, `'use client'` only when required |
| **NO** | styled-components, emotion, jQuery, class components, create-react-app |

## AI / LLM

| Decision | Value |
|----------|-------|
| Cloud LLM | Claude via Anthropic SDK, Gemini API|
| Local LLM | Ollama |
| Output handling | Always Pydantic (Python) or Zod (TS) — never raw string parsing of LLM output |
| Concurrency | Promise pool / asyncio.Semaphore — never unbounded parallel LLM calls |
| **NO** | LangChain (too heavy), free-form LLM output, LlamaIndex (unless baloo explicitly) |

## Database

| Decision | Value |
|----------|-------|
| Primary | Supabase — PostgreSQL + Storage |
| Vector search | pgvector via Supabase (default) or Pinecone (if scale justifies) |
| Cache | Redis — only if rate limiting or semantic cache required |
| Migrations | Supabase CLI — never modify schema manually in production |

## Infrastructure

| Decision | Value |
|----------|-------|
| Containers | Docker + Docker Compose |
| Frontend hosting | Vercel |
| Backend hosting | Supabase (BaaS) or Dockerized service |
| **NO** | Plain VPS/EC2 without Docker, serverless Lambda without explicit justification |

---

## MCP Servers

Catalog of available MCP servers. Enable per-project via `.claude/settings.json` → `mcpServers`.  
Document which are active in each project's `.studio/mcp.md`.

| Server           | Use when                                        | Stack tie-in              |
|------------------|-------------------------------------------------|---------------------------|
| `vercel`         | Any project deployed on Vercel                  | Frontend hosting          |
| `figma`          | Projects with design ↔ code sync                | Design system work        |
| `supabase`       | Direct DB/Storage inspection during dev         | Primary DB                |
| `shopify`        | E-commerce projects                             | Project-specific          |
| `klaviyo`        | Email marketing flows                           | Project-specific          |
| `gmail`          | Email automation or inbox workflows             | Project-specific          |
| `google-drive`   | Document-heavy workflows                        | Project-specific          |

**Default for new projects:** enable `vercel` if deployed on Vercel; enable `figma` if design files exist.  
All others: opt-in only when the project explicitly uses that service.

---

## Project-specific design systems

Design tokens, fonts, and color palettes are project-specific.  
See individual project `context.md` — not defined here.