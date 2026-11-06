/**
 * RushDB TypeScript SDK Quickstart
 * 
 * This tutorial demonstrates the core operations of the RushDB TypeScript SDK:
 * - Client initialization
 * - Record creation (single and bulk)
 * - Querying records (find, findById)
 * - Creating relationships between records
 * - Using transactions for atomic operations
 * - Updating and deleting records
 */

import RushDB from '@rushdb/javascript-sdk';
import dotenv from 'dotenv';

dotenv.config();

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_KEY = process.env.RUSHDB_API_KEY;

if (!API_KEY) {
  console.error('❌ Missing RUSHDB_API_KEY environment variable');
  console.error('   Copy .env.example to .env and add your API key');
  process.exit(1);
}

// =============================================================================
// TUTORIAL: Core SDK Operations
// =============================================================================

async function runTutorial() {
  console.log('\n=== RushDB TypeScript SDK Quickstart ===\n');

  // ==========================================================================
  // 1. Initialize the RushDB Client
  // ==========================================================================
  console.log('1. Initializing client...');
  
  const db = new RushDB(API_KEY);
  console.log('   ✓ Client connected to RushDB\n');

  // ==========================================================================
  // 2. Create Records
  // ==========================================================================
  console.log('2. Creating records...');

  // Create a single record with the 'AUTHOR' label
  const author = await db.records.create({
    label: 'AUTHOR',
    data: {
      name: 'Jane Doe',
      email: 'jane.doe@example.com',
      bio: 'Technical writer and developer advocate'
    }
  });
  console.log(`   ✓ Created author: ${author.data.name} (ID: ${author.id})`);

  // Create another record - an article
  const article = await db.records.create({
    label: 'ARTICLE',
    data: {
      title: 'Understanding Graph Databases',
      publishedAt: new Date().toISOString(),
      tags: ['database', 'graphs', 'tutorial']
    }
  });
  console.log(`   ✓ Created article: ${article.data.title}`);

  // Create multiple records at once using createMany
  const additionalAuthors = await db.records.createMany({
    label: 'AUTHOR',
    data: [
      { name: 'Alice Smith', email: 'alice@example.com' },
      { name: 'Bob Johnson', email: 'bob@example.com' }
    ]
  });
  console.log(`   ✓ Created ${additionalAuthors.data.length} additional authors\n`);

  // ==========================================================================
  // 3. Find Records
  // ==========================================================================
  console.log('3. Finding records...');

  // Find records using filters with the 'where' clause
  const { data: foundAuthors, total } = await db.records.find({
    labels: ['AUTHOR'],
    where: {
      name: 'Jane Doe'
    }
  });
  console.log(`   ✓ Found ${total} record(s) with name 'Jane Doe'`);

  // Find a specific record by its ID
  const authorById = await db.records.findById(author.id);
  if (authorById) {
    console.log(`   ✓ Found record by ID: ${authorById.data.name}`);
  }

  // Find with pagination - skip first 2 results, limit to 5
  const { data: paginatedAuthors } = await db.records.find({
    labels: ['AUTHOR'],
    skip: 2,
    limit: 5
  });
  console.log(`   ✓ Paginated query returned ${paginatedAuthors.length} authors`);

  // Find a single record using findOne (returns first match or null)
  const singleAuthor = await db.records.findOne({
    labels: ['AUTHOR'],
    where: { email: 'jane.doe@example.com' }
  });
  if (singleAuthor) {
    console.log(`   ✓ findOne returned: ${singleAuthor.data.name}\n`);
  }

  // ==========================================================================
  // 4. Create Relationships (Attach)
  // ==========================================================================
  console.log('4. Creating relationships...');

  // Link the article to its author using the attach method
  // The source is the article, target is the author
  await db.records.attach({
    source: article,
    target: author,
    options: { type: 'WRITTEN_BY', direction: 'out' }
  });
  console.log('   ✓ Linked article to author (WRITTEN_BY relationship)\n');

  // ==========================================================================
  // 5. Transactions
  // ==========================================================================
  console.log('5. Transaction demo...');

  // Begin a transaction for atomic operations
  const tx = await db.transactions.begin();

  try {
    // Create multiple records within the transaction
    const txAuthor = await db.records.create({
      label: 'AUTHOR',
      data: { name: 'Transaction Author', email: 'tx@example.com' }
    }, tx);

    const txArticle = await db.records.create({
      label: 'ARTICLE',
      data: { title: 'Transaction Test Article' }
    }, tx);

    // Link them within the transaction
    await db.records.attach({
      source: txArticle,
      target: txAuthor,
      options: { type: 'WRITTEN_BY', direction: 'out' }
    }, tx);

    // Commit the transaction - all operations succeed together
    await tx.commit();
    console.log('   ✓ Transaction committed: 2 records created atomically\n');
  } catch (error) {
    // Rollback on failure - none of the operations persist
    await tx.rollback();
    console.error('   ✗ Transaction rolled back:', error);
    throw error;
  }

  // ==========================================================================
  // 6. Update Records
  // ==========================================================================
  console.log('6. Updating records...');

  // Update the author's bio
  const updatedAuthor = await db.records.update({
    recordId: author.id,
    data: {
      bio: 'Updated bio: Technical writer, developer advocate, and open source enthusiast'
    }
  });
  console.log(`   ✓ Updated author bio`);

  // Update via record object (alternative syntax)
  await author.update({
    email: 'jane.updated@example.com'
  });
  console.log(`   ✓ Updated author email via record object\n`);

  // ==========================================================================
  // 7. Clean Up (Delete Records)
  // ==========================================================================
  console.log('7. Cleaning up...');

  // Delete the records we created during the tutorial
  await db.records.deleteById([
    author.id,
    article.id,
    txAuthor.id,
    txArticle.id
  ]);
  console.log('   ✓ Deleted test records\n');

  // Delete the additional authors we created
  for (const a of additionalAuthors.data) {
    await db.records.deleteById(a.id);
  }
  console.log('   ✓ Cleaned up all tutorial records\n');

  console.log('=== Tutorial Complete ===\n');
}

// =============================================================================
// RUN THE TUTORIAL
// =============================================================================

runTutorial()
  .then(() => {
    console.log('All operations completed successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Tutorial failed:', error);
    process.exit(1);
  });
