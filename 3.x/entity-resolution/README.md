# Entity resolution with exact values

Two made-up exports describe the same companies. The CRM has 6 `ACCOUNT` records (`name`, `vat_id`,
`country` spelled out); billing has 8 `CUSTOMER` records (`company`, `tax_id`, `email`, `country` as an
ISO code). Names differ ("Initech LLC" / "Initech"), one tax id is stored with spaces, one billing record
has no tax id, one company name appears in both exports with two different tax ids, and one billing
customer has no CRM account at all.

The script collects exact evidence (`describe.valueOverlap`, `joinPairs`), links the certain matches with
`linkRecords`, lists what is left with a `$not` relationship filter, looks for near matches with
`propertyValues` `similar` search and `domainOnMiss`, links two reviewed matches, and reads the result back
in SQL. Every decision is stored as a `SAME_AS` relationship with a `rule` property. The engine counts and
links; deciding that two records are the same company is left to you (or to a model you trust).

Article: [Entity resolution with exact values in a property graph](https://rushdb.com/blog/entity-resolution-property-graph)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `ACCOUNT` and `CUSTOMER` record, so it can be re-run.

## Files

- `data/crm-accounts.json`, `data/billing-customers.json`: the two exports (fake companies, `.example` domains,
  made-up tax ids)
- `queries/`: every request the script sends after seeding, one file each (`.json` envelopes for
  `POST /protocol/v1/execute`, `.sql` statements the script wraps in `query.statement`)
- `expected-output.txt`: output of a real run against the engine build of 2026-10-28 (`ab142c7`), in memory

Queries 03, 10 and 11 (`linkRecords`) change data. The script re-seeds on every run, so you can run it again.

## Notes

- `describe.valueOverlap`, `propertyValues` `search` (`similar`, `domainOnMiss`) are in the engine manual;
  the public docs pages for the [schema catalog](https://docs.rushdb.com/3.x/engine/data-model/schema-catalog)
  and [facets](https://docs.rushdb.com/3.x/engine/query/facets) don't describe them yet.
- `similar` results are near matches, not exact ones. Query 07 lowers `minSimilarity` from the default 0.6 to
  0.4 so "Globex Corp." is listed; check every near match before you link on it.
- On RushDB Cloud, relationship suggestions propose `join_pattern` links like the tax-id rule here for review;
  that feature is Cloud-only and is not part of this script.
