SELECT c.name, count(o.__id) AS orders, coalesce(sum(o.total), 0) AS spent
FROM customer c
LEFT JOIN rushdb_edges.placed pl ON pl.__source_id = c.__id
LEFT JOIN "ORDER" o ON o.__id = pl.__target_id
GROUP BY c.name
ORDER BY spent DESC
