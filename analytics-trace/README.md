# analytics-trace

An inspectable analytics answer. A scripted "agent" (fixed steps, no model) answers one question with a
read-only capability token, keeps a trace of every step with the catalog evidence behind each filter value
(`'Germany'` is stored as `DE`), and writes `trace.json`: question, user, credential, steps, the exact final
query, row count, sample rows, citations and outcome. The harness stores the trace as `ANALYSIS` + `STEP`
records, and `rerun.sh` reruns the final query from the file and tells "same result" from "the data moved".

Article: [Auditable AI analytics: making an agent's work inspectable](https://rushdb.com/blog/inspectable-analytics-agent).

## Prerequisites

- A RushDB 3.x engine you can throw away, started with a capability secret (the script writes `ORDER`,
  `ANALYSIS` and `STEP` records). The demo secret below is the script's default; use your own for real data.
- `curl`, `jq`, `openssl`.

## Run

```bash
rushdb serve --token local-token --capability-secret 00112233445566778899aabbccddeeff
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token \
       RUSHDB_CAPABILITY_SECRET=00112233445566778899aabbccddeeff
./run.sh
./rerun.sh trace.json        # any time later
```

The output should match `expected-output.txt` (`trace.json` itself has a timestamp and record ids, so it
differs per run). Safe to rerun: orders upsert on `order_id`, the stored trace is replaced by its
deterministic `analysisId`, and the late order the script adds to show a changed rerun is removed again.

## What is in here

| Path | What |
|---|---|
| `data/orders.json` | 40 example orders: country code, segment, status, date, amount |
| `lib.sh` | `rdb` (one envelope per call) and `mint_read_token`: a capability token with `scope: "read"`, signed with HMAC-SHA256, as in the engine's authentication docs |
| `queries/01–04` | The agent's catalog reads: `describe.schema`, `propertyValues` for `status`, a value search for "Germany" that misses and returns the stored codes (`domainOnMiss`), and an exact search for "enterprise" |
| `queries/05-final-query.json` | The final SearchQuery the trace records and `rerun.sh` replays |
| `queries/06–09` | The write the agent token cannot make (`401 unauthorized`), cleanup, and a query over stored traces |
| `rerun.sh` | Mints a fresh read-only token, runs `finalQuery` from a trace file, compares row count and citations |

## Notes

- The article stores the trace with the TypeScript SDK (`importJson`); this example sends the same nested
  JSON as `ingest.documents`, with `relationshipType: "HAS_STEP"`.
- Capability tokens are HTTP only and have no revocation list, so keep `exp` short (10 minutes here). On a
  multitenant engine, add a `tenant` claim and the `X-RushDB-Tenant` header; on a single-tenant engine the
  claim must be absent.
- Citations use the business key (`order_id`); `trace.json` also keeps the record ids (`recordIds`).
- A rerun reads current data. RushDB has no "as of commit N" reads for clients, so the trace keeps the row
  count and citations to tell a moved dataset from a wrong answer.
- On RushDB Cloud the equivalent credential is a read-only API key; not covered here.
- Expected output was captured against the engine build of 2026-10-27.
