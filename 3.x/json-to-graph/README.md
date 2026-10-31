# JSON to graph: nested documents to linked records

A made-up helpdesk export (3 tickets with requester, organization, custom fields, tags and comments) is
imported twice:

- **Import A**, as-is: the catalog shows duplicated people and companies, a 1:1 `CUSTOM_FIELDS` label, a
  `priority` stored as text and as a number, and an empty array stored as a property.
- **Import B**, after `queries/reshape.jq` (flatten `custom_fields`, normalise `priority`, drop empty
  `comments`) with `merge: true` and named relationships: 12 records, `REQUESTED_BY` / `MEMBER_OF` /
  `HAS_COMMENT`, and a second run that changes no counts.

It then queries the result across two relationships (native query) and with SQL.

Article: [JSON to graph database: how nested documents become records](https://rushdb.com/blog/json-to-graph-database)

## Prerequisites

- A RushDB 3.x engine (self-hosted; the SQL step is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script deletes the `TICKET`, `CUSTOM_FIELDS`, `REQUESTER`, `ORGANIZATION` and `COMMENTS` labels
before each import.

## Files

- `data/tickets.json`: the export (fake people, `.example` domains)
- `queries/reshape.jq`: the three reshape rules
- `queries/*.json`, `queries/*.sql`: catalog reads and queries the script sends
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27
