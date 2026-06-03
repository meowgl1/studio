---
scope: global
applies-to: all projects
---

# Security — Common Rules

## Secrets — absolute rules

- **Never** hardcode credentials, tokens, or keys in source code
- All secrets from environment variables or a secrets manager
- Validate all required secrets are present at startup — fail immediately if missing
- Rotate any secret that has been exposed — do not wait

## Input validation (OWASP Top 10)

- Validate at every boundary — HTTP body, query params, headers, CLI args, queue messages
- Schema-first validation (Pydantic / Zod) — no manual if-chains
- **SQL injection:** parameterized queries only — never string interpolation in SQL
- **XSS:** sanitize HTML output — never render raw user input as HTML
- **Path traversal:** validate and normalize file paths before use

## Authentication & authorization

- Verify JWT signature and expiry on every protected request
- RBAC: define roles and permissions explicitly — no implicit access
- Deny by default — explicit allowlist, not blocklist
- Never expose internal IDs in public APIs when avoidable (use UUIDs)

## CSRF

- Use CSRF tokens for state-changing form submissions
- SameSite cookie attribute: `Strict` or `Lax`

## Rate limiting

- Apply rate limiting at gateway or platform level — not in-process memory
- Return `429 Too Many Requests` with `Retry-After` header

## Error messages

- Never expose stack traces, internal paths, or DB schema in error responses
- Log full details server-side, return generic message client-side

## Dependency security

- Pin dependency versions in production
- Run `pip audit` / `npm audit` in CI — block on critical vulnerabilities

## Incident response

1. Stop development on affected code
2. Invoke `security-reviewer` agent
3. Fix critical vulnerabilities before resuming
4. Rotate any potentially exposed credentials
5. Audit codebase for similar patterns
