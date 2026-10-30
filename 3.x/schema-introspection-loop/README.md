# The schema introspection loop: read shape, narrow on values, read the matches, query

An agent's analytics loop, run by hand on made-up data (12 fictional companies with orders and support
tickets). It shows the filter a guessing agent writes and its empty result, then the four steps that
replace the guess: read the shape (`describe.schema`, `describe.schemaSummary`), narrow on stored values
(`propertyValues`), read the shape of the matching records (the same calls with a filter), and write one
precise query (native query document or SQL over label and `rushdb_edges` tables). Two questions:

- A. How many refunds did enterprise customers in Germany get last quarter? (Q3 2026)
- B. Why did enterprise customers cancel after the March price change?

Articles:

- [Agentic data analytics you can trust: the introspection loop](https://rushdb.com/blog/trustworthy-agentic-data-analytics) (question A)
- [AI agent schema: why agents should read the schema before they query](https://rushdb.com/blog/ai-agent-schema)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `CUSTOMER`, `ORDER` and `TICKET` record, so it can be re-run. Use an
empty node: the `customer-360` and `equivalent-relations` examples use some of the same labels.

## Files

- `data/customers.json`: example data; companies, orders and tickets are fictional
- `queries/`: every request the script sends after seeding, one file each (`.json` envelopes for
  `POST /protocol/v1/execute`, `.sql` statements the script wraps in `query.statement`)
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27

## A note on dates in SQL

SQL reads datetime properties as epoch milliseconds (`Int64`), so `canceled_at >= '2026-03-01'` fails.
Convert first: `to_timestamp_millis(canceled_at) >= TIMESTAMP '2026-03-01'`. The native query document
compares datetimes to date strings directly (`"canceled_at": {"$gte": "2026-03-01"}`).
