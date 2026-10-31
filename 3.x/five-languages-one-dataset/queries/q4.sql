SELECT other.name AS product, count(DISTINCT pl1.__source_id) AS customers
FROM product p
JOIN rushdb_edges.contains c1 ON c1.__target_id = p.__id
JOIN rushdb_edges.placed pl1 ON pl1.__target_id = c1.__source_id
JOIN rushdb_edges.placed pl2 ON pl2.__source_id = pl1.__source_id
JOIN rushdb_edges.contains c2 ON c2.__source_id = pl2.__target_id
JOIN product other ON other.__id = c2.__target_id
WHERE p.name = 'Paper filters' AND other.name <> 'Paper filters'
GROUP BY other.name
ORDER BY customers DESC, product
