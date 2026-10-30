# Fraud: circular money flows and shared identifiers

Example accounts, transfers and credit applications, with the queries from
[Best graph database for fraud detection (2026)](https://rushdb.com/blog/best-graph-database-fraud-detection).
It finds accounts on a directed transfer ring with `$cycle`, shows why the direction matters, finds applications that share a
phone (or a device) with confirmed fraud by naming related labels in the filter, and counts shared-phone pairs with `joinPairs`
before any links exist. Every name, number and account is made up.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP. A fresh in-memory node is best, so other data with the same labels doesn't show up in the results:
  `rushdb serve --token local-token` (default port 3000).
- `bash`, `curl` (7.76 or later) and `jq`.

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # these are the defaults
./run.sh
```

`run.sh` upserts every record by its business key (`accountId`, `applicationId`, `number`, `deviceId`), links them with
`linkRecords` on matching properties (existing relationships are skipped), then runs each request in `queries/`.
Running it again gives the same output. Compare with `expected-output.txt`, captured from a run against the engine build of 2026-10-27.

## The example graph

- `acct-a → acct-b → acct-c → acct-a`: a three-hop ring of high-risk accounts in CY, LV and MT.
- `acct-g → acct-h → acct-i → acct-j → acct-g`: a four-hop ring of medium-risk GB accounts, outside the scoped query.
- `acct-d` pays `acct-e` and `acct-f`, and `acct-e` pays `acct-f`: a triangle that is only a cycle if you ignore direction.
- `acct-k` is high-risk in CY and pays into `acct-d`, but is on no ring.
- `APP-002` shares a phone with fraud `APP-001`, `APP-006` with fraud `APP-005`. `APP-003` shares only a device with `APP-001`.
  `APP-004` and `APP-007` share a phone with each other, and neither is fraud.

## Notes

- The article shows the queries with the TypeScript SDK, which spells the filter `where`. The native protocol used here spells it
  `predicate`; the filter itself is the same.
- `joinPairs` on a self-join counts ordered pairs: the three pairs of applications that share a phone give `6`. It returns a
  count only, capped at `limit`.
