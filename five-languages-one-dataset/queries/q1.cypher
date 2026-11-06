MATCH (p:PRODUCT) WHERE p.price > 50 RETURN p.name AS name, p.price AS price ORDER BY price DESC
