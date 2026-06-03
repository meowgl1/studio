---
scope: global
applies-to: "**/*.sql, Supabase migrations"
---

# SQL — Coding Style

## Formatting

- Keywords: `UPPERCASE` — `SELECT`, `FROM`, `WHERE`, `JOIN`, `ON`, `ORDER BY`
- Identifiers: `snake_case` — tables, columns, functions, indexes
- One clause per line for readability
- Indent continuation lines by 2 spaces

```sql
SELECT
  u.id,
  u.email,
  u.created_at,
  o.total AS order_total
FROM users u
INNER JOIN orders o ON o.user_id = u.id
WHERE u.active = TRUE
  AND o.created_at >= NOW() - INTERVAL '30 days'
ORDER BY o.created_at DESC
LIMIT 100;
```

## Naming conventions

| Object | Convention | Example |
|--------|-----------|---------|
| Tables | plural, snake_case | `users`, `order_items` |
| Columns | snake_case | `created_at`, `user_id` |
| Primary key | `id` | always `id uuid DEFAULT gen_random_uuid()` |
| Foreign key | `{table_singular}_id` | `user_id`, `product_id` |
| Indexes | `idx_{table}_{column(s)}` | `idx_orders_user_id` |
| Functions | verb_noun | `get_user_by_email`, `calculate_order_total` |
| Boolean columns | `is_`, `has_`, `can_` | `is_active`, `has_verified_email` |

## Standard columns on every table

```sql
CREATE TABLE users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Always add `updated_at` trigger:

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

## NULL handling

- Be explicit about `NOT NULL` — default to `NOT NULL` unless null is meaningful
- Use `COALESCE(column, default)` explicitly — do not rely on implicit null coercion
- Never compare with `= NULL` — always `IS NULL` or `IS NOT NULL`

## Comments

Add a comment on non-obvious columns:

```sql
-- stores the Stripe customer ID for billing operations
stripe_customer_id TEXT,
```

Add a comment on complex queries explaining the business intent, not what SQL does.

## Migrations

- Use Supabase CLI — never modify schema manually in production
- Migration files: sequential numbered prefixes `20240101_add_user_roles.sql`
- Each migration is atomic — one logical change
- Migrations must be reversible (include rollback SQL as comment if needed)
- Never drop a column without first making it nullable in a prior migration
