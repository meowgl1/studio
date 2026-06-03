---
scope: global
applies-to: all projects
---

# Testing — Common Rules

## Coverage targets

- **Unit:** 80% minimum — all public functions
- **Integration:** all API endpoints + DB operations
- **E2E:** critical user workflows only (registration, checkout, key flows)

## TDD cycle (mandatory for new features)

1. Write failing test (RED) — describe expected behavior
2. Run test — confirm it fails for the right reason
3. Write minimum code to pass (GREEN)
4. Refactor — keep tests green
5. Confirm coverage target met

## Test structure — AAA pattern

```
# Arrange
user = create_user(role="admin")
# Act
result = service.delete_resource(resource_id, user)
# Assert
assert result.success is True
assert db.find(resource_id) is None
```

## Naming convention

Descriptive names that state the scenario and expected outcome:

```
test_returns_empty_list_when_no_results_match_filter
test_raises_unauthorized_when_token_is_expired
test_sends_email_when_order_is_confirmed
```

## What must be tested

- All public API endpoints (happy path + error paths)
- All service methods with business logic
- Edge cases: null/empty/invalid inputs, boundary values
- Error paths: what happens when dependencies fail

## What not to test

- Private implementation details
- Framework internals
- Trivial getters/setters with no logic

## Mocking rules

- Mock external services (email, payments, third-party APIs) — always
- **Never** mock your own DB in integration tests — use a real test DB
- Mock at the service boundary, not deep inside implementation

## When tests fail

Fix the implementation, not the test — unless the test itself has a bug.  
Do not comment out, skip, or relax assertions to make tests pass.

## Eval-driven additions

For AI/LLM features: define capability tests before implementing.  
Establish baseline, implement minimum change, report pass@1 and pass@3 metrics.
