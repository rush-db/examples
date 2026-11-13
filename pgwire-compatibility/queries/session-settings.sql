SET statement_timeout = '30s';
SHOW statement_timeout;
SET disallow_full_table_scans = on;
SELECT code FROM supplier WHERE region = 'flood-zone-07' ORDER BY code;
CREATE INDEX supplier_region ON supplier (region);
\! sleep 6
SELECT code FROM supplier WHERE region = 'flood-zone-07' ORDER BY code;
SELECT count(*) FROM supplier;
SET statement_timeout = '50ms';
SELECT count(*) FROM generate_series(1, 2000000000);
RESET ALL;
SHOW disallow_full_table_scans;
