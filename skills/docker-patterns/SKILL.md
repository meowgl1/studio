---
name: docker-patterns
description: Docker and Docker Compose best practices for local development and production builds
triggers:
  - "add docker"
  - "dockerize"
  - "docker compose"
  - "containerize"
  - "multi-stage build"
---

# Skill — Docker Patterns

## Multi-stage Dockerfile

```dockerfile
# ── Development stage ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS dev

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app/ ./app/

# Run as non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

## Docker Compose — local development

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app           # bind mount for hot reload
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/dev
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    env_file:
      - .env.local

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## .dockerignore

```
.git
.env*
__pycache__
*.pyc
node_modules
.next
dist
.pytest_cache
*.egg-info
```

## Security hardening

```dockerfile
# Pin exact versions — never use :latest in production
FROM python:3.12.3-slim

# Drop Linux capabilities
# Add to docker-compose:
# cap_drop:
#   - ALL
# cap_add:
#   - NET_BIND_SERVICE  # only if binding to port < 1024

# Read-only filesystem where possible
# security_opt:
#   - no-new-privileges:true
```

## Environment management

- Development: `.env.local` (git-ignored)
- CI: environment variables injected by CI platform
- Production: secrets manager or platform env vars — never baked into image

```bash
# Template to commit — no real values
cp .env.example .env.local
```

## Docker Compose for Next.js frontend

```yaml
  web:
    build:
      context: ./web
      target: dev
    ports:
      - "3000:3000"
    volumes:
      - ./web:/app
      - /app/node_modules   # anonymous volume — don't overwrite container's node_modules
      - /app/.next          # keep build cache in container
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Key rules

- `docker-compose` is for **local development only** — not production
- Use named volumes for persistence, bind mounts for hot reload
- Always add a `healthcheck` to DB services — use `depends_on: condition: service_healthy`
- Never hardcode secrets in Dockerfile or docker-compose.yml
- Use specific image tags — `:alpine` variants for smaller images
