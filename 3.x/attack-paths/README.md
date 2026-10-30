# Cybersecurity: group membership, identity attack paths, blast radius

Example users, nested groups, computers, sessions, scanner and EDR host exports, services, customers and incidents, with the
queries from [Graph databases for cybersecurity and identity (2026)](https://rushdb.com/blog/graph-database-cybersecurity).
It upserts hosts from two tools by `hostname` so neither tool's fields are lost, resolves transitive group membership with a
`hops` traversal, follows an identity attack path across mixed labels with fixed nesting, and counts the customers behind an
incident. Every user, host, CVE and customer is made up.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP. A fresh in-memory node is best, so other data with the same labels doesn't show up in the results:
  `rushdb serve --token local-token` (default port 3000).
- `bash`, `curl` (7.76 or later) and `jq`.

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # these are the defaults
./run.sh
```

`run.sh` upserts every record by its natural key, imports `data/scanner-hosts.json` and then `data/edr-hosts.json` as `HOST`
with `mergeBy: ["hostname"]` and `mergeStrategy: "append"`, links records with `linkRecords` on matching properties (existing
relationships are skipped), then runs each request in `queries/`. Running it again gives the same output. Compare with
`expected-output.txt`, captured from a run against the engine build of 2026-10-27.

## The example graph

- `alice.hart → g-helpdesk → g-it-support → g-server-ops → g-tier0-admins`, and `g-tier0-admins` is `ADMIN_TO` the tier-0 `DC-01`.
- `g-it-support` is `ADMIN_TO` workstation `WS-114`, where privileged `erin.walsh` has a session (`WS-114 -HAS_SESSION-> erin.walsh`).
  That is Alice's attack path: helpdesk membership → admin on `WS-114` → Erin's session.
- `bob.lin` (sales) has no path to tier 0.
- Incident `INC-2026-031` affects `svc-auth` and `svc-payments`; four distinct customers sit behind them.

## Notes

- The article shows the queries with the TypeScript SDK, which spells the filter `where`. The native protocol used here spells it
  `predicate`; the filter itself is the same.
- Every record along a `hops` path must carry the block's label. The `MEMBER_OF` walk therefore stays inside `GROUP` records, and
  the nested `COMPUTER` and `USER` blocks continue from the endpoint group. A path that alternates labels (group, computer,
  session, group …) to any depth can't be written as one native query; `queries/04` spells out one fixed shape.
- `hops` starts at 1, so "effective groups of a user" (`queries/03`) uses `$or`: direct membership, or a group reached through
  1–6 nested `MEMBER_OF` hops from one of the user's groups.
- The blast-radius requests filter on the incident's record id (`$id`), as in the article. `run.sh` looks the id up with
  `queries/05-find-incident.json` and puts it in place of `__INCIDENT_ID__`. `$count: "*"` counts distinct customers: `CUST-01`
  and `CUST-02` sit behind both affected services and are counted once.
