/**
 * Seed Script for RushDB TypeScript SDK Quickstart
 * 
 * This script populates your RushDB instance with sample data
 * that you can use to experiment with queries and relationships.
 * 
 * Run with: npm run seed
 */

import RushDB from '@rushdb/javascript-sdk';
import dotenv from 'dotenv';

dotenv.config();

const API_KEY = process.env.RUSHDB_API_KEY;

if (!API_KEY) {
  console.error('❌ Missing RUSHDB_API_KEY environment variable');
  process.exit(1);
}

// Sample data for seeding
const sampleAuthors = [
  {
    name: 'Dr. Sarah Chen',
    email: 'sarah.chen@techcorp.com',
    role: 'Principal Engineer',
    expertise: ['distributed systems', 'graph databases']
  },
  {
    name: 'Marcus Williams',
    email: 'marcus.w@startup.io',
    role: 'CTO',
    expertise: ['machine learning', 'data pipelines']
  },
  {
    name: 'Elena Rodriguez',
    email: 'elena.r@cloudnative.dev',
    role: 'Developer Advocate',
    expertise: ['kubernetes', 'devops']
  },
  {
    name: 'James Park',
    email: 'james.park@aisystems.com',
    role: 'ML Architect',
    expertise: ['neural networks', 'vector databases']
  },
  {
    name: 'Aisha Patel',
    email: 'aisha@dataengineering.co',
    role: 'Senior Data Engineer',
    expertise: ['etl', 'data warehousing']
  }
];

const sampleArticles = [
  {
    title: 'Getting Started with Graph Databases',
    slug: 'getting-started-graph-databases',
    content: 'Graph databases represent data as nodes and edges, making them ideal for highly connected data...',
    readTimeMinutes: 8,
    publishedAt: '2024-01-15T10:00:00Z'
  },
  {
    title: 'Vector Search Explained',
    slug: 'vector-search-explained',
    content: 'Vector search enables semantic similarity matching by representing data as numerical vectors...',
    readTimeMinutes: 12,
    publishedAt: '2024-01-22T14:30:00Z'
  },
  {
    title: 'Building RAG Applications with RushDB',
    slug: 'building-rag-applications',
    content: 'Retrieval Augmented Generation combines the power of LLMs with vector search...',
    readTimeMinutes: 15,
    publishedAt: '2024-02-05T09:00:00Z'
  },
  {
    title: 'TypeScript SDK: A Complete Guide',
    slug: 'typescript-sdk-complete-guide',
    content: 'Learn how to integrate RushDB into your TypeScript projects with the official SDK...',
    readTimeMinutes: 20,
    publishedAt: '2024-02-12T11:00:00Z'
  },
  {
    title: 'Transactions in RushDB',
    slug: 'transactions-in-rushdb',
    content: 'ACID transactions ensure data consistency even in complex multi-step operations...',
    readTimeMinutes: 10,
    publishedAt: '2024-02-20T16:00:00Z'
  }
];

async function seed() {
  console.log('\n=== RushDB Seed Script ===\n');
  
  const db = new RushDB(API_KEY);
  console.log('✓ Connected to RushDB\n');

  // Check if data already exists (idempotent)
  const existing = await db.records.find({
    labels: ['AUTHOR'],
    where: { email: 'sarah.chen@techcorp.com' }
  });

  if (existing.total > 0) {
    console.log('⚠ Sample data already exists. Skipping seed.');
    console.log('   Run the cleanup or use the main tutorial directly.\n');
    return;
  }

  console.log('Creating sample authors...');
  const authors = await db.records.createMany({
    label: 'AUTHOR',
    data: sampleAuthors
  });
  console.log(`   ✓ Created ${authors.data.length} authors\n`);

  console.log('Creating sample articles...');
  const articles = await db.records.createMany({
    label: 'ARTICLE',
    data: sampleArticles
  });
  console.log(`   ✓ Created ${articles.data.length} articles\n`);

  console.log('Creating relationships...');
  // Link articles to authors based on a simple round-robin assignment
  for (let i = 0; i < articles.data.length; i++) {
    const article = articles.data[i];
    const author = authors.data[i % authors.data.length];

    await db.records.attach({
      source: article,
      target: author,
      options: { type: 'WRITTEN_BY', direction: 'out' }
    });
  }
  console.log(`   ✓ Created ${articles.data.length} WRITTEN_BY relationships\n`);

  // Create some additional relationships for richer graph
  console.log('Creating additional relationships...');
  
  // Articles can reference other articles (related articles)
  const [article1, article2, article3] = articles.data;
  
  await db.records.attach({
    source: article2,
    target: article1,
    options: { type: 'REFERENCES', direction: 'out' }
  });
  await db.records.attach({
    source: article3,
    target: article2,
    options: { type: 'REFERENCES', direction: 'out' }
  });
  
  console.log('   ✓ Created cross-references between articles\n');

  console.log('=== Seed Complete ===\n');
  console.log('Sample data summary:');
  console.log(`  • ${authors.data.length} authors`);
  console.log(`  • ${articles.data.length} articles`);
  console.log(`  • ${articles.data.length} WRITTEN_BY links`);
  console.log(`  • 2 REFERENCES links\n`);
  console.log('You can now run the main tutorial or query this data directly.\n');
}

seed()
  .then(() => {
    console.log('Seed completed successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Seed failed:', error);
    process.exit(1);
  });
