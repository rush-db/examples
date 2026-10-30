# Customer 360 as linked records

Loads made-up CRM, billing and support data as nested JSON (each nested object becomes a linked record),
adds flat product events from a separate tracking system, and checks the identity key with
`describe.valueOverlap` before linking events to customers with `linkRecords`. Then it asks questions
three ways on the same store: filtered schema and facets, a native graph filter (overdue invoice and an
open high-priority ticket), and SQL over label tables joined through `rushdb_edges`.

Article: [Customer 360 analytics without a six-month data project](https://rushdb.com/blog/customer-360-analytics-graph)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `CUSTOMER`, `SUBSCRIPTION`, `INVOICE`, `TICKET` and `PRODUCT_EVENT`
record, so it can be re-run. Use an empty node, or one where those labels hold nothing you need (the
`schema-introspection-loop` example also uses `CUSTOMER`, and `equivalent-relations` uses `INVOICE`).

## Files

- `data/customers.json`, `data/product-events.json`: example data (fake people and `.example` domains)
- `queries/`: every request the script sends after seeding, one file each (`.json` envelopes for
  `POST /protocol/v1/execute`, `.sql` statements the script wraps in `query.statement`)
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27

The `.sql` file also runs over the PostgreSQL wire protocol:
`PGPASSWORD=$RUSHDB_TOKEN psql "host=127.0.0.1 port=5432 user=rushdb dbname=rushdb sslmode=disable" -f queries/08-events-per-customer.sql`
