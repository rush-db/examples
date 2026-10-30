SELECT count(*) AS customers
FROM customer
WHERE segment = 'ENTERPRISE'
  AND to_timestamp_millis(canceled_at) >= TIMESTAMP '2026-03-01';
