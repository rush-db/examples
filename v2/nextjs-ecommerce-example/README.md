## RushDB Full‑Stack E‑commerce Demo (Next.js)

This repository demonstrates how easy it is to build a full‑stack app with RushDB. The app is a small e‑commerce demo built with Next.js, featuring categories, items, dynamic filters, and a simple checkout flow powered by RushDB.

### Why starting with RushDB is easy

- Zero schema migrations: model with labels and properties; evolve as you go.
- Bring your own data: import `data.json` (top label `CATEGORY`) and start querying immediately.
- One SDK, one key: use a single JavaScript client for reads and writes.
- Built‑in querying: express filters with `SearchQuery` and fetch facet values via `/properties/:id/values`.
- Single‑call writes: create an order with delivery, address, and items in one `importJson` call.
- Minimal glue code: Next.js API routes are thin wrappers around RushDB’s SDK.

## What’s inside

- Next.js app with API routes that talk to RushDB via the official JS SDK
- Dynamic filters and server‑side querying using RushDB SearchQuery
- Basic order creation (with delivery and address) using a single importJson call
- Example dataset in `data.json` (categories with nested items)

## Quick start

Prerequisites:
- Node.js 18+ and pnpm installed

1) Get your API token
   - Sign in at https://app.rushdb.com and create a project.
   - Copy your API token.

2) Import the demo data
   - In the RushDB dashboard, import the file `./data.json` from this repo.
   - Use top label: `CATEGORY`.

3) Set your API token locally
   - Create a `.env.local` file in `HolyJS_Shop` with:

     RUSHDB_API_KEY=your_token_here

4) Install and run

```bash
pnpm i
pnpm dev
```

The app runs at http://localhost:3007.

## How the backend works

All server code lives in Next.js API routes and calls the RushDB SDK via a small client in `src/db/index.ts`:

```ts
// src/db/index.ts
import RushDB from '@rushdb/javascript-sdk'
export const db = new RushDB(process.env.RUSHDB_API_KEY)
```

Main labels used in this demo: `CATEGORY`, `ITEM`, `ORDER`, `ORDER_ITEM`, `DELIVERY`, `ADDRESS`.

## API overview

Base path: `/api`

- GET `/categories`
  - Lists all categories (`labels: ['CATEGORY']`).
  - Response: `{ ok: true, data: Array<{ id, ...categoryFields }> }`

- POST `/categories/:id`
  - Body: optional RushDB `SearchQuery` (supports `where`, `limit`, `skip`).
  - Fetches items (`labels: ['ITEM']`) that belong to the given category ID.
  - Response: `{ ok: true, data: { category, items, total } }`

- POST `/labels`
  - Body: RushDB `SearchQuery` for labels.
  - Response: `{ ok: true, data }`

- POST `/properties`
  - Body: RushDB `SearchQuery` for properties.
  - Response: `{ ok: true, data }`

- POST `/properties/:id/values`
  - Body: RushDB `SearchQuery` for property values (useful for dynamic filters/facets).
  - Response: `{ ok: true, data }`

- GET `/products/:id`
  - Returns a single record by ID using `db.records.findById`.
  - Response: `{ ok: true, data: { id, ...fields } }`

- GET `/addresses`
  - Lists all `ADDRESS` records.
  - Response: `{ ok: true, data: Array<{ id, ...address }> }`

- GET `/orders`
  - Lists `ORDER` records. Example nested aggregations are included as comments in code for reference.
  - Response: `{ ok: true, data: Array<{ id, ...order }> }`

- POST `/orders`
  - Creates a new order using a single `db.records.importJson` call.
  - Expected payload shape (simplified):
    ```json
    {
      "createdAt": "2025-01-01T00:00:00Z",
      "status": "Pending",
      "delivery": {
        "method": "Express",
        "status": "New",
        "address": {
          "city": "Berlin",
          "street": "Main 1",
          "postalCode": "10115",
          "country": "DE"
        }
      },
      "order_item": [
        { "id": "ITEM_RECORD_ID", "name": "Product A", "price": 99.5, "qty": 2, "subtotal": 199 }
      ],
      "total": 199
    }
    ```
  - Response: `{ ok: true }` on success.

## Data

- `./data.json` holds demo categories and nested items. Import this file in RushDB with top label `CATEGORY` before running the app.

## Scripts

- `pnpm dev` — starts Next.js dev server on port 3007
- `pnpm build` — builds for production
- `pnpm start` — runs the production build

## Notes

- This project’s purpose is educational: to show how quickly you can wire a full‑stack app with RushDB using simple API routes and the JS SDK.
- If you change labels or the data model in your project, update the API routes accordingly.

