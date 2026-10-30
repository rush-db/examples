SELECT p.name, o.name AS employer
FROM person p
JOIN rushdb_edges.works_at w ON w.__source_id = p.__id
JOIN organization o ON o.__id = w.__target_id
LEFT JOIN rushdb_edges.located_in l ON l.__source_id = o.__id
WHERE l.__id IS NULL;
