# wire-protocols

One RushDB 3.x engine, one question ("how many suppliers are in `flood-zone-07`?"), four wire protocols:
the native JSON envelope over HTTP, the same envelope as protobuf bytes over gRPC, SQL over the
PostgreSQL wire, and Cypher over Bolt with the official Neo4j Python driver. All four reach the same
protocol executor and return the same count. `--bench` adds a small loopback round-trip timing per
transport.

Article: [One binary, five protocols: HTTP, pgwire, gRPC, Bolt and MCP](https://rushdb.com/blog/one-binary-five-protocols)

## Prerequisites

- A RushDB 3.x engine you can throw away (the script deletes and re-creates `SUPPLIER` records), with gRPC
  and Bolt switched on and Cypher enabled (Bolt carries Cypher only; openCypher is a release candidate).
- Python 3.10+ and `pip install -r requirements.txt` (grpcio, neo4j, psycopg).

## Run

```bash
rushdb serve --token local-token --grpc-port 50051 --bolt-port 7687 --languages sql,cypher
pip install -r requirements.txt
RUSHDB_TOKEN=local-token python four_transports.py           # add --bench for timings
```

Ports default to 3000 (HTTP), 5432 (pgwire), 50051 (gRPC) and 7687 (Bolt); override with `HTTP_PORT`,
`PG_PORT`, `GRPC_PORT`, `BOLT_PORT`.

`expected-output.txt` is a real run with `--bench` against the engine build of 2026-10-27 on an i9-12900H
laptop (Linux, loopback, in-memory engine, 7 records). The counts must match; the timings will not. They
include each Python client library's own overhead, so read them as "how much does the transport add",
not as a database benchmark.

## How gRPC is called without generated code

The service is `rushdb.v1.Database/Execute`, unary, and its message has one field: `bytes json = 1`, the
same JSON envelope HTTP takes. The script encodes that field by hand (tag `0x0A`, a varint length, the
bytes), so it needs `grpcio` but no `.proto` file. Authentication is `authorization: Bearer <token>`
metadata; a multitenant server also needs `x-rushdb-tenant`.
