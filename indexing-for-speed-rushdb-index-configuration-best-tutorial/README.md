# Indexing for Speed: RushDB Index Configuration Best Practices

A practical tutorial demonstrating RushDB index configuration strategies for optimal query performance. Designed for senior engineers looking to master vector and property indexing in RushDB.

## What This Tutorial Covers

- **Vector index types**: Managed vs. external indexes and when to use each
- **Index configuration**: Dimensions, similarity functions, and source types
- **Performance monitoring**: Using `index.stats()` to track indexing progress
- **Query optimization**: Combining vector search with property filters
- **Best practices**: Index lifecycle management and maintenance

## Prerequisites

- Python 3.9+
- A RushDB account ([get one free](https://rushdb.com))
- `sentence-transformers` for embedding generation (external index demo)

## Setup

```bash
# Clone the repository
git clone https://github.com/rush-db/examples.git
cd indexing-for-speed-rushdb-index-configuration-best-tutorial

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your RushDB API key
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```
RUSHDB_API_KEY=your_api_key_here
RUSHDB_URL=https://api.rushdb.com/api/v1  # Optional: for self-hosted
```

## Running the Project

### Step 1: Seed the Database

Generate mock e-commerce product data to demonstrate indexing:

```bash
python seed.py
```

This creates 200+ products with rich descriptions across multiple categories.

### Step 2: Run the Indexing Tutorial

```bash
python main.py
```

## Expected Output

```
===========================================
RushDB Indexing Best Practices Tutorial
===========================================

[1/5] Creating vector indexes...
    ✓ Created 'external' index: PRODUCT.description (768 dimensions, cosine)
    ✓ Created 'managed' index: PRODUCT.shortDescription (managed embedding)

[2/5] Upserting records with vectors...
    ✓ Upserted 200 products with description vectors
    ✓ Upserted 200 products with shortDescription vectors

[3/5] Checking index statistics...
    Index: prod_desc_ext
      - Status: online
      - Indexed: 200 / 200 records
      - Dimensions: 768
      - Similarity: cosine

[4/5] Running vector searches...
    Query: "wireless headphones with noise cancellation"
    Results:
      1. [0.847] Sony WH-1000XM4 - $349.99
      2. [0.823] Bose QuietComfort 45 - $329.00
      3. [0.801] Apple AirPods Max - $549.00
      ...

[5/5] Combined search with property filters...
    Query: "laptop computer"
    Filter: category == "Electronics", price < 1000
    Results:
      1. [0.891] Dell XPS 13 - $999.00
      2. [0.876] MacBook Air M2 - $1199.00
      ...

===========================================
Tutorial Complete! ✓
===========================================
```

## Project Structure

```
indexing-for-speed-rushdb-index-configuration-best-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Mock data generation script
└── main.py             # Main tutorial code
```

## Key Concepts Demonstrated

### 1. Managed vs. External Indexes

```sdk
# Managed index - RushDB handles embedding generation
db.ai.indexes.create({
    "label": "PRODUCT",
    "propertyName": "shortDescription",
    "sourceType": "managed"
})

# External index - you provide pre-computed vectors
db.ai.indexes.create({
    "label": "PRODUCT",
    "propertyName": "description",
    "sourceType": "external",
    "dimensions": 768,
    "similarityFunction": "cosine"
})
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

// Managed index - server handles embedding
await db.ai.indexes.create({
    label: 'PRODUCT',
    propertyName: 'shortDescription',
    sourceType: 'managed'
})

// External index - client provides vectors
await db.ai.indexes.create({
    label: 'PRODUCT',
    propertyName: 'description',
    sourceType: 'external',
    dimensions: 768,
    similarityFunction: 'cosine'
})
```

### 2. Inline Vector Writes

```sdk
db.records.upsert(
    label="PRODUCT",
    data={"name": "Sony WH-1000XM4", "description": "Premium wireless headphones"},
    options={"mergeBy": ["name"]},
    vectors=[{"propertyName": "description", "vector": embedding}]
)
___SPLIT___
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_API_KEY!)

await db.records.upsert({
    label: 'PRODUCT',
    data: { name: 'Sony WH-1000XM4', description: 'Premium wireless headphones' },
    options: { mergeBy: ['name'] },
    vectors: [{ propertyName: 'description', vector: embedding }]
})
```

### 3. Monitoring Index Health

```sdk
stats = db.ai.indexes.stats(index_id)
print(f"Indexed: {stats['indexedRecords']}/{stats['totalRecords']}")
___SPLIT___
const stats = await db.ai.indexes.stats(indexId)
console.log(`Indexed: ${stats.indexedRecords}/${stats.totalRecords}`)
```

## Choosing the Right Index Type

| Scenario | Recommended Index Type |
|----------|------------------------|
| Short fields, flexible embedding | **Managed** |
| Custom embeddings (OpenAI, local models) | **External** |
| High-volume writes with pre-computed vectors | **External** |
| Prototype/quick testing | **Managed** |

## Similarity Functions

- **cosine**: Best for normalized vectors and most general use cases
- **euclidean**: Better for exact distance comparisons
- **dotProduct**: Optimal for unnormalized embeddings

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [Vector Search Guide](https://docs.rushdb.com/features/vector-search)
- [Pricing Information](https://rushdb.com/pricing)

## License

MIT License - See [rush-db/examples](https://github.com/rush-db/examples) for details.
