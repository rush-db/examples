# TypeScript SDK Quickstart: Setting Up Your First RushDB Project

A step-by-step guide to getting started with the RushDB TypeScript SDK. This tutorial demonstrates the core operations you'll use in every RushDB project: client setup, record creation, querying, relationships, and transactions.

## What You'll Build

By the end of this tutorial, you'll have a working TypeScript application that:
- Connects to RushDB using the official SDK
- Creates records with different labels and properties
- Queries records using filters and pagination
- Links records together using relationships
- Uses transactions for atomic operations

## Prerequisites

- Node.js 18+ and npm
- A RushDB account (free tier works fine)
- TypeScript familiarity

## Setup

### 1. Clone and Install Dependencies

```bash
cd typescript-sdk-quickstart-setting-up-your-first-ru-tutorial
npm install
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env`:
```
RUSHDB_API_KEY=your_api_key_here
```

Get your API key from the [RushDB dashboard](https://app.rushdb.com/settings/api-keys).

### 3. Seed Test Data (Optional)

Run the seed script to populate your database with sample data:

```bash
npm run seed
```

This creates sample authors and articles for you to query against.

### 4. Run the Tutorial

```bash
npm run dev
```

Expected output:
```
=== RushDB TypeScript SDK Quickstart ===

1. Initializing client...
   ✓ Client connected to RushDB

2. Creating records...
   ✓ Created author: Jane Doe (ID: abc123)
   ✓ Created article: Understanding Graph Databases

3. Finding records...
   ✓ Found 1 record(s) with name 'Jane Doe'
   ✓ Found record by ID: Jane Doe

4. Creating relationships...
   ✓ Linked article to author (WRITTEN_BY)

5. Transaction demo...
   ✓ Transaction committed: 2 records created atomically

6. Updating records...
   ✓ Updated author bio

7. Cleaning up...
   ✓ Deleted test records

=== Tutorial Complete ===
```

## Project Structure

```
├── src/
│   ├── main.ts        # Main tutorial code
│   └── seed.ts       # Seed script for test data
├── .env.example      # Environment variable template
├── package.json
├── tsconfig.json
└── README.md
```

## Key Concepts Demonstrated

| Concept | Method | Description |
|---------|--------|-------------|
| Client init | `new RushDB(apiKey)` | Connect to RushDB |
| Create record | `db.records.create()` | Create single record with label and data |
| Bulk create | `db.records.createMany()` | Create multiple records at once |
| Find records | `db.records.find()` | Query with filters, pagination |
| Find by ID | `db.records.findById()` | Retrieve specific record |
| Relationships | `db.records.attach()` | Link records together |
| Transactions | `db.transactions.begin()` | Atomic multi-step operations |
| Update | `db.records.update()` | Modify existing records |
| Delete | `db.records.deleteById()` | Remove records |

## Useful Links

- [RushDB Documentation](https://docs.rushdb.com)
- [TypeScript SDK Reference](https://docs.rushdb.com/sdks/typescript)
- [GitHub Examples](https://github.com/rush-db/examples)
