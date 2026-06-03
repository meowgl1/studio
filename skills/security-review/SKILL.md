---
name: security-review
description: Run a structured security audit on a codebase or PR — OWASP Top 10, secrets, auth, SQL injection
triggers:
  - "security review"
  - "security audit"
  - "check for vulnerabilities"
  - "owasp"
  - "is this secure"
---

# Skill — Security Review

## Process

1. Read all changed or targeted files — do not skim
2. Check each category below
3. Report findings by severity: Critical → High → Medium → Low
4. For each finding: file path, line, issue, fix

## Category checklist

### Secrets and credentials
- [ ] No hardcoded API keys, passwords, tokens in source code
- [ ] No secrets in comments
- [ ] Environment variables validated at startup (not silently defaulting to empty)
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in log output

### Injection
- [ ] All SQL via parameterized queries or ORM — no string interpolation
- [ ] No `eval()`, `exec()`, or dynamic code execution on user input
- [ ] No shell injection: `subprocess.run` with `shell=False` and args as list
- [ ] HTML output properly escaped (React does this by default — check `dangerouslySetInnerHTML`)

### Authentication and authorization
- [ ] All state-changing endpoints require authentication
- [ ] JWT signature verified (not just decoded)
- [ ] JWT expiry checked
- [ ] Role/permission checks present on admin and sensitive endpoints
- [ ] No authentication logic bypassed by parameter manipulation

### Input validation
- [ ] All user inputs validated with Pydantic/Zod before use
- [ ] Path parameters and query strings validated (not just body)
- [ ] File uploads: type and size validated, stored outside web root
- [ ] No unsafe deserialization of untrusted data

### CSRF and session
- [ ] SameSite cookie attribute set (`Strict` or `Lax`)
- [ ] Session tokens not logged or exposed in URLs
- [ ] Logout actually invalidates the session/token

### Information disclosure
- [ ] Stack traces not returned in API responses
- [ ] Internal paths, table names, DB structure not in error messages
- [ ] Sensitive fields (passwords, tokens) not in API responses or logs

### Dependency vulnerabilities
- [ ] `pip audit` / `npm audit` has been run
- [ ] No known critical CVEs in dependencies

### Rate limiting
- [ ] Auth endpoints (login, password reset) have rate limiting
- [ ] Public endpoints have rate limiting to prevent abuse

## Output format

```
## Critical
- app/routers/auth.py:42 — JWT decoded without signature verification
  Fix: use `jwt.decode(token, secret, algorithms=["HS256"])` not `jwt.decode(token, options={"verify_signature": False})`

## High
- app/repositories/user.py:78 — SQL string interpolation
  Fix: replace f-string query with parameterized `.eq("id", user_id)` call

## Medium
- .env.example contains real API key value
  Fix: replace with placeholder `STRIPE_KEY=sk_test_REPLACE_ME`

## Low
- app/main.py:12 — debug=True in production config path
  Note: verify this is never reached in production

## Clean
- Authentication: ✓ JWT verification correct
- Input validation: ✓ All endpoints use Pydantic models
```

## When to invoke this skill

- Before merging any auth-related PR
- Before deploying a new public endpoint
- When adding file upload functionality
- When adding third-party integrations
- When a vulnerability is suspected (`security-reviewer` agent handles incident response)
