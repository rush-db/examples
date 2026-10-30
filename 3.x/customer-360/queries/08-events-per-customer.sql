SELECT c.email, c.plan, COUNT(e.__id) AS events
FROM customer c
LEFT JOIN rushdb_edges.performed_by p ON p.__target_id = c.__id
LEFT JOIN product_event e ON e.__id = p.__source_id
GROUP BY c.email, c.plan
ORDER BY events DESC, c.email;
