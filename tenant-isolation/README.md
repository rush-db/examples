# tenant-isolation

Two tenants on one multitenant RushDB 3.x engine, and every way we could think of to make one see the
other. Same SQL in each tenant; a request with no tenant, with mismatched tenants, and with the other
tenant's name inside the query; a read-only capability token bound to one tenant, pointed at the other and
then asked to write; a ticket whose body is a prompt injection; a data-access policy that hides a label and
two columns; and a tenant purge.

Articles:
- [Multi-tenant database design for AI apps](https://rushdb.com/blog/multi-tenant-database-design-ai)
- [MCP database server security: designing tools for the lethal trifecta](https://rushdb.com/blog/mcp-database-server-security)

## Prerequisites

- A RushDB 3.x engine you can throw away, started **multitenant** with a capability secret and the `sql`
  and `cypher` languages. The demo secret below is the script's default; use your own for real data.
- `curl`, `jq`, `openssl`.

## Run

```bash
rushdb serve --multitenant --token local-token \
  --capability-secret 00112233445566778899aabbccddeeff --languages sql,cypher
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token \
       RUSHDB_CAPABILITY_SECRET=00112233445566778899aabbccddeeff
./run.sh
```

Without `--data-dir` the engine runs in memory, which is all this needs. The tenancy mode is fixed when a
data directory is created, so don't point this at a single-tenant directory.

The output should match `expected-output.txt` except for record ids (`__id`), which differ per run. Safe to
rerun: both example tenants (`example-acme`, `example-globex`; override with `ACME_TENANT` /
`GLOBEX_TENANT`) are purged first and the policy is switched off at the start and the end.

## What it shows

| Step | Result |
|---|---|
| Same `SELECT` in two tenants | 3 rows in one, 2 in the other |
| No `X-RushDB-Tenant` header | `403 missing_scope` |
| Header and envelope `context.scope` disagree | `403 scope_mismatch` |
| `SELECT … FROM globex.Ticket` from inside `example-acme` | `404 not_found`: tenants are key ranges, not schemas |
| A tenant name with a typo | `200`, an empty tenant: a new scope creates its tenant on first use |
| Read-only token for `example-acme`, sent to `example-globex` | `401 unauthorized` |
| Read-only token runs `DELETE` / `purgeTenant` | `401 unauthorized` |
| A ticket body that says "Ignore all previous instructions…" | returned verbatim as data; the obeying delete is `401` |
| Capability token tries to install a policy | `401`: only the boot token can |
| `SELECT *` under the policy | only `subject`, `status` (and `__id`) |
| The hidden `customer` label | not a table, not in `describe.labels` |
| Cypher under the policy | `401 policy-enforced reads are unavailable for this adapter` (fails closed) |
| `purgeTenant` on `example-globex` | its labels are gone; `example-acme` still has 3 tickets |

## Files

| Path | What |
|---|---|
| `data/*.json` | example tickets with a nested `customer` (fake names), one with an injected instruction in `body` |
| `queries/*.sql`, `*.cypher` | the statements `run.sh` wraps in `query.statement` / `mutate.statement` envelopes |
| `queries/06-policy.json` | the data-access policy (`allowedLabels`, `visibleProperties`) |
| `lib.sh` | `call` (one envelope, prints the HTTP status and response), `envelope`, and `mint`: a capability token bound to one tenant, HMAC-SHA256 as in the engine's authentication docs |

## Over the PostgreSQL wire (not in run.sh)

On a multitenant server the pgwire `database` startup parameter is the tenant. The password is the boot
token or a capability token bound to that tenant (`mint` in `lib.sh`); a capability for another tenant is
refused (`Password authentication failed`). Two things worth knowing, both checked on RushDB 3.0.10:

- libpq defaults `dbname` to the user name, so `psql "host=127.0.0.1 user=rushdb"` without `dbname` opens a
  tenant called `rushdb`, not an error.
- On a non-loopback multitenant listener the engine starts pgwire only with TLS and tenant-bound
  credentials (`--tls-cert`, `--tls-key`, `--capability-secret`); without them it refuses to start:
  `refusing to bind pgwire on a non-loopback multitenant listener without TLS and --capability-secret`.
