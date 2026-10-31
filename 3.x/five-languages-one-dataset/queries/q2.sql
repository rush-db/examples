SELECT DISTINCT c.name
FROM customer c
JOIN rushdb_edges.placed pl ON pl.__source_id = c.__id
JOIN rushdb_edges.contains ct ON ct.__source_id = pl.__target_id
JOIN product p ON p.__id = ct.__target_id
WHERE p.name = 'Paper filters'
ORDER BY c.name
