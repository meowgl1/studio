---
scope: global
applies-to: "**/*.py"
---

# Python — Testing

## Stack

`pytest` + `pytest-asyncio` + `httpx.AsyncClient` for API tests.

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## File structure

```
tests/
  unit/
    test_user_service.py
    test_order_service.py
  integration/
    test_user_api.py
    test_orders_api.py
  conftest.py
```

## Fixtures — conftest.py

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import get_test_db

@pytest.fixture(scope="session")
def db():
    return get_test_db()  # real test DB, not mock

@pytest.fixture
async def client(db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def auth_client(client, db):
    """Authenticated client with a seeded test user."""
    user = await db.table("users").insert({"email": "test@test.com", ...}).execute()
    token = create_token(user.data[0]["id"])
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
```

## Unit test example

```python
@pytest.mark.asyncio
async def test_returns_none_when_user_not_found(mock_repo):
    service = UserService(repo=mock_repo)
    mock_repo.find_by_id.return_value = None

    result = await service.get_user("nonexistent-id")

    assert result is None
```

## Integration test example

```python
@pytest.mark.asyncio
async def test_creates_user_and_returns_201(auth_client):
    response = await auth_client.post("/users", json={"email": "new@test.com"})

    assert response.status_code == 201
    assert response.json()["data"]["email"] == "new@test.com"
```

## Mocking

- Mock external services (email, Stripe, third-party APIs) with `unittest.mock.AsyncMock`
- **Never mock Supabase** in integration tests — use a real test project/schema
- Mock at the repository boundary when testing services in isolation

```python
@pytest.fixture
def mock_email_service():
    with patch("app.services.email.EmailService.send") as mock:
        mock.return_value = None
        yield mock
```

## Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

Target: 80% line coverage minimum. Not a vanity metric — tests must cover real logic.

## Parametrize for edge cases

```python
@pytest.mark.parametrize("email", ["", "not-an-email", "a@", "@b.com"])
async def test_rejects_invalid_emails(client, email):
    response = await client.post("/users", json={"email": email})
    assert response.status_code == 422
```
