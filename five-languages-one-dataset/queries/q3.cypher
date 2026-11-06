MATCH (c:CUSTOMER)
OPTIONAL MATCH (c)-[:PLACED]->(o:ORDER)
RETURN c.name AS name, count(o) AS orders, coalesce(sum(o.total), 0) AS spent
ORDER BY spent DESC
