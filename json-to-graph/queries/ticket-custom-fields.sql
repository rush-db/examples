SELECT t.ticket_id, cf.plan, cf.region
FROM ticket t
JOIN rushdb_edges.__rushdb__relation__default__ e ON e.__source_id = t.__id
JOIN custom_fields cf ON cf.__id = e.__target_id
ORDER BY t.ticket_id
