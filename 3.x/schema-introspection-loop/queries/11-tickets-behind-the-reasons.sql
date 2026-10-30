SELECT c.name, c.cancel_reason, t.topic, t.subject
FROM customer c
JOIN rushdb_edges.opened e ON e.__source_id = c.__id
JOIN ticket t ON t.__id = e.__target_id
WHERE c.segment = 'ENTERPRISE'
  AND to_timestamp_millis(c.canceled_at) >= TIMESTAMP '2026-03-01'
ORDER BY c.name, t.opened_at;
