# RushDB 3.x examples

Runnable examples for RushDB 3.x, the standalone Rust engine. Each folder seeds a small, made-up dataset and runs every query from its accompanying article against a local engine over the native HTTP protocol (`POST /protocol/v1/execute`), using `curl` and `jq`. `catalog-grounding-check` also needs Python 3, and `analytics-trace` also needs `openssl`.

```bash
rushdb serve --token local-token          # or: rushdb up
export RUSHDB_URL=http://127.0.0.1:3000 RUSHDB_TOKEN=local-token
cd 3.x/<example> && ./run.sh
```

Run each example on an empty node: several share label names. `expected-output.txt` in each folder is the output of a real run against the 3.0 engine build of 2026-10-27.

| Example | What it shows | Article |
|---|---|---|
| [`agent-memory-provenance`](agent-memory-provenance) | Agent memories as linked records with their source turn: scoped recall, supersession, vector recall with and without a scope filter, and deleting one user's memories. | [rushdb.com/blog/ai-agent-memory-database](https://rushdb.com/blog/ai-agent-memory-database) |
| [`analytics-trace`](analytics-trace) | An inspectable analytics answer: a read-only capability token, catalog evidence per filter value, a stored trace, and a rerun that tells "same result" from "data moved". | [rushdb.com/blog/inspectable-analytics-agent](https://rushdb.com/blog/inspectable-analytics-agent) |
| [`attack-paths`](attack-paths) | Identity attack paths: transitive group membership, merged scanner and EDR host records, and incident blast radius. | [rushdb.com/blog/graph-database-cybersecurity](https://rushdb.com/blog/graph-database-cybersecurity) |
| [`beneficial-ownership`](beneficial-ownership) | Ownership chains with a percent on each link, sanctions exposure through ownership layers, circular ownership, and effective stake computed in jq. | [rushdb.com/blog/graph-database-financial-services](https://rushdb.com/blog/graph-database-financial-services) |
| [`catalog-grounding-check`](catalog-grounding-check) | A client-side check for agent-written SQL (Python + sqlglot): unknown tables, columns and stored values are rejected with the stored alternatives. | [rushdb.com/blog/grounding-analytics-agents](https://rushdb.com/blog/grounding-analytics-agents) |
| [`clinical-ontology`](clinical-ontology) | A concept hierarchy with coded diagnoses: cohort queries over ontology hops and compound to gene to disease paths. | [rushdb.com/blog/graph-database-healthcare-life-sciences](https://rushdb.com/blog/graph-database-healthcare-life-sciences) |
| [`company-brain`](company-brain) | HR-, Notion-, Jira- and Slack-style JSON linked on matching keys, queried with SearchQuery and SQL, BM25 search, and a data-access policy. | [rushdb.com/blog/build-company-brain-rushdb](https://rushdb.com/blog/build-company-brain-rushdb) |
| [`customer-360`](customer-360) | CRM, billing, support and product events as linked records: value overlap, filtered schema, facets and a SQL join over relationships. | [rushdb.com/blog/customer-360-analytics-graph](https://rushdb.com/blog/customer-360-analytics-graph) |
| [`equivalent-relations`](equivalent-relations) | Two sources naming the same relation differently: name similarity, value overlap, similar-value search, and merging the relationship types. | [rushdb.com/blog/semantically-equivalent-relations-knowledge-graph](https://rushdb.com/blog/semantically-equivalent-relations-knowledge-graph) |
| [`fraud-rings`](fraud-rings) | Shared-identifier rings, circular money flows with $cycle, and why direction matters. | [rushdb.com/blog/best-graph-database-fraud-detection](https://rushdb.com/blog/best-graph-database-fraud-detection) |
| [`kg-predicate-completeness`](kg-predicate-completeness) | Predicate completeness per label, conditional completeness under a filter, and completeness across linked records. | [rushdb.com/blog/predicate-completeness-knowledge-graph](https://rushdb.com/blog/predicate-completeness-knowledge-graph) |
| [`schema-introspection-loop`](schema-introspection-loop) | The agent loop: read the shape, filter on stored values, read the shape of what matched, then ask the precise SQL question. | [rushdb.com/blog/trustworthy-agentic-data-analytics](https://rushdb.com/blog/trustworthy-agentic-data-analytics) |
| [`supply-chain-tier-n`](supply-chain-tier-n) | Tier-N supplier exposure with hops, recall tracing, bill-of-materials where-used and single-source dependencies. | [rushdb.com/blog/best-graph-database-supply-chain](https://rushdb.com/blog/best-graph-database-supply-chain) |
