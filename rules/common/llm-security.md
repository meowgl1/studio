---
scope: global
applies-to: all projects with LLM features
ref: OWASP LLM Top 10 (2025)
---

# LLM Security — Common Rules

## LLM01 — Prompt Injection

- **Never** concatenate untrusted input directly into a system prompt or instruction string
- Treat all user-supplied content as data, not instructions — enforce structural separation
- Use a fixed system prompt; inject dynamic content only in clearly delimited `<user_input>` blocks
- When content comes from external sources (web scraping, documents, email), sanitize and label it explicitly before passing to the LLM
- Validate that the model's output matches the expected task — a response that ignores the task is a signal of injection

## LLM02 — Sensitive Information Disclosure

- Never include PII, secrets, or internal system details in prompts unless strictly necessary
- Strip sensitive fields from data before feeding to the LLM — apply field-level redaction upstream
- Do not log raw prompts or completions that may contain user data — log metadata only (tokens, latency, success)
- Instruct the model explicitly not to repeat back sensitive data in its responses

## LLM05 — Improper Output Handling

- **Always** validate and sanitize LLM output before any downstream operation — this is `harness.md` §1 (schema-first), applied to security
- Never pass raw LLM output to: `eval()`, `exec()`, `subprocess`, SQL queries, shell commands, or HTML render targets
- Parse and validate structured output (JSON, code, SQL) against a schema before use — Pydantic or Zod
- Treat LLM output as untrusted external input at every integration boundary

## LLM06 — Excessive Agency

- Apply least-privilege to every tool the LLM can call — only expose what the current task requires
- **Never** give an agent write access to production systems unless explicitly scoped and confirmed
- Destructive or irreversible tool calls must require human confirmation — never auto-execute
- Scope tool permissions per workflow phase — a research agent does not need write tools
- Cap the number of tool calls per session — detect and abort loops (`max_iterations`, timeout)
- Log every tool call with: tool name, input, output, timestamp — audit trail is mandatory

## LLM07 — System Prompt Leakage

- Do not put credentials, internal architecture details, or business logic in system prompts
- Assume any system prompt can be extracted by a determined user — it is not a secret
- Sensitive configuration belongs in environment variables, not prompt context

## LLM10 — Unbounded Consumption

- Set hard timeouts on all LLM calls — never `await` without a timeout
- Limit max output tokens per call — reject completions that exceed the expected range
- Apply rate limiting on LLM-facing endpoints — protect against prompt flooding
- Monitor token usage per user/session — alert on anomalous spikes
- Use `asyncio.Semaphore(N)` or equivalent to bound concurrent LLM calls — `harness.md` §4
