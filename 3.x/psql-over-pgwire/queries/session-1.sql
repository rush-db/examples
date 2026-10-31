-- psql session against RushDB's PostgreSQL wire listener.
-- Part 1. run.sh runs part 1, waits until the index is ready, then runs part 2.
\echo '== 1. Who am I talking to?'
SELECT version();
SHOW server_version;

\echo '== 2. Tables come from labels and relationship types'
SELECT table_schema, table_name FROM information_schema.tables
WHERE table_name IN ('CUSTOMER', 'ORDER', 'PRODUCT', 'placed', 'contains') ORDER BY 1, 2;

SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'PRODUCT' ORDER BY ordinal_position;

\echo '== 3. Plain SQL over a label'
SELECT name, price FROM product ORDER BY price DESC;

\echo '== 4. Traverse by joining relationship tables'
SELECT c.name AS customer, count(*) AS orders, sum(o.total) AS spent
FROM customer c
JOIN rushdb_edges.placed pl ON pl.__source_id = c.__id
JOIN "ORDER" o ON o.__id = pl.__target_id
GROUP BY c.name
ORDER BY spent DESC;

\echo '== 5. Extended protocol: a bound parameter'
SELECT name FROM product WHERE price > $1 ORDER BY name \bind 50 \g

\echo '== 6. Session guards'
SET statement_timeout = '5s';
SHOW statement_timeout;
SET disallow_full_table_scans = on;
SELECT name FROM customer WHERE city = 'Berlin';
CREATE INDEX customer_city ON "CUSTOMER"(city);
