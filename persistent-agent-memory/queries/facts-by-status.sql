SELECT "subjectKey", active, text, to_timestamp_millis("validFrom") AS valid_from, to_timestamp_millis("validUntil") AS valid_until
FROM memory_fact
ORDER BY "validFrom"
