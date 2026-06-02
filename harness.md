---
scope: global
applies-to: all projects
---

# Harness Engineering — Standards

Rules for every project. Override only in project `context.md` with explicit justification.

---

## 1 — Schema-first

- NEVER use LLM output directly — validate with Pydantic (Python) or Zod (TypeScript) before ANY operation
- NEVER insert to DB, return to caller, or pass to next stage without passing schema validation
- Define output schema BEFORE writing the prompt — schema is part of the spec
- Prompt MUST include the expected output schema as part of the instruction
- Validation failure = explicit error with context, never silent discard

## 2 — Evals-driven

- NEVER modify a prompt without running it against `golden_dataset` first
- New feature minimum: 20 golden examples before first deploy
- Production feature minimum: 50 golden examples
- Eval result drops below baseline → revert, do not ship
- Golden examples live in `golden_dataset.json` at project root — never in tests only
- Add a golden example BEFORE fixing a bug (regression prevention)

## 3 — Context engineering

- NEVER send raw HTML, raw document text, or unprocessed input to LLM
- Strip before sending: `<script>`, `<style>`, nav, footer, header, ads, cookie banners
- Target: under 3000 input tokens per LLM call unless justified in spec
- Rule: more relevant context beats more total context
- Build context in a dedicated function — never inline inside the prompt string

## 4 — Failure-aware design

- ALWAYS use exception chaining: `raise NewError("context: what failed") from original_exception`
- ALWAYS retry LLM calls: max 3 attempts, exponential backoff (1s → 2s → 4s)
- ALWAYS return partial results on batch failure — never discard completed work
- NEVER swallow exceptions silently — every catch must log or re-raise
- Timeout all LLM calls explicitly — never rely on default client timeout
- Concurrency: use `asyncio.Semaphore(N)` or promise pool — never unbounded `Promise.all` on large inputs

## 5 — Observability

- LOG every LLM call: `model · input_tokens · output_tokens · latency_ms · success · error_type · cost_est`
- Write to structured log (DB table or append-only file) — not just console
- NEVER optimize a prompt or model without before/after metrics
- Cost tracking: session-tracker appends summary to `.studio/changelog.md` at session end
- Alert condition: success_rate < 0.9 on any extractor/agent = investigate before shipping