# Predicate completeness, conditional completeness and hierarchical predicates

One small knowledge graph (8 `PERSON`, 6 `ORGANIZATION`, 3 `COUNTRY`, loaded from nested JSON with some
values left out on purpose) and every query from a three-part series: per-label predicate completeness
from exact catalog counts and SQL, conditional completeness under a filter and per segment, and path
predicates across linked records with nested blocks, bounded `hops` and a SQL anti-join.

Articles:

- Part 1: [Predicate completeness in knowledge graphs](https://rushdb.com/blog/predicate-completeness-knowledge-graph) (queries 03–06)
- Part 2: [Conditional completeness](https://rushdb.com/blog/conditional-completeness-knowledge-graph) (queries 07–11)
- Part 3: [Hierarchical predicates](https://rushdb.com/blog/hierarchical-predicates-graph-queries) (queries 01, 12–17)

## Prerequisites

- A RushDB 3.x engine (self-hosted; SQL is an engine feature) reachable over HTTP
- `bash`, `curl`, `jq`

## Run

```bash
rushdb up                        # or: rushdb serve --token local-token
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
./run.sh
```

The script first deletes every `PERSON`, `ORGANIZATION` and `COUNTRY` record, so it can be re-run.
Use an empty node, or one where those labels hold nothing you need.

## Files

- `data/people.json`: example data. The names are well-known computer scientists and mathematicians, but
  the records are simplified and incomplete on purpose (Katherine Johnson's death date and Barbara
  Liskov's birth date are left out, Edsger Dijkstra has no nationality); do not use them as facts.
- `queries/`: every request the script sends after seeding, one file each (`.json` envelopes for
  `POST /protocol/v1/execute`, `.sql` statements the script wraps in `query.statement`)
- `expected-output.txt`: output of a real run against the engine build of 2026-10-27

The `.sql` files also run over the PostgreSQL wire protocol:
`PGPASSWORD=$RUSHDB_TOKEN psql "host=127.0.0.1 port=5432 user=rushdb dbname=rushdb sslmode=disable" -f queries/10-born-completeness-by-occupation.sql`
