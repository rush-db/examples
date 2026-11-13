# psql against RushDB over the PostgreSQL wire protocol

Seeds a small shop graph over HTTP, then runs a psql session: `information_schema`, plain SQL over label
tables, traversal by joining `rushdb_edges` tables, a bound parameter with `\bind`, the
`statement_timeout` and `disallow_full_table_scans` session guards, single-statement writes, and the
statements that fail (with their SQLSTATE).

Article: [How to query a graph database with SQL from psql](https://rushdb.com/blog/query-graph-database-with-sql)

## Prerequisites

- A RushDB 3.x engine with SQL enabled (the default), HTTP on 3000 and the PostgreSQL wire listener on 5432
- `bash`, `curl`, `jq`, and `psql` 16 or later (for `\bind`)

## Run

```bash
rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token PGHOST=127.0.0.1 PGPORT=5432
./run.sh
```

`CREATE INDEX` returns before the index is ready, so the script runs `session-1.sql`, waits until
`describe.indexes` reports `customer_city` as `ready`, then runs `session-2.sql`.

## Files

- `data/customers.json`: nested customers → orders → products (made-up data)
- `queries/session-1.sql`, `queries/session-2.sql`: the psql session
- `expected-output.txt`: output of a real run (psql 18.6) against RushDB 3.0.10

The listener is cleartext without `--tls-cert` (`sslmode=disable`), and every write commits on its own: a
`BEGIN` block is read-only. Keep a cleartext listener on loopback.
