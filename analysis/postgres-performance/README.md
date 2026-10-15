# Postgres indexing: before/after on a customer order-history lookup

ShopPulse's pipeline runs entirely on BigQuery, which doesn't expose `EXPLAIN ANALYZE` plans or let you add secondary indexes the way a transactional database does. This is a quick, separate exercise to show query-plan and indexing fundamentals on the same underlying data: `orders` and `order_items` loaded from `bigquery-public-data.thelook_ecommerce` into a local PostgreSQL 17 instance (125,004 orders, 181,081 order items).

## The query

A customer order-history lookup — "show me this user's orders," one of the most common query shapes in any e-commerce app:

```sql
SELECT o.order_id, o.status, oi.product_id, oi.sale_price
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.user_id = 33685;
```

Tables start with only their primary keys indexed (`orders.order_id`, `order_items.id`) — nothing on `user_id` or `order_items.order_id`, which is a realistic starting point for a table created without thinking about access patterns yet.

## Before: full table scans

```text
Gather  (cost=3215.16..6736.26 rows=3 width=26) (actual time=17.840..29.043 rows=10 loops=1)
  Workers Planned: 1
  Workers Launched: 1
  Buffers: shared hit=3569
  ->  Parallel Hash Join  (actual time=10.379..20.292 rows=5 loops=2)
        Hash Cond: (oi.order_id = o.order_id)
        ->  Parallel Seq Scan on order_items oi  (actual time=0.011..6.429 rows=90540 loops=2)
              Buffers: shared hit=2176
        ->  Parallel Hash  (actual time=7.258..7.258 rows=2 loops=2)
              ->  Parallel Seq Scan on orders o  (actual time=2.026..7.221 rows=2 loops=2)
                    Filter: (user_id = 33685)
                    Rows Removed by Filter: 62500
                    Buffers: shared hit=1296
Planning Time: 1.360 ms
Execution Time: 29.146 ms
```

Postgres can't jump to `user_id = 33685` without an index, so it reads every row in both tables (125K + 181K rows, 3,569 buffer pages touched) in parallel, just to find the 4 matching orders and their 10 line items.

## The fix

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

One index on the filter column, one on the join column.

## After: index scans

```text
Nested Loop  (cost=8.87..36.82 rows=3 width=26) (actual time=0.107..0.181 rows=10 loops=1)
  Buffers: shared hit=24 read=4
  ->  Bitmap Heap Scan on orders o  (actual time=0.059..0.068 rows=4 loops=1)
        Recheck Cond: (user_id = 33685)
        ->  Bitmap Index Scan on idx_orders_user_id  (actual time=0.044..0.044 rows=4 loops=1)
              Index Cond: (user_id = 33685)
  ->  Bitmap Heap Scan on order_items oi  (actual time=0.017..0.025 rows=2 loops=4)
        Recheck Cond: (o.order_id = order_id)
        ->  Bitmap Index Scan on idx_order_items_order_id  (actual time=0.008..0.008 rows=2 loops=4)
              Index Cond: (order_id = o.order_id)
Planning Time: 1.984 ms
Execution Time: 0.321 ms
```

The planner switches from a parallel hash join over full scans to a nested loop driven by two bitmap index scans — it jumps straight to the matching rows instead of reading the tables.

## Result

| | Before | After |
| --- | --- | --- |
| Plan | Parallel Seq Scan + Hash Join | Bitmap Index Scan + Nested Loop |
| Buffer pages touched | 3,569 | 24 (+4 read from disk) |
| Execution time | 29.146 ms | 0.321 ms |

**~91x faster**, and the gap only widens as the tables grow — the "before" plan is O(table size) per query regardless of how selective the filter is; the "after" plan is effectively O(log n) plus the size of the actual result set.

## Reproduce it

```bash
createdb shoppulse_perf
psql shoppulse_perf -f schema.sql
# load orders.csv / order_items.csv exported from
# bigquery-public-data.thelook_ecommerce via \copy ... FROM '...' WITH (FORMAT csv, HEADER true)
psql shoppulse_perf -c "EXPLAIN (ANALYZE, BUFFERS) $(cat query.sql)"   # before
psql shoppulse_perf -f indexes.sql
psql shoppulse_perf -c "EXPLAIN (ANALYZE, BUFFERS) $(cat query.sql)"   # after
```
