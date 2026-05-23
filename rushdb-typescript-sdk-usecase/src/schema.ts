import RushDB from '@rushdb/javascript-sdk';
import { generateEmbedding, EMBEDDING_DIMENSIONS } from './embeddings.js';
import seedData from '../data/seed-data.json' assert { type: 'json' };
import type { RushDBRecord } from './types.js';


// Initialize RushDB client
const db = new RushDB(process.env.RUSHDB_API_KEY!, {
  url: process.env.RUSHDB_URL,
});


// Label constants
export const LABELS = {
  USER: 'User',
  PRODUCT: 'Product',
  TOPIC: 'Topic',
  MESSAGE: 'Message',
  SESSION: 'Session',
  PURCHASE: 'Purchase',
} as const;

// Relationship type constants
export const RELATIONSHIPS = {
  ASKED_ABOUT: 'asked_about',
  PURCHASED: 'purchased',
  RELATED_TO: 'related_to',
  IN_SESSION: 'in_session',
  REPLIES_TO: 'replies_to',
  HAS_INTENT: 'has_intent',
} as const;


/**
 * Check if the knowledge graph is already initialized
 */
async function isInitialized(): Promise<boolean> {
  try {
    const { data: products } = await db.records.find({
      labels: [LABELS.PRODUCT],
      limit: 1,
    });
    return products.length > 0;
  } catch {
    return false;
  }
}

/**
 * Create vector index for Message content
 */
async function createMessageIndex(): Promise<string> {
  try {
    const { data: indexes } = await db.ai.indexes.find();
    const messageIndex = indexes.find(
      (idx: { label: string; propertyName: string }) =>
        idx.label === LABELS.MESSAGE && idx.propertyName === 'content'
    );

    if (messageIndex) {
      console.log('  ✓ Message vector index already exists');
      return messageIndex.__id;
    }


    const index = await db.ai.indexes.create({
      label: LABELS.MESSAGE,
      propertyName: 'content',
      dimensions: EMBEDDING_DIMENSIONS,
      sourceType: 'external',
      similarityFunction: 'cosine',
    });


    console.log('  ✓ Created Message vector index');
    return index.data.__id;
  } catch (error) {
    console.error('Error creating message index:', error);
    throw error;
  }
}

/**
 * Initialize users in the knowledge graph
 */
async function initializeUsers(): Promise<RushDBRecord[]> {
  console.log('  → Loading users...');
  const { data: existingUsers } = await db.records.find({
    labels: [LABELS.USER],
    limit: 1,
  });

  if (existingUsers.length > 0) {
    console.log(`  ✓ ${existingUsers.length} users already exist`);
    return existingUsers;
  }

  const users: RushDBRecord[] = [];
  for (const user of seedData.users) {
    const record = await db.records.create({
      label: LABELS.USER,
      data: user,
    });
    users.push(record);
  }

  console.log(`  ✓ Created ${users.length} users`);
  return users;
}

/**
 * Initialize products in the knowledge graph
 */
async function initializeProducts(): Promise<RushDBRecord[]> {
  console.log('  → Loading products...');
  const { data: existingProducts } = await db.records.find({
    labels: [LABELS.PRODUCT],
    limit: 1,
  });

  if (existingProducts.length > 0) {
    console.log(`  ✓ Products already exist`);
    return existingProducts;
  }


  const products: RushDBRecord[] = [];
  for (const product of seedData.products) {
    const record = await db.records.create({
      label: LABELS.PRODUCT,
      data: product,
    });
    products.push(record);
  }

  console.log(`  ✓ Created ${products.length} products`);
  return products;
}

/**
 * Initialize topics in the knowledge graph
 */
async function initializeTopics(): Promise<RushDBRecord[]> {
  console.log('  → Loading topics...');
  const { data: existingTopics } = await db.records.find({
    labels: [LABELS.TOPIC],
    limit: 1,
  });

  if (existingTopics.length > 0) {
    console.log(`  ✓ Topics already exist`);
    return existingTopics;
  }

  const topics: RushDBRecord[] = [];
  for (const topic of seedData.topics) {
    const record = await db.records.create({
      label: LABELS.TOPIC,
      data: topic,
    });
    topics.push(record);
  }

  console.log(`  ✓ Created ${topics.length} topics`);
  return topics;
}

/**
 * Initialize sample messages with vector embeddings
 */
async function initializeMessages(indexId: string): Promise<RushDBRecord[]> {
  console.log('  → Loading sample messages with embeddings...');
  const { data: existingMessages } = await db.records.find({
    labels: [LABELS.MESSAGE],
    limit: 1,
  });

  if (existingMessages.length > 0) {
    console.log(`  ✓ Messages already exist`);
    return existingMessages;
  }

  const messages: RushDBRecord[] = [];
  for (let i = 0; i < seedData.sampleMessages.length; i++) {
    const msg = seedData.sampleMessages[i];
    const content = msg.content;

    // Generate embedding for this message
    const vector = await generateEmbedding(content);

    // Create message record with vector embedding
    const record = await db.records.create(
      {
        label: LABELS.MESSAGE,
        data: {
          content,
          role: msg.role,
          intent: msg.intent,
          timestamp: Date.now() - (seedData.sampleMessages.length - i) * 1000,
        },
      },
      undefined,
      [{ propertyName: 'content', vector }]
    );

    messages.push(record);

    if ((i + 1) % 100 === 0) {
      console.log(`    Progress: ${i + 1}/${seedData.sampleMessages.length} messages`);
    }
  }


  console.log(`  ✓ Created ${messages.length} messages with vector embeddings`);
  return messages;
}

/**
 * Set up relationships between products (related_to)
 */
async function setupProductRelations(products: RushDBRecord[]): Promise<void> {
  console.log('  → Setting up product relationships...');

  // Find all products that are in the "耳机" (headphones) category
  const { data: headphones } = await db.records.find({
    labels: [LABELS.PRODUCT],
    where: { category: '耳机' },
  });

  // Create related_to relationships between headphone products
  for (let i = 0; i < headphones.length; i++) {
    for (let j = i + 1; j < headphones.length; j++) {
      await db.records.attach({
        source: headphones[i],
        target: headphones[j],
        options: { type: RELATIONSHIPS.RELATED_TO, direction: 'out' },
      });
    }
  }

  console.log(`  ✓ Created ${(headphones.length * (headphones.length - 1)) / 2} related_to links`);
}

/**
 * Create sample purchase history for demo
 */
async function setupPurchaseHistory(users: RushDBRecord[]): Promise<void> {
  console.log('  → Setting up purchase history...');

  // Get user 李四 (lisi@example.com)
  const { data: lisi } = await db.records.find({
    labels: [LABELS.USER],
    where: { email: 'lisi@example.com' },
  });

  // Get product 入耳式耳机 (earbuds)
  const { data: earbuds } = await db.records.find({
    labels: [LABELS.PRODUCT],
    where: { name: '入耳式耳机' },
  });

  if (lisi.length > 0 && earbuds.length > 0) {
    await db.records.attach({
      source: lisi[0],
      target: earbuds[0],
      options: { type: RELATIONSHIPS.PURCHASED, direction: 'out' },
    });
    console.log('  ✓ Created purchase history for demo user');
  }
}

/**
 * Main initialization function
 */
export async function initializeKnowledgeGraph(): Promise<void> {
  console.log('\n📊 Initializing knowledge graph schema...');

  // Check if already initialized
  const initialized = await isInitialized();
  if (initialized) {
    console.log('  ✓ Knowledge graph already initialized, skipping...');
    return;
  }

  // Step 1: Create vector index for semantic search
  const indexId = await createMessageIndex();

  // Step 2: Initialize entities
  const users = await initializeUsers();
  const products = await initializeProducts();
  const topics = await initializeTopics();

  // Step 3: Initialize messages with embeddings
  await initializeMessages(indexId);

  // Step 4: Set up relationships
  await setupProductRelations(products);
  await setupPurchaseHistory(users);

  console.log('\n✅ Knowledge graph initialized successfully!\n');
}

export { db };
