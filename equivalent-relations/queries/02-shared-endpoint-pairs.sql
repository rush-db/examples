SELECT COUNT(*) AS same_pairs
FROM rushdb_edges.works_at w
JOIN rushdb_edges.employed_by e
  ON e.__source_id = w.__source_id AND e.__target_id = w.__target_id;
