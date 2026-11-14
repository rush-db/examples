# Finding and merging semantically equivalent relations

Two made-up imports describe the same people: HR links employees to companies with `WORKS_AT`, a CRM
uses `EMPLOYED_BY`. Orders carry `customer_id`, invoices carry `cust_id`. The script collects the
evidence the article walks through (relationship shapes, shared endpoint pairs in SQL, `describe.names`,
`describe.valueOverlap`, `propertyValues` similar search, `query.searchValues`), then merges the two
relationship types with `retypeRelations` and re-reads the counts. The engine counts; deciding that two
names mean the same thing is left to you.

Article: [Semantically equivalent relations in a knowledge graph](https://rushdb.com/blog/semantically-equivalent-relations-knowledge-graph)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `EMPLOYEE`, `COMPANY`, `ORDER` and `INVOICE` record, so it can be
re-run. Use an empty node: `describe.names` (query 03) reads every label on the node, so data from other
examples (for example a `CUSTOMER` label) adds suggestions that are not in `expected-output.txt`.

## Files

- `data/`: the HR and CRM exports, orders and invoices (fake people, `.example` domains)
- `queries/`: every request the script sends after seeding, one file each (`.json` envelopes for
  `POST /protocol/v1/execute`, `.sql` statements the script wraps in `query.statement`)
- `expected-output.txt`: output of a real run against RushDB 3.0.10

Query 07 (`retypeRelations`) changes data. The script re-seeds on every run, so you can run it again.
