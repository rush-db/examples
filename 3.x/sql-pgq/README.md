# SQL/PGQ on RushDB: the PostgreSQL 19 docs examples

The PostgreSQL 19 betas documented SQL/PGQ with a small shop graph (`customers`, `orders`, `products`,
with `customer_orders` and `order_items` edges). PG19 reverted the feature on 2026-09-07. This example
loads the same shop into RushDB, runs the docs query verbatim (it fails), runs the forms RushDB's read-only
`GRAPH_TABLE` profile accepts, the relational SQL equivalent over `rushdb_edges`, and lists the PG19
constructs outside the profile with the error each returns.

Article: [Postgres 19 reverted SQL/PGQ: graph queries in SQL today](https://rushdb.com/blog/sql-pgq-graph-queries-today)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL and SQL/PGQ are engine features, on by default) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `customers`, `orders` and `products` record, so it can be re-run.

## Files

- `data/`: the three vertex tables as JSON (made-up customers and orders). `orders.json` carries the
  foreign keys (`customer_id`, `product_nos`) that become relationships.
- `queries/link-*.json`: `linkRecords` calls that turn the foreign-key values into `customer_orders` and
  `order_items` relationships (the PG19 "edge tables")
- `queries/0*.pgq`, `queries/03-relational-equivalent.sql`: the statements the script runs
- `queries/not-in-profile/`: PG19 docs constructs RushDB's profile does not accept
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27

Datetimes reach SQL/PGQ as epoch milliseconds, so query 02 compares `ordered_when` with `1793318400000`
(2026-10-30T00:00Z).
