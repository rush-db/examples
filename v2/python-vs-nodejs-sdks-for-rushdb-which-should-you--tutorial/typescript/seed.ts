/**
 * Seed script for RushDB TypeScript SDK comparison.
 *
 * Creates a small graph of Movies, Actors, and Articles to demonstrate
 * graph traversal and vector similarity search patterns.
 *
 * This script is idempotent — running it multiple times is safe.
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

// Sample data
const MOVIES = [
  { title: 'Inception', year: 2010, rating: 8.8, genre: 'sci-fi' },
  { title: 'The Dark Knight', year: 2008, rating: 9.0, genre: 'action' },
  { title: 'Interstellar', year: 2014, rating: 8.6, genre: 'sci-fi' },
  { title: 'Dunkirk', year: 2017, rating: 7.8, genre: 'war' },
  { title: 'Tenet', year: 2020, rating: 7.5, genre: 'sci-fi' },
]

const ACTORS = [
  { name: 'Leonardo DiCaprio', age: 49 },
  { name: 'Christian Bale', age: 49 },
  { name: 'Michael Caine', age: 89 },
  { name: 'Marion Cotillard', age: 48 },
  { name: 'Tom Hardy', age: 46 },
]

const ARTICLES = [
  {
    title: 'Understanding Transformer Architecture',
    content:
      'Transformers revolutionized NLP by using self-attention mechanisms ' +
      'to process sequences in parallel. Unlike RNNs, transformers can ' +
      'capture long-range dependencies efficiently.',
    tags: ['ai', 'machine-learning'],
  },
  {
    title: 'Introduction to Graph Neural Networks',
    content:
      'Graph Neural Networks (GNNs) extend deep learning to graph-structured ' +
      'data. They can reason about relationships between entities, making them ' +
      'ideal for social networks and knowledge graphs.',
    tags: ['ai', 'deep-learning'],
  },
  {
    title: 'Building RAG Applications',
    content:
      'Retrieval-Augmented Generation combines vector search with LLMs to ' +
      'produce contextually relevant answers grounded in your documents. ' +
      'This pattern is essential for enterprise AI applications.',
    tags: ['ai', 'rag', 'llm'],
  },
  {
    title: 'Vector Databases Explained',
    content:
      'Vector databases store high-dimensional embeddings that enable ' +
      'semantic similarity search. Unlike traditional databases, they excel ' +
      'at finding conceptually similar items rather than exact matches.',
    tags: ['databases', 'ai'],
  },
  {
    title: 'AsyncIO Best Practices',
    content:
      "Python's asyncio library enables concurrent I/O operations without " +
      'threads. Proper use involves async/await syntax, event loop management, ' +
      'and avoiding blocking calls in async functions.',
    tags: ['python', 'async'],
  },
]

// Deterministic random for mock embeddings
function seededRandom(seed: number): () => number {
  let s = seed
  return () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
}

async function seedGraphData(): Promise<void> {
  console.log('Seeding graph data (Movies and Actors)...')

  // Check if data already exists
  const existing = await db.records.find({
    labels: ['MOVIE'],
    where: { title: 'Inception' },
  })
  if (existing.total > 0) {
    console.log('  Graph data already exists, skipping seed.')
    return
  }

  // Create movies
  const movies: Awaited<ReturnType<typeof db.records.create>>[] = []
  for (const movieData of MOVIES) {
    const movie = await db.records.create({ label: 'MOVIE', data: movieData })
    movies.push(movie)
    console.log(`  Created movie: ${movieData.title}`)
  }

  // Create actors and relationships
  for (let i = 0; i < ACTORS.length; i++) {
    const actorData = ACTORS[i]
    const actor = await db.records.create({ label: 'ACTOR', data: actorData })

    // Each actor acts in a random subset of movies
    const numMovies = Math.floor(Math.random() * 3) + 1
    const selectedIndices = new Set<number>()
    while (selectedIndices.size < numMovies) {
      selectedIndices.add(Math.floor(Math.random() * movies.length))
    }

    for (const idx of selectedIndices) {
      await db.records.attach({
        source: movies[idx],
        target: actor,
        options: { type: 'ACTED_IN' },
      })
    }
    console.log(`  Created actor: ${actorData.name} (${selectedIndices.size} movies)`)
  }

  console.log('  Graph data seeded successfully!\n')
}

async function seedVectorData(): Promise<void> {
  console.log('Seeding vector data (Articles)...')

  // Check if data already exists
  const existing = await db.records.find({
    labels: ['ARTICLE'],
    where: { title: 'Understanding Transformer Architecture' },
  })
  if (existing.total > 0) {
    console.log('  Article data already exists, skipping seed.')
    return
  }

  // Create a vector index for the content property
  try {
    const indexes = await db.ai.indexes.find()
    let articleIndex = indexes.data.find(
      (idx) => idx.label === 'ARTICLE' && idx.propertyName === 'content'
    )

    if (!articleIndex) {
      console.log('  Creating vector index for ARTICLE.content...')
      const index = await db.ai.indexes.create({
        label: 'ARTICLE',
        propertyName: 'content',
        sourceType: 'external',
        dimensions: 384,
      })
      console.log(`  Index created: ${index.data.__id}`)
    }
  } catch (e) {
    console.log(`  Index creation warning: ${e}`)
  }

  // Generate mock embedding vectors (deterministic for reproducibility)
  // In production, use OpenAI embeddings or similar
  function mockEmbedding(text: string, dim: number = 384): number[] {
    const seed = text.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
    const random = seededRandom(seed)
    return Array.from({ length: dim }, () => random() * 2 - 1)
  }

  // Create articles with embeddings
  for (let i = 0; i < ARTICLES.length; i++) {
    const articleData = ARTICLES[i]
    const vector = mockEmbedding(articleData.content)

    await db.records.create({
      label: 'ARTICLE',
      data: articleData,
      vectors: [{ propertyName: 'content', vector }],
    })
    console.log(`  Created article: ${articleData.title} (dim=384)`)

    // Progress indicator
    if ((i + 1) % 100 === 0) {
      console.log(`  ... ${i + 1} articles created`)
    }
  }

  console.log('  Vector data seeded successfully!\n')
}

async function main(): Promise<void> {
  console.log('='.repeat(60))
  console.log('RushDB TypeScript SDK — Seed Script')
  console.log('='.repeat(60))
  console.log()

  await seedGraphData()
  await seedVectorData()

  console.log('='.repeat(60))
  console.log('Seed complete! Run `npx tsx main.ts` to see the SDK comparison.')
  console.log('='.repeat(60))
}

main().catch(console.error)
