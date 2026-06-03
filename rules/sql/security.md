---
scope: global
applies-to: "**/*.sql, Supabase projects"
---

# SQL — Security

## Parameterized queries — absolute rule

**Never** interpolate user input into SQL strings.

```python
# Forbidden
query = f"SELECT * FROM users WHERE email = '{email}'"

# Safe — Supabase Python client
result = await db.table("users").select("*").eq("email", email).execute()

# Safe — raw psycopg2
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

```typescript
// Forbidden
const query = `SELECT * FROM users WHERE email = '${email}'`

// Safe — Supabase JS client
const { data } = await supabase.from("users").select("*").eq("email", email)

// Safe — raw postgres
await db.query("SELECT * FROM users WHERE email = $1", [email])
```

## Row Level Security (RLS)

Enable RLS on every table that stores user data:

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
```

Default deny — add explicit policies for each operation:

```sql
-- Without this, no one can access the table
-- DENY is implicit when RLS is enabled and no matching policy exists

CREATE POLICY "select_own_orders"
  ON orders FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "insert_own_orders"
  ON orders FOR INSERT
  WITH CHECK (user_id = auth.uid());
```

## Function security

Use `SECURITY DEFINER` carefully — it runs with the function owner's privileges:

```sql
-- Only use SECURITY DEFINER when the function needs elevated access
-- Always restrict who can call it
CREATE FUNCTION admin_get_all_users()
RETURNS TABLE (id uuid, email text)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id, email FROM users;
$$;

-- Revoke from public, grant only to service role
REVOKE EXECUTE ON FUNCTION admin_get_all_users() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_get_all_users() TO service_role;
```

## Column-level permissions

Do not expose sensitive columns to the anon or authenticated role:

```sql
-- Revoke access to sensitive columns
REVOKE SELECT (hashed_password, stripe_customer_id) ON users FROM authenticated;

-- Or create a view that excludes them
CREATE VIEW public_profiles AS
  SELECT id, display_name, avatar_url, created_at
  FROM users;
```

## Audit logging

For sensitive operations (delete, admin actions):

```sql
CREATE TABLE audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name  TEXT NOT NULL,
  operation   TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
  row_id      UUID NOT NULL,
  actor_id    UUID,           -- who did it (nullable for system ops)
  old_data    JSONB,
  new_data    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Minimal privilege — service accounts

- Application reads → authenticated role (Supabase default)
- Migrations → postgres role (never expose in application code)
- Service operations that bypass RLS → service_role (only in backend, never client-side)

Never expose `service_role` key in frontend code or public repositories.

## Backup and encryption

- Enable point-in-time recovery on production Supabase projects
- Sensitive columns (SSN, payment data) → encrypt at application level before storing
- Supabase encrypts data at rest by default — do not store additional copies unencrypted
