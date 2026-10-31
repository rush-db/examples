# Type drift: one property name, two stored types

Two extractor versions write `PRODUCT` records. v1 sends `price` as a number and `in_stock` as a
boolean; v2 sends `price` as text (`"249.00"`, `"$59.99"`) and `in_stock` as `"yes"`/`"no"`. RushDB
accepts both and keeps one typed definition per type. The script shows:

- what `describe.properties` reports (one entry per type, `siblingTypes`)
- a numeric filter, `$sum`/`$max`, a `propertyValues` range and a sort on the split property
- `$type` on a split property
- SQL over the same label (the column reads as text)
- a drift gate a pipeline can run after each batch
- the repair: re-ingest with `convertNumericValuesToNumbers`, clean what the converter cannot parse,
  upsert by `sku`

Article: [Type drift in agent pipelines: never rejecting a write for a type](https://rushdb.com/blog/type-drift-agent-pipelines)

## Prerequisites

- A RushDB 3.x engine reachable over HTTP (SQL is on by default)
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script deletes every `PRODUCT` record first.

## Files

- `data/`: 12 made-up products, 8 from extractor v1 and 4 from v2
- `queries/`: every request the script sends (`.json` envelopes, `.sql` statements wrapped in `query.statement`)
- `expected-output.txt`: a real run against the engine build of 2026-10-27 (`rushdb 3.0.1`)
