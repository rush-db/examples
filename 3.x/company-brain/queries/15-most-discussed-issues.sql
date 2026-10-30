SELECT i.ticket_key, i.title, p.name AS assignee, count(m.__id) AS mentions
FROM issue i
JOIN rushdb_edges.assigned_to a ON a.__source_id = i.__id
JOIN person p ON p.__id = a.__target_id
LEFT JOIN rushdb_edges.mentions e ON e.__target_id = i.__id
LEFT JOIN message m ON m.__id = e.__source_id
GROUP BY i.ticket_key, i.title, p.name
ORDER BY mentions DESC;
