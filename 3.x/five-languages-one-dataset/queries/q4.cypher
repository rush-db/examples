MATCH (:PRODUCT {name: 'Paper filters'})<-[:CONTAINS]-(:ORDER)<-[:PLACED]-(c:CUSTOMER)
      -[:PLACED]->(:ORDER)-[:CONTAINS]->(other:PRODUCT)
WHERE other.name <> 'Paper filters'
RETURN other.name AS product, count(DISTINCT c) AS customers
ORDER BY customers DESC, product
