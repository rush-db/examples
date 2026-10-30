# Supply chain: tier-N exposure, recall tracing, BOM where-used

Example data for a small supply chain (suppliers six tiers deep, components, a bill of materials, lots, production runs, products and shipments) and the queries from
[Best graph database for supply chain management (2026)](https://rushdb.com/blog/best-graph-database-supply-chain).
It shows tier-N supplier exposure with a variable-length `hops` traversal, downstream and upstream recall tracing with nested
related-record filters, BOM explosion and where-used over a recursive `CONTAINS` hierarchy, and single-source dependency with a
per-component supplier count. All companies, codes and quantities are made up.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP. A fresh in-memory node is best, so other data with the same labels doesn't show up in the results:
  `rushdb serve --token local-token` (default port 3000).
- `bash`, `curl` (7.76 or later) and `jq`.

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # these are the defaults
./run.sh
```

`run.sh` upserts every record by its business key (`code`, `lotId`, `runId`, `sku`, `shipmentId`), links them with
`linkRecords` on matching properties (existing relationships are skipped), then runs each request in `queries/`.
Running it again gives the same output. Compare with `expected-output.txt`, captured from a run against the engine build of 2026-10-27.

## Files

| Path | What it is |
|---|---|
| `data/*.json` | One file per label, flat records with foreign-key fields such as `suppliesTo` and `inputLots` |
| `seed/*.json` | The `linkRecords` requests that turn those fields into typed relationships |
| `queries/*.json` | Each article query as a full Protocol v1 envelope you can send with `curl --data-binary @file` |

## Notes

- The article shows the queries with the TypeScript SDK, which spells the filter `where`. The native protocol used here spells it
  `predicate`; the filter itself is the same.
- Tier-N exposure: every record along a `hops` path must carry the block's label, so the walk stays inside `SUPPLIER` records.
  The filter (`region: "flood-zone-07"`) applies to the endpoint only. `S-104` has a flood-zone supplier five tiers behind it, so it
  is not returned with `max: 4`; raise `max` to 5 and it is.
- Single-source dependency: the engine counts suppliers per component (`$count` over an alias). Keeping only the components where
  that count is 1 is done in `jq`, because the native query has no filter on a computed count.
