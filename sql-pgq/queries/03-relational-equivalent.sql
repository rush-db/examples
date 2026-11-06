SELECT c.name AS customer_name, o.order_id
FROM customers c
JOIN rushdb_edges.customer_orders co ON co.__source_id = c.__id
JOIN orders o ON o.__id = co.__target_id
WHERE to_timestamp_millis(o.ordered_when) >= TIMESTAMP '2026-10-30'
ORDER BY o.order_id
