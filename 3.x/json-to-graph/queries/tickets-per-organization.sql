SELECT o.name AS organization, count(*) AS tickets
FROM ticket t
JOIN rushdb_edges.requested_by rb ON rb.__source_id = t.__id
JOIN rushdb_edges.member_of m ON m.__source_id = rb.__target_id
JOIN organization o ON o.__id = m.__target_id
GROUP BY o.name
ORDER BY tickets DESC
