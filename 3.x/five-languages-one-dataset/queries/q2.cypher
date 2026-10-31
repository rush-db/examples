MATCH (c:CUSTOMER)-[:PLACED]->(:ORDER)-[:CONTAINS]->(:PRODUCT {name: 'Paper filters'})
RETURN DISTINCT c.name AS name ORDER BY name
