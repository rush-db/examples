# RushDB 2.x (legacy) examples

> **RushDB 2.x (legacy, Neo4j-based).** Security fixes only until 2027-10-28.
> New projects: use [RushDB 3](https://github.com/rush-db/rushdb), a standalone Rust database for AI.

Every folder in this directory was written for RushDB 2.x: the Neo4j-based TypeScript stack (the `2.x` branch of rush-db/rushdb and the `rushdb/platform` image). They were written against the 1.x and 2.x SDKs and the 2.x REST API, and are kept as they are for existing 2.x projects. To run one, install the 2.x SDK (`npm i @rushdb/javascript-sdk@2` or `pip install "rushdb<3"`).

| Group | Folders | What is there |
|---|---|---|
| Framework starters | `express-rushdb-sdk`, `express-books-rag`, `nextjs-cms`, `nextjs-ecommerce-example`, `nextjs-filters-rushdb-sdk`, `nextjs-simple-waitlist`, `nuxt-auth-rushdb-sdk`, `vite-react-useForm`, `python-simple-rag`, `python-books-rag`, `python-import-csv`, `jupyter-examples` | Small apps with the JavaScript and Python SDKs: an Express REST API, Next.js CMS, e-commerce, filters and waitlist apps, Nuxt auth, a React form, RAG APIs in Python and Express, CSV import and a Jupyter notebook. |
| Tutorials | 126 folders ending in `-tutorial` | Step-by-step Python scripts (a few in TypeScript), one per topic: ingestion patterns, relationship modeling, RAG retrieval and reranking, agent memory, multi-agent coordination, conversation state and graph traversal. |
| Use cases | 55 folders ending in `-usecase` | Single-scenario Python demos (a few in TypeScript): production RAG pipelines, citation tracking, semantic caching, code search, research assistants and similar applications. |

Each folder's README has its own setup steps.

## Running RushDB 2.x

Self-host the 2.x image against your own Neo4j instance:

```bash
docker run -p 3000:3000 \
  --name rushdb \
  -e NEO4J_URL='neo4j+s://your-instance.neo4j.io' \
  -e NEO4J_USERNAME='neo4j' \
  -e NEO4J_PASSWORD='password' \
  rushdb/platform:2.13.3
```

Self-hosting 2.x requires Neo4j 2026.01.4 or later with the APOC plugin (the requirement stated in the 2.x README).

For RushDB 3.x examples, see the [repository root](../README.md).

## Getting help

- Documentation: [docs.rushdb.com](https://docs.rushdb.com)
- Discussions: [github.com/rush-db/rushdb/discussions](https://github.com/rush-db/rushdb/discussions)
- Issues: [github.com/rush-db/rushdb/issues](https://github.com/rush-db/rushdb/issues)
