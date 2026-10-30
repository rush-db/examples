SELECT c.cancel_reason,
       count(DISTINCT c.__id) AS customers,
       count(e.__id) AS tickets
FROM customer c
LEFT JOIN rushdb_edges.opened e ON e.__source_id = c.__id
WHERE c.segment = 'ENTERPRISE'
  AND to_timestamp_millis(c.canceled_at) >= TIMESTAMP '2026-03-01'
GROUP BY c.cancel_reason
ORDER BY customers DESC, c.cancel_reason;
