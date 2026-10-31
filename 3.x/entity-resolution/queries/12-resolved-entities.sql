SELECT a.name AS account, c.company AS billing_name, c.tax_id, s.rule
FROM account a
JOIN rushdb_edges.same_as s ON s.__source_id = a.__id
JOIN customer c ON c.__id = s.__target_id
ORDER BY a.name, c.company;
