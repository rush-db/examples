# pgwire-compatibility

What works over RushDB's PostgreSQL wire listener, and what fails, with the SQLSTATE of every failure.
The script seeds 7 example suppliers over HTTP (nested JSON, linked with `BUYS_FROM`), then runs about
30 probes through `psql`: catalog queries, joins over `rushdb_edges`, CTEs and window functions, the
extended protocol, `information_schema`, `\d`, transactions, `COPY`, casts, DDL, cursors, the 100,000-row
cap, session settings (`statement_timeout`, `disallow_full_table_scans`), index creation and DML.

Article: [What "speaks the Postgres wire protocol" really means](https://rushdb.com/blog/postgres-wire-protocol-compatibility)

## Prerequisites

- A single-tenant RushDB 3.x engine you can throw away (the script deletes `SUPPLIER` records and creates
  an index), with `sql` enabled (the default, which also starts the pgwire listener on 5432).
- `curl`, `jq`, `psql` (checked with psql 18.6).

## Run

```bash
rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # PGPORT if not 5432
./run.sh
```

`expected-output.txt` is a real run against RushDB 3.0.10. The script sleeps 6 s so the index it creates
finishes building in the background.

Driver probes (optional): `clients/psycopg_probe.py` (`pip install "psycopg[binary]"`) and
`clients/node_pg_probe.mjs` (`npm install pg@8`) run the same checks from code; their real output is in
`clients/expected-output.txt` (psycopg 3.3.6, node-postgres 8.23.1).

## What the run shows (RushDB 3.0.10)

| Works | Fails (SQLSTATE) |
|---|---|
| Simple and extended query flow (`\bind … \g`), typed parameters | `\d <table>`: psql's query uses `COLLATE` (0A000) |
| `\dt`, `information_schema.tables` / `.columns` with PostgreSQL type names | multi-statement strings in one message (0A000) |
| Joins, `GROUP BY`, CTEs, window functions, `EXPLAIN` | `COPY` (42601) |
| Label tables, `rushdb_edges.<type>` tables | `LISTEN`, `DECLARE … CURSOR`, SQL `PREPARE`, `CREATE TABLE` (0A000, each with what to use instead) |
| `BEGIN`/`COMMIT` (a read-only block; writes in it are refused) | `::jsonb` cast (0A000) |
| `INSERT`/`UPDATE`/`DELETE`, each its own commit | `GRAPH_TABLE` (SQL/PGQ is not on pgwire; 42601) |
| `SET`/`SHOW`/`RESET` (`statement_timeout`, `disallow_full_table_scans`, `search_path`) | TLS without `--tls-cert` (`sslmode=require` refused) |
| `statement_timeout` cancels (57014); 100,000-row cap (53200) | |
| Unknown table or column: a suggestion ("Did you mean 'SUPPLIER'?", 42P01 / 42703) | |

Gotchas the run exposes:

- Unquoted identifiers fold to lowercase, as in PostgreSQL, so a camelCase property needs double quotes
  (`"onboardedAt"`). Datetimes come back as epoch milliseconds (`bigint`), arrays as `jsonb` text.
- `CREATE INDEX … ON supplier (region)` resolves the label name the way `SELECT … FROM supplier` does,
  so the lowercase name indexes `SUPPLIER` and the guarded query runs once the index is built.
- `'supplier'::regclass` returns `NULL` rather than an OID.
