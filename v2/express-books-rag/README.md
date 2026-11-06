# RushDB Generic RAG API (Express + TypeScript)

A generic RAG (Retrieval-Augmented Generation) API built with Express and RushDB, providing record vectorization and semantic search capabilities via sentence-transformers.

## Features

- **Generic Record Processing**: Index any text field on any record collection in RushDB  
- **Vector Embeddings**: Use HuggingFace-style models (`@xenova/transformers`) for embedding generation  
- **RushDB Integration**: Attach embedding vectors directly to your existing records  
- **RushDB Vector Search**: Perform cosine-similarity search over stored embeddings  
- **Express Interface**: Lightweight REST API for easy integration  
- **Auto-Configuration**: All settings via `.env`, no code changes required  

## Getting Started

### Prerequisites

- Node.js ≥ 18  
- A RushDB API token (from https://app.rushdb.com/)  
- `npm` or `yarn`  

### Clone & Install

```bash
git clone https://github.com/rush-db/examples.git
cd examples/express-books-rag
npm install
```

### Environment

Copy and fill out your environment variables:

```bash
cp .env.example .env
```

```ini
# .env
PORT=3007
RUSHDB_API_TOKEN=your_rushdb_token
RUSHDB_BASE_URL=https://api.rushdb.com/api/v1
EMBEDDING_MODEL=Xenova/all-MiniLM-L6-v2
```

## Scripts

```jsonc
{
  "scripts": {
    "dev": "tsx --watch --env-file .env src/index.ts",
    "start": "node --env-file .env dist/index.js",
    "build": "tsc",
    "import":"tsx --env-file .env src/import-data.ts"
  }
}
```

- **`npm run dev`** — run in watch mode with hot reload  
- **`npm run build`** — compile to `dist/`  
- **`npm start`** — run the compiled code  
- **`npm run import`** — import CSV data into RushDB  

## Build & Run

```bash
# Development
npm run dev

# Production
npm run build
npm start
```

The server will listen on `http://localhost:<PORT>` (default: 3007).

## Quick Start

### CSV Import

Place your `data.csv` under `test_data/`, then run:

```bash
npm run import
```

This will:
1. Parse CSV → JSON
2. Call `db.records.createMany({ label: 'BOOK', data: [...] })`
3. Log success or error

### Index Records

POST to `/index` with **field**, optional **vectorDimension** and any RushDB filters:

```bash
curl -X POST http://localhost:3007/index \
  -H "Content-Type: application/json" \
  -d '{
    "field": "content",
    "vectorDimension": 384,
    "where": {
      "published_year": {
        "$gte": 1960
      }
    }
  }'
```

Response:

```json
{
  "message": "Indexing complete",
  "processed": 120,
  "errors": 3,
  "skipped": 5
}
```

### Search Records

POST to `/search` with **query**, optional **vectorDimension**, and any RushDB filters:

```bash
curl -X POST http://localhost:3007/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Magic",
    "vectorDimension": 384,
    "where": {
      "published_year": {
        "$gte": 1960
      }
    }
  }'
```

Response:

```json
{
  "success": true,
  "total": 42,
  "data": [
    { "title": "...", "content": "...", "embedding": [ ... ] },
    ….
  ]
}
```

## How It Works Inside

1. **paginate()** — internal async generator hides RushDB pagination  
2. **vectorize()** — calls `@xenova/transformers` feature-extraction pipeline with pooling & normalization  
3. **indexRecords()** — loops through records, embeds a specified field, and updates each record  
4. **search()** — runs a vector similarity query (cosine) via RushDB’s `$vector` filter & aggregation  

## Code Structure

```
.
├── src/
│   ├── index.ts           # Express server & routes
│   ├── config.ts          # Env var loader & defaults
│   ├── rag.service.ts     # Functional RAG API (paginate, index, search)
│   ├── text-processor.ts  # `vectorize()` helper using Xenova/Transformers
│   └── import-data.ts     # CSV → JSON → RushDB import script
├── test_data/
│   └── data.csv
├── .env.example
├── package.json
├── tsconfig.json
└── README.md
```

## Postman Collection
For testing the API, you can use the [Postman collection](./RushDB%20Express%20RAG%20API.postman_collection.json) located in the project root.

## Customization

- **Embedding Model**: change `EMBEDDING_MODEL` in `.env`  
- **Batch Size**: adjust in `paginate()` default  
- **Vector Threshold**: modify `threshold` in `search()`  
- **Additional Filters**: pass any RushDB `where` properties to both `/index` and `/search`  

## Dependencies

- **`express`** — web framework  
- **`@rushdb/javascript-sdk`** — RushDB client  
- **`@xenova/transformers`** — on-device transformer pipelines  
- **`csv-parse`**, **`fs-extra`** — CSV parsing & file I/O  
- **`tsx`**, **`typescript`** — TS runtime & compiler  

---

Happy building your semantic-search applications with RushDB and TypeScript!
