# RushDB examples

[![RushDB Logo](https://raw.githubusercontent.com/rush-db/rushdb/main/rushdb-logo.svg)](https://rushdb.com)

> **RushDB — the database for AI**
>
> One database for your records, their relationships, and search over them.

Runnable examples for RushDB 3.x. Each folder at the repository root goes with an article on [rushdb.com/blog](https://rushdb.com/blog). Examples for RushDB 2.x (legacy) are in [`v2/`](v2).

- [Website](https://rushdb.com) · [Documentation](https://docs.rushdb.com) · [RushDB Cloud](https://app.rushdb.com) · [RushDB on GitHub](https://github.com/rush-db/rushdb)

## Quick start (RushDB 3.x)

Install and start RushDB with one of:

```bash
curl -fsSL https://rushdb.com/install.sh | sh && rushdb up
brew install rush-db/tap/rushdb
docker run -p 3000:3000 -e RUSHDB_TOKEN=change-me rushdb/rushdb:3
```

Then run an example against it:

```bash
git clone https://github.com/rush-db/examples.git && cd examples
export RUSHDB_URL=http://127.0.0.1:3000
export RUSHDB_TOKEN=change-me      # the token RushDB runs with; `rushdb up` uses local-token
cd company-brain && ./run.sh      # or any other example folder
```

Each example seeds a small dataset and runs every query from its article over the HTTP protocol with `curl` and `jq`. Some also use pgwire, Bolt, gRPC or MCP, or need Python, Node.js, `psql` or `openssl`: each folder's README lists its prerequisites and engine flags. Run each example on an empty node, since several share label names.

## Examples

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
| [`entity-resolution`](entity-resolution) | Two exports of the same companies matched on exact stored values: normalized tax ids, name collisions with conflicting ids, and records with no key. | [rushdb.com/blog/entity-resolution-property-graph](https://rushdb.com/blog/entity-resolution-property-graph) |
| [`equivalent-relations`](equivalent-relations) | Two sources naming the same relation differently: name similarity, value overlap, similar-value search, and merging the relationship types. | [rushdb.com/blog/semantically-equivalent-relations-knowledge-graph](https://rushdb.com/blog/semantically-equivalent-relations-knowledge-graph) |
| [`filtered-vector-search`](filtered-vector-search) | Post-filter vs pre-filter on a tiny vector set where every score is readable, filters across relationships, and a recall measurement script. | [rushdb.com/blog/filtered-vector-search](https://rushdb.com/blog/filtered-vector-search) |
| [`five-languages-one-dataset`](five-languages-one-dataset) | One shop dataset, four questions, each asked in SQL, openCypher, GQL, SQL/PGQ, Gremlin and SearchQuery. | [rushdb.com/blog/gremlin-cypher-gql-sql-pgq-compared](https://rushdb.com/blog/gremlin-cypher-gql-sql-pgq-compared) |
| [`fraud-rings`](fraud-rings) | Shared-identifier rings, circular money flows with $cycle, and why direction matters. | [rushdb.com/blog/best-graph-database-fraud-detection](https://rushdb.com/blog/best-graph-database-fraud-detection) |
| [`hybrid-rrf-dbsf`](hybrid-rrf-dbsf) | BM25 and vector legs over 20 help-center articles fused with RRF and DBSF, with both fusions recomputed by hand in jq. | [rushdb.com/blog/hybrid-search-rrf-vs-dbsf](https://rushdb.com/blog/hybrid-search-rrf-vs-dbsf) |
| [`json-to-graph`](json-to-graph) | A nested helpdesk export imported as-is and then reshaped: what the catalog shows before and after, and the queries each shape allows. | [rushdb.com/blog/json-to-graph-database](https://rushdb.com/blog/json-to-graph-database) |
| [`kg-predicate-completeness`](kg-predicate-completeness) | Predicate completeness per label, conditional completeness under a filter, and completeness across linked records. | [rushdb.com/blog/predicate-completeness-knowledge-graph](https://rushdb.com/blog/predicate-completeness-knowledge-graph) |
| [`mcp-tool-budget`](mcp-tool-budget) | Token counts for the RushDB MCP server: instructions, every tool definition and ten tool results, measured over stdio. | [rushdb.com/blog/mcp-database-tools-design](https://rushdb.com/blog/mcp-database-tools-design) |
| [`neo4j-driver-bolt`](neo4j-driver-bolt) | The official Neo4j Python driver against RushDB's Bolt listener: what works, what is refused, and the errors you get. | [rushdb.com/blog/neo4j-driver-bolt-compatibility](https://rushdb.com/blog/neo4j-driver-bolt-compatibility) |
| [`pgwire-compatibility`](pgwire-compatibility) | About 30 psql probes over the PostgreSQL wire listener, with the SQLSTATE of every failure. | [rushdb.com/blog/postgres-wire-protocol-compatibility](https://rushdb.com/blog/postgres-wire-protocol-compatibility) |
| [`psql-over-pgwire`](psql-over-pgwire) | A psql session: information_schema, SQL over label tables, traversal through rushdb_edges joins, bound parameters and session guards. | [rushdb.com/blog/query-graph-database-with-sql](https://rushdb.com/blog/query-graph-database-with-sql) |
| [`rag-in-python`](rag-in-python) | A RAG loop in one Python file with the `rushdb` SDK: fastembed vectors stored with each record, top-3 retrieval with sources, a citing prompt and any OpenAI-compatible model; plus vector vs BM25 vs hybrid on the same questions. | [rushdb.com/blog/rag-in-python](https://rushdb.com/blog/rag-in-python) |
| [`schema-introspection-loop`](schema-introspection-loop) | The agent loop: read the shape, filter on stored values, read the shape of what matched, then ask the precise SQL question. | [rushdb.com/blog/trustworthy-agentic-data-analytics](https://rushdb.com/blog/trustworthy-agentic-data-analytics) |
| [`schema-tokens`](schema-tokens) | One BIRD database described nine ways, from DDL to RushDB's catalog, with the token cost of each. | [rushdb.com/blog/schema-tokens-for-agents](https://rushdb.com/blog/schema-tokens-for-agents) |
| [`sql-pgq`](sql-pgq) | The PostgreSQL 19 docs' SQL/PGQ examples run against RushDB's read-only GRAPH_TABLE profile, plus the relational equivalent. | [rushdb.com/blog/sql-pgq-graph-queries-today](https://rushdb.com/blog/sql-pgq-graph-queries-today) |
| [`structured-recall-test`](structured-recall-test) | Twelve count, sum, latest and filter questions over 107 agent memories, answered three ways. | [rushdb.com/blog/structured-recall-test](https://rushdb.com/blog/structured-recall-test) |
| [`supply-chain-tier-n`](supply-chain-tier-n) | Tier-N supplier exposure with hops, recall tracing, bill-of-materials where-used and single-source dependencies. | [rushdb.com/blog/best-graph-database-supply-chain](https://rushdb.com/blog/best-graph-database-supply-chain) |
| [`tenant-isolation`](tenant-isolation) | Two tenants on one multitenant engine and every attempt to cross between them: queries, tokens, prompt injection and data-access policies. | [rushdb.com/blog/multi-tenant-database-design-ai](https://rushdb.com/blog/multi-tenant-database-design-ai) |
| [`type-drift`](type-drift) | Two extractor versions writing the same property as a number and as text: both stored, one typed definition each, and how to query across them. | [rushdb.com/blog/type-drift-agent-pipelines](https://rushdb.com/blog/type-drift-agent-pipelines) |
| [`wire-protocols`](wire-protocols) | One question asked over HTTP, gRPC, pgwire and Bolt, returning the same count, with optional loopback timings. | [rushdb.com/blog/one-binary-five-protocols](https://rushdb.com/blog/one-binary-five-protocols) |

`expected-output.txt` in each folder is the output of a real run against a RushDB 3.0 engine.

## RushDB 2.x (legacy) examples

The examples for RushDB 2.x (the Neo4j-based stack, security fixes only until 2027-10-28) are in [`v2/`](v2), with their own [README](v2/README.md).

## Getting help

- Documentation: [docs.rushdb.com](https://docs.rushdb.com)
- Discussions: [github.com/rush-db/rushdb/discussions](https://github.com/rush-db/rushdb/discussions)
- Issues: [github.com/rush-db/rushdb/issues](https://github.com/rush-db/rushdb/issues)
