-- The fix: index both sides of the join/filter.
-- user_id is the filter predicate on orders; order_id is the join key
-- on order_items. Neither was indexed (only the primary keys were).
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
