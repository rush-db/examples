SELECT "externalSessionId", count(*) AS episodes, to_timestamp_millis(min("observedAt")) AS first_turn, to_timestamp_millis(max("observedAt")) AS last_turn
FROM episode
GROUP BY "externalSessionId"
ORDER BY "externalSessionId"
