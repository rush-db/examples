# One dataset, five query languages

A small shop (4 customers, 5 orders, 4 products, loaded as nested JSON) and four questions, each asked in
SQL, openCypher, ISO GQL, SQL/PGQ, Gremlin and RushDB's native SearchQuery document:

1. Products over 50, most expensive first (filter)
2. Customers who bought Paper filters (two hops)
3. Orders and spend per customer, including a customer with no orders (optional match / outer join)
4. Customers who bought Paper filters also bought... (four hops, distinct counts)

The script prints one line per language per question, so differences are easy to spot.

Article: [Gremlin vs Cypher vs GQL vs SQL/PGQ: one dataset compared](https://rushdb.com/blog/gremlin-cypher-gql-sql-pgq-compared)

## Prerequisites

- A RushDB 3.x engine with every language enabled. Cypher and GQL are release candidates and opt-in, and
  `--languages` replaces the default set:

  ```bash
  rushdb serve --token local-token --languages sql,gql,cypher,gremlin,sql-pgq,mongodb
  ```

- `bash`, `curl`, `jq`

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script deletes every `CUSTOMER`, `ORDER` and `PRODUCT` record first, so it can be re-run.

## Files

- `data/customers.json`: nested customers → orders → products (made-up data); products are merged on `sku`
- `queries/qN.{sql,cypher,gql,pgq,gremlin,searchquery.json}`: one file per question and language
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27

Notes: `ORDER` is a reserved word in SQL and SQL/PGQ, so those files quote it. The Gremlin answer to Q3
counts orders only: grouped projections with anonymous traversals (`by(out(...).count())`) are outside
RushDB's tested Gremlin profile and were refused.
