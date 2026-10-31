#!/usr/bin/env bash
# Tenant isolation on one RushDB 3.x engine: two tenants, cross-tenant attempts, a read-only
# tenant-bound capability token, a stored prompt injection, a data-access policy, and a purge.
# Needs: curl, jq, openssl, and an engine started with --multitenant and --capability-secret
# (see README). Safe to rerun: both example tenants are purged first.
set -euo pipefail
cd "$(dirname "$0")"
. ./lib.sh
B="$RUSHDB_TOKEN"
h() { printf '\n== %s\n' "$1"; }
ingest() { # TENANT FILE
  call "$B" "$1" "$(envelope "$1" "$(jq -c '{kind: "ingest", ingest: {kind: "documents", label: "Ticket", documents: ., options: {relationshipTypes: {customer: "OPENED_BY"}}}}' "$2")")"
}

h "Reset: purge both example tenants (boot token)"
call "$B" "$ACME" "$(envelope "$ACME" '{"kind":"purgeTenant"}')" | jq -Rc 'split(" ") | {http: .[1]}'
call "$B" "$GLOBEX" "$(envelope "$GLOBEX" '{"kind":"purgeTenant"}')" | jq -Rc 'split(" ") | {http: .[1]}'
# A purge keeps the tenant's policy, so switch off one left by an interrupted run.
call "$B" "$ACME" "$(envelope "$ACME" '{"kind":"policy","policy":{"kind":"put","enforced":false,"policy":{"allowedLabels":["*"]}}}')" | jq -Rc 'split(" ") | {policyOff: .[1]}'

h "Seed: 3 tickets in $ACME, 2 in $GLOBEX (each nested customer becomes a linked record)"
ingest "$ACME" data/acme-tickets.json
ingest "$GLOBEX" data/globex-tickets.json

h "Same SQL, two tenants: each sees only its own rows"
call "$B" "$ACME" "$(envelope "$ACME" "$(sql_read queries/01-tickets.sql)")"
call "$B" "$GLOBEX" "$(envelope "$GLOBEX" "$(sql_read queries/01-tickets.sql)")"

h "No tenant on the request: refused before anything runs"
call "$B" - "$(envelope - "$(sql_read queries/02-count.sql)")"

h "Header says $ACME, envelope says $GLOBEX: refused"
call "$B" "$ACME" "$(envelope "$GLOBEX" "$(sql_read queries/02-count.sql)")"

h "Naming the other tenant inside the query: there is no such table"
call "$B" "$ACME" "$(envelope "$ACME" "$(sql_read queries/03-other-tenant-by-name.sql)")"

h "A tenant name with a typo: a new, empty tenant (not an error)"
call "$B" "${ACME}x" "$(envelope "${ACME}x" '{"kind":"describe","describe":{"kind":"labels","query":{}}}')"
call "$B" "${ACME}x" "$(envelope "${ACME}x" '{"kind":"purgeTenant"}')" | jq -Rc 'split(" ") | {cleanup: .[1]}'

h "Agent credential: a read-only capability token bound to $ACME, 10 minutes"
AGENT="$(mint support-agent read "$ACME" 600)"
jq -R 'split(".")[0] | gsub("-"; "+") | gsub("_"; "/") | . + ("=" * ((4 - length % 4) % 4)) | @base64d | fromjson | {sub, scope, tenant}' -c <<<"$AGENT"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(sql_read queries/02-count.sql)")"

h "The same token pointed at $GLOBEX"
call "$AGENT" "$GLOBEX" "$(envelope "$GLOBEX" "$(sql_read queries/02-count.sql)")"

h "The same token tries to write: DELETE, then purgeTenant"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(sql_write queries/04-delete-all.sql)")"
call "$AGENT" "$ACME" "$(envelope "$ACME" '{"kind":"purgeTenant"}')"

h "Stored prompt injection: a ticket body in $GLOBEX is an instruction; the database returns it as data"
GLOBEX_AGENT="$(mint support-agent read "$GLOBEX" 600)"
call "$GLOBEX_AGENT" "$GLOBEX" "$(envelope "$GLOBEX" "$(sql_read queries/05-poisoned-ticket.sql)")"

h "An agent that obeys it, holding a read-only token: the delete is refused, the rows stay"
call "$GLOBEX_AGENT" "$GLOBEX" "$(envelope "$GLOBEX" "$(sql_write queries/04-delete-all.sql)")"
call "$GLOBEX_AGENT" "$GLOBEX" "$(envelope "$GLOBEX" "$(sql_read queries/02-count.sql)")"

h "Policy: only the boot token can install one (the agent's token cannot)"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(jq -c '{kind: "policy", policy: .}' queries/06-policy.json)")"
call "$B" "$ACME" "$(envelope "$ACME" "$(jq -c '{kind: "policy", policy: .}' queries/06-policy.json)")" \
  | jq -Rc 'split(" ") | {http: .[1], policy: (.[2:] | join(" ") | fromjson | .policy | {allowedLabels, visibleProperties})}'

h "Under the policy: SELECT * returns only the visible columns"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(sql_read queries/07-select-star.sql)")"

h "Under the policy: the customer label is not visible at all"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(sql_read queries/08-hidden-label.sql)")"
call "$AGENT" "$ACME" "$(envelope "$ACME" '{"kind":"describe","describe":{"kind":"labels","query":{}}}')"

h "Under the policy: Cypher cannot apply it yet, so it fails closed"
call "$AGENT" "$ACME" "$(envelope "$ACME" "$(statement cypher queries/09-cypher.cypher)")"

h "Purge $GLOBEX (boot token): its data is gone, $ACME is untouched"
call "$B" "$GLOBEX" "$(envelope "$GLOBEX" '{"kind":"purgeTenant"}')" | jq -Rc 'split(" ") | {http: .[1]}'
call "$B" "$GLOBEX" "$(envelope "$GLOBEX" '{"kind":"describe","describe":{"kind":"labels","query":{}}}')"
call "$B" "$ACME" "$(envelope "$ACME" "$(sql_read queries/02-count.sql)")"

h "Cleanup: remove the policy from $ACME"
call "$B" "$ACME" "$(envelope "$ACME" '{"kind":"policy","policy":{"kind":"put","enforced":false,"policy":{"allowedLabels":["*"]}}}')" | jq -Rc 'split(" ") | {http: .[1]}'
