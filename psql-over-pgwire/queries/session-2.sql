-- psql session, part 2 (after the customer_city index is ready).
\echo '== 6b. Same filter once the index is ready'
SET disallow_full_table_scans = on;
SELECT name FROM customer WHERE city = 'Berlin';
RESET ALL;

\echo '== 7. Single-statement writes commit on their own'
UPDATE product SET price = 30.0 WHERE name = 'Scale';
SELECT name, price FROM product WHERE name = 'Scale';
UPDATE product SET price = 32.0 WHERE name = 'Scale';

\echo '== 8. What BI tools send on connect: settings, the catalog, a transaction block'
\echo '-- SET application_name (what Metabase sends on connect)'
SET application_name = 'metabase';
\echo '-- the describe-tables meta-command (reads pg_catalog)'
\dt
\echo '-- BEGIN opens a read-only block: reads work, a write is refused'
BEGIN;
SELECT count(*) FROM product;
UPDATE product SET price = 31.0 WHERE name = 'Scale';
COMMIT;

\echo '== 9. What does not work, and the SQLSTATE you get'
\set VERBOSITY sqlstate
\echo '-- GRAPH_TABLE over pgwire'
SELECT * FROM GRAPH_TABLE (MATCH (c:CUSTOMER) COLUMNS (c.name AS name)) AS g;
\echo '-- COPY'
COPY product TO STDOUT;
DROP INDEX customer_city;
