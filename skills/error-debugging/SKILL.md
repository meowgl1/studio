---
name: error-debugging
description: Systematic error debugging — structured approach to reading error messages, tracing root causes, isolating layers, and applying fixes. Use this skill whenever the user reports an error, stack trace, crash, "it doesn't work", failing test, or unexpected behavior. Also use when debugging infrastructure issues (Docker, Ollama, DB connections) or when error messages are unclear.
---

# Skill — Error Debugging

Activate on: error message, stack trace, "doesn't work", "failed", crash, unexpected behavior, failing test, status code error, infrastructure issue.

---

## Phase 1 — Read the Error (don't guess)

Before touching code, extract these from the error output:

```
Error type:    [exception class / HTTP status / exit code]
Error message: [exact text — copy, don't paraphrase]
Location:      [file:line if available]
Stack trace:   [bottom frame = where it broke, top frame = where it started]
Trigger:       [what action caused it — user click, API call, startup, background job]
```

**Rules:**
- Read the FULL error message — the fix is often in the text
- Stack traces read bottom-up: last frame = crash point, first frame = entry point
- HTTP errors: the response body often has more detail than the status code
- Docker errors: check if the error is from the container or from the host
- Don't assume the error is where it looks — a 500 in route X may originate in service Y

---

## Phase 2 — Classify the Error

| Category | Signals | First action |
|----------|---------|--------------|
| **Import / Module** | `ModuleNotFoundError`, `Cannot find module`, `ImportError` | Check installed packages, check path, check typos |
| **Connection** | `ConnectionRefused`, `ECONNREFUSED`, `timeout`, `ConnectError` | Is the service running? Correct host/port? Firewall? |
| **Auth / Permission** | `401`, `403`, `PermissionDenied`, `EACCES` | Check tokens, API keys, file permissions, CORS |
| **Data / Schema** | `ValidationError`, `KeyError`, `TypeError`, `422` | Check input shape vs expected schema |
| **Not Found** | `404`, `FileNotFoundError`, `No such file`, `ENOENT` | Check path, check if resource exists, check naming |
| **Infrastructure** | `binary not found`, `command not found`, `ENOMEM` | Check installation, PATH, disk space, memory |
| **State / Race** | `IntegrityError`, `duplicate key`, `deadlock`, intermittent failures | Check concurrency, check unique constraints, check ordering |
| **Dependency** | `version mismatch`, `peer dependency`, `incompatible` | Check version pins, check compatibility matrix |

---

## Phase 3 — Isolate the Layer

Errors propagate through layers. Identify WHERE the actual failure is:

```
Frontend (browser/Next.js)
    ↓ HTTP request
API layer (route handler)
    ↓ function call
Service layer (business logic)
    ↓ I/O call
Infrastructure (DB / Vector DB / LLM / Queue / Filesystem)
    ↓ external call
External service (Ollama / Qdrant / Redis / third-party API)
```

**Isolation strategy:**
1. Start at the error point
2. Test the layer BELOW it directly (curl the API, query the DB, ping the service)
3. If the layer below works → bug is in the current layer
4. If the layer below fails → go one layer deeper
5. Repeat until you find the actual broken layer

**Quick checks per layer:**
- **External service:** `curl`, `ping`, `telnet`, service status command
- **Infrastructure:** connection string, env vars, service health endpoint
- **Service layer:** call the function directly in a REPL or test
- **API layer:** `curl` the endpoint with known-good input
- **Frontend:** browser console, network tab, check response body

---

## Phase 4 — Reproduce Minimally

Before fixing, create the smallest reproduction:

1. Strip away unrelated code/config
2. Use hardcoded values instead of dynamic input
3. Run the minimal case — does it fail the same way?
4. If yes → you've isolated the bug
5. If no → the bug depends on something you stripped — add back incrementally

**For infrastructure errors:**
- Check version: `ollama --version`, `docker --version`, `node --version`
- Check process: `ps aux | grep <service>`, `docker ps`
- Check logs: `docker logs <container>`, service log files
- Check config: env vars, config files, connection strings

---

## Phase 5 — Fix and Verify

1. **Fix one thing at a time** — don't stack multiple changes
2. **Verify the fix** — reproduce the original error path, confirm it's gone
3. **Check for collateral** — did the fix break anything adjacent?
4. **Add error handling** if the error could recur (network, external services):
   - Specific exception types, not bare `except`
   - Human-readable error messages for the user
   - Structured logging for the developer

**Verification checklist:**
- [ ] Original error no longer occurs
- [ ] Happy path still works
- [ ] Edge cases still work (empty input, invalid input, service offline)
- [ ] Error message is clear if the underlying issue recurs

---

## Anti-patterns — Avoid These

| Anti-pattern | Why it fails | Do instead |
|--------------|-------------|------------|
| Guess-and-check | Wastes time, may introduce new bugs | Read the error first |
| Change multiple things at once | Can't tell what fixed it | One change, then verify |
| Suppress the error | Hides the bug, breaks later | Fix root cause |
| "Works on my machine" | Environment difference IS the bug | Check env, versions, config |
| Blame the framework | Framework bugs are rare — your code is more likely | Check your code first |
| Restart and hope | Masks the issue, it will return | Understand why it failed |
| Add try/except everywhere | Error handling is not error fixing | Fix the cause, then handle the edge |

---

## Common Patterns by Stack

### Python / FastAPI
```
ImportError → pip install missing, or wrong virtualenv
ModuleNotFoundError → check __init__.py, check PYTHONPATH
pydantic.ValidationError → input doesn't match schema — read which field failed
httpx.ConnectError → target service not running
sqlalchemy.exc.OperationalError → DB connection issue or bad query
```

### Next.js / React
```
Hydration mismatch → server/client render different output — check dynamic content
"use client" missing → using hooks/state in server component
NEXT_PUBLIC_ missing → env var not prefixed, not available client-side
fetch failed → check API URL, CORS, backend running
```

### Docker / Infrastructure
```
"port already in use" → another process on that port — lsof -i :<port>
"binary not found" → not installed, or not in PATH
"connection refused" → service not started, wrong host/port
"no space left" → disk full — docker system prune
"permission denied" → file ownership, or missing sudo
```

### Ollama (local LLM)
```
"model not found" → ollama pull <model> first
"llama-server binary not found" → broken installation — reinstall from ollama.com/download
"connection refused :11434" → ollama serve not running
timeout → model loading into memory (first call), or model too large for RAM
```
