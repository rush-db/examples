/**
 * TypeScript SDK implementation — RushDB Python vs Node.js Comparison
 *
 * Demonstrates the three most common patterns:
 * 1. CRUD Operations
 * 2. Graph Traversal
 * 3. Vector Similarity Search
 *
 * Each pattern is shown side-by-side with commentary on ergonomic differences.
 */

import process from 'process'
import RushDB from '@rushdb/javascript-sdk'

// Initialize the client
const apiKey = process.env.RUSHDB_API_KEY
if (!apiKey) {
  throw new Error(
    'RUSHDB_API_KEY not found. ' +
    'Copy .env.example to .env and fill in your API key.'
  )
}

const db = new RushDB(apiKey)

// ===============================
// PATTERN 1: CRUD OPERATIONS
// ===============================

async function demonstrateCrud(): Promise<void> {
  /**
   * Both SDKs support full CRUD. TypeScript is async/await, returns typed responses.
   *
   * Key TypeScript patterns:
   * - await db.records.create({ label: 'LABEL', data: {...} }) — object syntax, always await
   * - await db.records.find({...}) — returns { data: T[], total: number }
   * - response.data[0].id, response.data[0].data — typed access
   */
  console.log('\n' + '='.repeat(60))
  console.log('PATTERN 1: CRUD OPERATIONS (TypeScript SDK)')
  console.log('='.repeat(60))

  // Create a movie record
  const movie = await db.records.create({
    label: 'MOVIE',
    data: { title: 'Oppenheimer', year: 2023, rating: 8.9, genre: 'drama' },
  })
  console.log(`\n[CREATE] Movie '${movie.data.title}' created with ID: ${movie.id}`)

  // Find movies with high ratings
  const results = await db.records.find({
    labels: ['MOVIE'],
    where: { rating: { $gte: 8.5 } },
    limit: 10,
    orderBy: { rating: 'desc' },
  })
  console.log(`\n[FIND] Found ${results.total} movies with rating >= 8.5:`)
  for (const m of results.data) {
    console.log(`  - ${m.data.title} (${m.data.year}): ★ ${m.data.rating}`)
  }

  // Update the record
  await db.records.update({ recordId: movie.id, data: { rating: 9.0 } })
  console.log('\n[UPDATE] Oppenheimer rating updated to 9.0')

  // Verify the update
  const updated = await db.records.findById(movie.id)
  console.log(`[VERIFY] Updated rating: ${(updated as any).data.rating}`)

  // Delete the test record (cleanup)
  await db.records.deleteById(movie.id)
  console.log('\n[DELETE] Oppenheimer deleted')

  console.log('\n→ TypeScript SDK: async/await, typed responses with .data property')
  console.log('→ Python: synchronous, dict-like Record objects')
}

// ===============================
// PATTERN 2: GRAPH TRAVERSAL
// ===============================

async function demonstrateGraph(): Promise<void> {
  /**
   * RushDB stores records as graph nodes. Filter by related record properties.
   *
   * Key TypeScript patterns:
   * - await db.records.find({...}) with nested where clauses
   * - { LABEL: { $relation: {...}, field: value }} for relationship filters
   * - await db.records.attach({ source: ..., target: ..., options: {...} }) for relationships
   */
  console.log('\n' + '='.repeat(60))
  console.log('PATTERN 2: GRAPH TRAVERSAL (TypeScript SDK)')
  console.log('='.repeat(60))

  // Find actors in high-rated sci-fi movies using relationship traversal
  // Filter: ACTOR records where the related MOVIE has rating >= 8.5 AND genre = sci-fi
  const actorsInQualitySciFi = await db.records.find({
    labels: ['ACTOR'],
    where: {
      MOVIE: {
        $relation: { type: 'ACTED_IN', direction: 'in' },
        rating: { $gte: 8.5 },
        genre: 'sci-fi',
      },
    },
  })

  console.log(`\n[GRAPH TRAVERSE] Actors in high-rated sci-fi movies: ${actorsInQualitySciFi.total}`)
  for (const actor of actorsInQualitySciFi.data) {
    // Find the related movies for this actor
    const related = await db.records.find({
      labels: ['MOVIE'],
      where: {
        ACTOR: { $relation: { type: 'ACTED_IN', direction: 'in' } },
      },
    })
    const movieTitles = related.data.map((m) => (m.data as any).title)
    console.log(`  - ${(actor.data as any).name}: ${movieTitles.join(', ')}`)
  }

  // Find all movies and their actors
  const allMovies = await db.records.find({
    labels: ['MOVIE'],
    limit: 5,
    orderBy: { title: 'asc' },
  })

  console.log('\n[GRAPH] Movies and their cast:')
  for (const movie of allMovies.data) {
    const cast = await db.records.find({
      labels: ['ACTOR'],
      where: {
        MOVIE: {
          $id: movie.id,
          $relation: { type: 'ACTED_IN', direction: 'in' },
        },
      },
    })
    const castNames = cast.data.map((a) => (a.data as any).name)
    const movieData = movie.data as any
    console.log(
      `  '${movieData.title}' (${movieData.year}) starring: ${
        castNames.length > 0 ? castNames.join(', ') : 'unknown'
      }`
    )
  }

  console.log('\n→ Graph traversal uses relationship filters in where clause')
  console.log('→ No Cypher queries needed — RushDB handles graph traversal internally')
}

// ===============================
// PATTERN 3: VECTOR SIMILARITY SEARCH
// ===============================

async function demonstrateVectorSearch(): Promise<void> {
  /**
   * Store records with vector embeddings, then search semantically.
   *
   * Key TypeScript patterns:
   * - await db.records.create({...}, vectors: [{ propertyName: 'field', vector: [...] }]) for writes
   * - await db.ai.search({...}) for similarity search
   * - result.data[0].score — similarity score from search results
   *
   * Note: This demo uses mock embeddings. In production, use OpenAI embeddings
   * or similar to generate real vectors.
   */
  console.log('\n' + '='.repeat(60))
  console.log('PATTERN 3: VECTOR SIMILARITY SEARCH (TypeScript SDK)')
  console.log('='.repeat(60))

  // Ensure we have vector data
  const existingArticles = await db.records.find({ labels: ['ARTICLE'], limit: 1 })
  if (existingArticles.total === 0) {
    console.log('\n[SKIP] No articles found. Run `npx tsx seed.ts` first.')
    return
  }

  // Semantic search: find articles about AI and machine learning
  // Using a natural language query (RushDB embeds it server-side)
  const aiResults = await db.ai.search({
    propertyName: 'content',
    query: 'machine learning and neural networks',
    labels: ['ARTICLE'],
    limit: 5,
  })

  console.log('\n[SEMANTIC SEARCH] Articles about \'machine learning and neural networks\':')
  for (const article of aiResults.data) {
    const articleData = article.data as any
    const score = (article as any).score ?? 0
    console.log(`  [${score.toFixed(3)}] ${articleData.title}`)
    console.log(`       Tags: ${articleData.tags?.join(', ') ?? 'none'}`)
  }

  // Filter by tag in addition to semantic similarity
  const taggedResults = await db.ai.search({
    propertyName: 'content',
    query: 'database technology',
    labels: ['ARTICLE'],
    where: { tags: { $contains: 'databases' } },
    limit: 3,
  })

  console.log('\n[SEMANTIC SEARCH] Articles about \'database technology\' tagged \'databases\':')
  for (const article of taggedResults.data) {
    console.log(`  - ${(article.data as any).title}`)
  }

  // Count total indexed articles
  const allArticles = await db.records.find({ labels: ['ARTICLE'] })
  console.log(`\n[INDEX] Total articles: ${allArticles.total}`)

  console.log('\n→ Vector search uses natural language queries (server embeds the query)')
  console.log('→ Combine semantic similarity with standard field filters')
  console.log('→ result.score gives similarity confidence (higher = more similar)')
}

// ===============================
// ERGONOMIC COMPARISON SUMMARY
// ===============================

function printSummary(): void {
  console.log('\n' + '='.repeat(60))
  console.log('SDK ERGONOMIC SUMMARY')
  console.log('='.repeat(60))
  console.log(`
| Aspect              | Python SDK               | TypeScript SDK           |
|---------------------|--------------------------|--------------------------|
| Async Model         | Synchronous (blocking)   | async/await (non-blocking)|
| Response Style      | Record objects (dict)    | Typed responses (T[])    |
| Method Names        | snake_case               | camelCase                |
| Transaction Syntax  | with db.transactions...  | await db.tx.begin()      |
| ML/AI Integration   | Native (sentence-transformers)| Via HTTP/external    |
| Web Framework       | Works but less idiomatic | Next.js, Express-native  |
| Type Safety         | Duck-typed               | Full TypeScript inference|

When to choose Python:
  → Data pipelines, ETL, batch scripts
  → ML/AI workflows (RAG, embeddings)
  → Rapid prototyping (no async ceremony)

When to choose TypeScript:
  → Web APIs (Next.js, Express)
  → Real-time apps (WebSocket integrations)
  → Full-stack projects (shared types)
`)
}

// ===============================
// MAIN EXECUTION
// ===============================

async function main(): Promise<void> {
  console.log('\n' + '#'.repeat(60))
  console.log('# RushDB TypeScript SDK — Comparison Demo')
  console.log('# See python/ for the equivalent Python implementation')
  console.log('#'.repeat(60))

  await demonstrateCrud()
  await demonstrateGraph()
  await demonstrateVectorSearch()
  printSummary()

  console.log('\n' + '='.repeat(60))
  console.log('Demo complete!')
  console.log('='.repeat(60))
}

main().catch(console.error)
