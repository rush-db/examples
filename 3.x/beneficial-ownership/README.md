# Financial services: beneficial ownership chains

Example people, companies and `OWNS` links with a `percent` on each, and the queries from
[Graph databases for financial services and compliance (2026)](https://rushdb.com/blog/graph-database-financial-services).
It finds companies exposed to a sanctioned owner directly or through up to five layers of holding companies (`$or` plus a `hops`
block with a nested `PERSON` block), finds circular ownership with `$cycle`, and computes each customer's effective
ownership by multiplying stakes along every path. That last step runs in `jq`, not in the engine (see below). All people and
companies are made up.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP. A fresh in-memory node is best, so other data with the same labels doesn't show up in the results:
  `rushdb serve --token local-token` (default port 3000).
- `bash`, `curl` (7.76 or later) and `jq`.

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # these are the defaults
./run.sh
```

`run.sh` upserts people and companies by `code`, creates one `OWNS` relationship per row of `data/ownership.json` with its
`percent` (existing relationships are skipped), runs the requests in `queries/`, then feeds the records and links to
`effective-stake.jq`. Running it again gives the same output. Compare with `expected-output.txt`, captured from a run against
the engine build of 2026-10-27.

## The example graph

- `Viktor Halden` (sanctioned) owns 100% of `CO-300`, which owns 70% of `CO-200`, which owns 60% of customer `CO-100`.
  His effective stake in `CO-100` is 100% × 70% × 60% = 42%.
- `Elena Marsh` (sanctioned) owns 10% of customer `CO-110` directly: exposed, but below the 25% threshold.
- `CO-400 → CO-410 → CO-420 → CO-400` is a circular holding; `CO-400` owns 80% of customer `CO-130`.

## Where the effective stake is computed, and why

Native SearchQuery filters on the endpoint of a path; it does not carry a value along the path, so it can't multiply 70% by 60%.
The engine's part is to return the `OWNS` relationships with their `percent` (`queries/04-ownership-links.json`) and the records
(`queries/03-owners-and-companies.json`). `effective-stake.jq` walks up from each customer, multiplies the stakes, and sums them
per person when there are several paths.

A path stops when it would revisit a company, so a circular holding contributes its first pass only. For `CO-130` that gives
Maria Lindqvist 56%. Regulators and vendors treat circular holdings in different ways; decide your rule before you rely on a number.

## Notes

- The article shows the queries with the TypeScript SDK, which spells the filter `where`. The native protocol used here spells it
  `predicate`; the filter itself is the same.
- Every record along a `hops` path must carry the block's label, so the walk stays inside `COMPANY` records, and the nested
  `PERSON` block is tested from the endpoint company. The `$or` branch catches a sanctioned person who owns a company directly.
- The sanctions query returns holding companies too (`CO-200`, `CO-300`). Add `"customer": true` to the predicate to keep only customers.
