# Healthcare and life sciences: ontology cohorts and drug-target-disease paths

A small concept hierarchy, patients with coded diagnoses, and compounds, genes and diseases, with the queries from
[Graph databases for healthcare and life sciences (2026)](https://rushdb.com/blog/graph-database-healthcare-life-sciences).
It finds compounds that bind a gene associated with a disease through two nested related-record blocks, and builds a patient
cohort by walking `IS_A` links up a concept hierarchy with `hops`, with and without the parent concept itself. Patients,
diagnoses and compounds are made up; the concept names only resemble clinical terminology and are not SNOMED CT or UMLS content.

## Prerequisites

- A RushDB 3.x engine reachable over HTTP. A fresh in-memory node is best, so other data with the same labels doesn't show up in the results:
  `rushdb serve --token local-token` (default port 3000).
- `bash`, `curl` (7.76 or later) and `jq`.

## Run

```bash
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token   # these are the defaults
./run.sh
```

`run.sh` upserts every record by its key, links them with `linkRecords` on matching properties (existing relationships are
skipped), then runs each request in `queries/`. Running it again gives the same output. Compare with `expected-output.txt`,
captured from a run against the engine build of 2026-10-27.

## The example graph

- `Diabetes mellitus` has children `Type 1`, `Type 2` and `Gestational diabetes mellitus`; `Type 2 … with nephropathy` sits under
  `Type 2`, and a stage-3 nephropathy concept under that (three `IS_A` levels below the root).
- `PT-004` is coded at `Diabetes mellitus` itself, so the plain `hops` query (which starts at 1) misses them, and the `$or` query finds them.
- `PT-003` has only essential hypertension and is in neither cohort.

## Notes

- The article shows the queries with the TypeScript SDK, which spells the filter `where`. The native protocol used here spells it
  `predicate`; the filter itself is the same.
- Every record along a `hops` path must carry the block's label, so the walk stays inside `CONCEPT` records.
- Put the `$or` at the top level (or at the `DIAGNOSIS` level), as `queries/03` does. With the engine build of 2026-10-27, an
  `$or` placed inside the `CONCEPT` block, which is itself nested in `DIAGNOSIS`, matched no records.
