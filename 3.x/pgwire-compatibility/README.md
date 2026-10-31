# pgwire-compatibility

What works over RushDB's PostgreSQL wire listener, and what fails, with the SQLSTATE of every failure.
The script seeds 7 example suppliers over HTTP (nested JSON, linked with `BUYS_FROM`), then runs about
30 probes through `psql`: catalog queries, joins over `rushdb_edges`, CTEs and window functions, the
extended protocol, `information_schema`, `\d`, transactions, `COPY`, casts, DDL, cursors, the 100,000-row
cap, session settings (`statement_timeout`, `disallow_full_table_scans`), index creation and DML.

Article: [What "speaks the Postgres wire protocol" really means](https://rushdb.com/blog/postgres-wire-protocol-compatibility)

## Prerequisites

- A single-tenant RushDB 3.x engine you can throw away (the script deletes `SUPPLIER` records and creates
  two indexes), with `sql` enabled (the default, which also starts the pgwire listener on 5432).
- `curl`, `jq`, `psql` (checked with psql 18.6).

## Run

```bash
rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # PGPORT if not 5432
./run.sh
```

`expected-output.txt` is a real run against the engine build of 2026-10-27; a rerun produced identical
output. The script sleeps 6 s twice so the two indexes it creates finish building in the background.

Driver probes (optional): `clients/psycopg_probe.py` (`pip install "psycopg[binary]"`) and
`clients/node_pg_probe.mjs` (`npm install pg@8`) run the same checks from code; their real output is in
`clients/expected-output.txt` (psycopg 3.3.6, node-postgres 8.23.1).

## What the run shows (engine build 2026-10-27)

| Works | Fails (SQLSTATE) |
|---|---|
| Simple and extended query flow (`\bind … \g`), typed parameters | `\d`, `\dt`, `\l`: no `pg_catalog` (42P01) |
| Joins, `GROUP BY`, CTEs, window functions, `EXPLAIN` | `BEGIN`/`COMMIT`/`ROLLBACK` (0A000), autocommit only |
| `information_schema.tables` / `.columns` | multi-statement strings in one message (XX000) |
| Label tables, `rushdb_edges.<type>` tables | `COPY` (42601), `LISTEN`, `DECLARE … CURSOR`, `PREPARE`, `CREATE TABLE`, `SET search_path` (42601) |
| `INSERT`/`UPDATE`/`DELETE`, each its own commit | `::jsonb`, `::regclass` casts (XX000) |
| `SET`/`SHOW`/`RESET` of `statement_timeout`, `disallow_full_table_scans` | `GRAPH_TABLE` (SQL/PGQ is not on pgwire; 42601) |
| `statement_timeout` cancels (57014); 100,000-row cap (53200) | TLS (`sslmode=require` refused) |
| Unknown table: suggestion ("Did you mean 'SUPPLIER'?") | Unknown column: generic `internal execution error` (XX000); the detail is only in the server log |

Gotchas the run exposes:

- Unquoted identifiers fold to lowercase, as in PostgreSQL, so a camelCase property needs double quotes
  (`"onboardedAt"`). Datetimes come back as epoch milliseconds (`Int64`), arrays as JSON text.
- `CREATE INDEX … ON supplier (region)` (lowercase) creates an index on a label named `supplier`, while
  `SELECT … FROM supplier` reads the label `SUPPLIER` (table lookup is case-insensitive). The index is
  never used. Write the label's exact case in `CREATE INDEX`.
- The `INSERT` command tag is `INSERT 1`; PostgreSQL sends `INSERT 0 1`. psql prints `could not interpret
  result from server` (the row is written) and psycopg 3 reports `rowcount = -1`. node-postgres 8.23
  reports `rowCount: 1`. `UPDATE` and `DELETE` tags are fine.
- `SELECT current_database()` alone works (a compatibility answer); combined with another expression it fails.
