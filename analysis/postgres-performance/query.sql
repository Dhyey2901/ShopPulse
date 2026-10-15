-- Customer order-history lookup: a "show me this customer's orders" page,
-- one of the most common query shapes in an e-commerce app.
SELECT o.order_id, o.status, oi.product_id, oi.sale_price
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.user_id = 33685;
