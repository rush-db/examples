SELECT e.name, c.name AS company, COUNT(*) AS works_at_edges
FROM employee e
JOIN rushdb_edges.works_at w ON w.__source_id = e.__id
JOIN company c ON c.__id = w.__target_id
GROUP BY e.name, c.name
ORDER BY e.name;
