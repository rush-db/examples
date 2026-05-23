import RushDB from '@rushdb/javascript-sdk';
import { generateEmbedding } from './embeddings.js';
import { db, LABELS, RELATIONSHIPS } from './schema.js';
import type { RushDBRecord, ChatContext, ContextQueryResult } from './types.js';

/**
 * Layer 1: Semantic Search using vector similarity
 * Find similar messages based on semantic meaning
 */
export async function semanticSearch(
  query: string,
  limit: number = 5
): Promise<{ record: RushDBRecord; score: number }[]> {
  console.log(`  → Layer 1: Semantic search for "${query}"`);


  try {
    const { data } = await db.ai.search({
      propertyName: 'content',
      query,
      labels: [LABELS.MESSAGE],
      limit,
    });

    const results = data.map((record: RushDBRecord & { __score?: number }) => ({
      record,
      score: record.__score || 0,
    }));

    console.log(`    Found ${results.length} similar messages`);
    return results;
  } catch (error) {
    console.log('    Semantic search unavailable (no index), falling back...');
    return [];
  }
}

/**
 * Layer 2: Graph traversal for context resolution
 * Find user's purchase history and related products
 */
export async function resolveUserContext(
  userEmail: string
): Promise<ChatContext> {
  console.log(`  → Layer 2: Graph traversal for user "${userEmail}"`);

  const context: ChatContext = {
    recentMessages: [],
    userPurchaseHistory: [],
  };

  // Find user by email
  const { data: users } = await db.records.find({
    labels: [LABELS.USER],
    where: { email: userEmail },
    limit: 1,
  });


  if (users.length === 0) {
    console.log('    User not found, returning empty context');
    return context;
  }

  const user = users[0];
  console.log(`    Found user: ${(user as { name: string }).name}`);

  // Find products purchased by this user via relationship
  const { data: purchases } = await db.records.find({
    labels: [LABELS.PRODUCT],
    where: {
      [LABELS.USER]: {
        $relation: { type: RELATIONSHIPS.PURCHASED, direction: 'in' },
        email: userEmail,
      },
    },
    limit: 10,
  });

  context.userPurchaseHistory = purchases as ChatContext['userPurchaseHistory'];
  console.log(`    Found ${purchases.length} products in purchase history`);

  return context;
}

/**
 * Find products related to a given product
 */
export async function findRelatedProducts(productName: string): Promise<RushDBRecord[]> {
  console.log(`  → Finding products related to "${productName}"`);


  const { data: products } = await db.records.find({
    labels: [LABELS.PRODUCT],
    where: {
      [LABELS.PRODUCT]: {
        $relation: { type: RELATIONSHIPS.RELATED_TO, direction: 'in' },
        name: productName,
      },
    },
    limit: 5,
  });

  return products;
}

/**
 * Detect intent from user message using topic matching
 */
export async function detectIntent(message: string): Promise<string | null> {
  console.log(`  → Detecting intent for "${message}"`);

  // Get all topics
  const { data: topics } = await db.records.find({
    labels: [LABELS.TOPIC],
  });

  // Simple keyword matching for intent detection
  const lowerMessage = message.toLowerCase();
  let bestMatch: string | null = null;
  let maxScore = 0;

  for (const topic of topics as Array<{ name: string; keywords: string[] }>) {
    const score = topic.keywords.filter((kw) =>
      lowerMessage.includes(kw.toLowerCase())
    ).length;

    if (score > maxScore) {
      maxScore = score;
      bestMatch = topic.name;
    }
  }

  console.log(`    Detected intent: ${bestMatch || 'unknown'}`);
  return bestMatch;
}

/**
 * Get product details by name
 */
export async function getProductByName(name: string): Promise<RushDBRecord | null> {
  const { data: products } = await db.records.find({
    labels: [LABELS.PRODUCT],
    where: { name },
    limit: 1,
  });

  return products.length > 0 ? products[0] : null;
}

/**
 * Get conversation history for a session
 */
export async function getConversationHistory(
  sessionId: string,
  limit: number = 10
): Promise<RushDBRecord[]> {
  const { data: messages } = await db.records.find({
    labels: [LABELS.MESSAGE],
    where: {
      [LABELS.SESSION]: {
        $relation: { type: RELATIONSHIPS.IN_SESSION, direction: 'in' },
        id: sessionId,
      },
    },
    orderBy: { timestamp: 'asc' },
    limit,
  });

  return messages;
}

/**
 * Complete context query: combines vector search + graph traversal
 */
export async function queryContext(
  userMessage: string,
  userEmail: string,
  currentProduct?: string
): Promise<ContextQueryResult> {
  console.log('\n🧠 Context Query Starting...');

  // Parallel execution of semantic search and graph traversal
  const [similarMessages, userContext] = await Promise.all([
    semanticSearch(userMessage),
    resolveUserContext(userEmail),
  ]);

  let relatedProducts: RushDBRecord[] = [];
  if (currentProduct) {
    relatedProducts = await findRelatedProducts(currentProduct);
  }

  // Detect intent from message
  const detectedIntent = await detectIntent(userMessage);

  return {
    similarMessages,
    userHistory: userContext.userPurchaseHistory[0] as unknown as null,
    purchaseHistory: userContext.userPurchaseHistory,
    relatedProducts,
  };
}
