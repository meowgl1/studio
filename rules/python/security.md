---
scope: global
applies-to: "**/*.py"
---

# Python — Security

## Never do this

```python
# FORBIDDEN — code execution from user input
eval(user_input)
exec(user_input)
__import__(user_provided_module)

# FORBIDDEN — shell injection
os.system(f"ls {user_path}")
subprocess.call(user_command, shell=True)

# FORBIDDEN — SQL string interpolation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

## Parameterized queries

Always use parameterized queries or ORM:

```python
# Safe — Supabase
result = await db.table("users").select("*").eq("id", user_id).execute()

# Safe — raw SQL with psycopg2
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

## Subprocess — safe usage

```python
# Safe — args as list, shell=False
result = subprocess.run(["git", "log", "--oneline"], capture_output=True, text=True)
```

## File path safety

```python
from pathlib import Path

def safe_path(base_dir: str, user_provided: str) -> Path:
    base = Path(base_dir).resolve()
    target = (base / user_provided).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("path traversal detected")
    return target
```

## Secrets management

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    jwt_secret: str

    class Config:
        env_file = ".env"

settings = Settings()  # fails at startup if any required secret is missing
```

Never use `os.environ.get("SECRET", "fallback")` for real secrets — missing secrets must crash.

## Password hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

Never store plain text passwords. Never use MD5/SHA1 for passwords.

## JWT validation

```python
import jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("token expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("invalid token")
```

Always verify signature + expiry. Never decode without verification.

## Dependency auditing

```bash
pip-audit  # run in CI — block on critical vulnerabilities
```

Pin versions in `pyproject.toml` or `requirements.txt` for production.
