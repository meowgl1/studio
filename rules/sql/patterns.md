---
scope: global
applies-to: "**/*.sql, Supabase queries"
---

# SQL — Patterns

## Indexes — when to add

Add an index when:
- Column is used in `WHERE` clause frequently
- Column is used in `JOIN ON` conditions
- Column is used in `ORDER BY` on large tables
- Foreign key columns (Postgres does not auto-index FK columns)

```sql
-- Foreign key index
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Composite index for common filter + sort combo
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial index for active records only
CREATE INDEX idx_users_active_email ON users(email) WHERE is_active = TRUE;
```

Do not add indexes speculatively — they slow writes. Profile first.

## CTEs for readable complex queries

```sql
WITH
  active_users AS (
    SELECT id, email
    FROM users
    WHERE is_active = TRUE
      AND created_at >= NOW() - INTERVAL '90 days'
  ),
  recent_orders AS (
    SELECT user_id, COUNT(*) AS order_count, SUM(total) AS total_spent
    FROM orders
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY user_id
  )
SELECT
  u.email,
  COALESCE(o.order_count, 0) AS orders_last_30d,
  COALESCE(o.total_spent, 0) AS spent_last_30d
FROM active_users u
LEFT JOIN recent_orders o ON o.user_id = u.id
ORDER BY total_spent DESC;
```

## Preventing N+1 — use JOINs or subqueries

```sql
-- Forbidden pattern (in application code): query user, then loop to fetch orders
-- Correct: fetch everything in one query
SELECT
  u.id,
  u.email,
  json_agg(o.*) AS orders
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.email;
```

## Transactions

Use transactions for operations that must succeed or fail together:

```sql
BEGIN;

UPDATE inventory SET quantity = quantity - 1 WHERE product_id = $1 AND quantity > 0;

-- Check affected rows in application, rollback if 0
INSERT INTO orders (user_id, product_id, quantity) VALUES ($2, $1, 1);

COMMIT;
```

## Pagination — cursor-based (preferred over OFFSET)

```sql
-- Keyset pagination — efficient on large tables
SELECT id, created_at, title
FROM posts
WHERE created_at < $1  -- cursor from previous page
ORDER BY created_at DESC
LIMIT 20;
```

OFFSET pagination degrades on large tables (`OFFSET 10000` scans 10,000 rows).  
Use cursor-based for feeds, lists, anything >10k rows.

## Aggregations with window functions

```sql
SELECT
  user_id,
  order_date,
  total,
  SUM(total) OVER (PARTITION BY user_id ORDER BY order_date) AS running_total,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC) AS rank_by_value
FROM orders;
```

## Supabase RLS patterns

```sql
-- Users can only see their own data
CREATE POLICY "users_select_own"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Admins can see everything
CREATE POLICY "admins_select_all"
  ON users FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );
```

Always enable RLS on tables with user data:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```
