/**
 * seed.ts — Creates INPUT records for the reflection agent to process.
 *
 * These are realistic documents across three document types:
 * invoice, support_ticket, technical_doc.
 *
 * Idempotent: safe to run multiple times. Detects existing INPUT records
 * and skips creation if they already exist.
 */

import * as dotenv from 'dotenv';
import { RushDB } from '@rushdb/javascript-sdk';

dotenv.config();

const API_KEY = process.env.RUSHDB_API_KEY;
if (!API_KEY) {
  console.error('❌ RUSHDB_API_KEY is not set in .env');
  process.exit(1);
}

const db = new RushDB(API_KEY);

const INPUT_DOCUMENTS = [
  {
    title: 'Invoice document',
    docType: 'invoice' as const,
    content: `Invoice #INV-2024-0847  
Date: 10/15/2024  
From: Acme Supplies Ltd.  
Bill To: TechCorp Inc.  
  
2x Premium printer paper, A4, 500 sheets — $45.00  
1x Wireless mouse, ergonomic — $29.50  
3x USB-C charging cable, 2m — $24.00  
1x Laptop stand, aluminum — $76.00  
  
Subtotal: $174.50  
Tax (8%): $13.96  
Total: $188.46  
Payment terms: Net 30`,
  },
  {
    title: 'Support ticket',
    docType: 'support_ticket' as const,
    content: `Subject: Missing items in my order — urgent  
Priority: HIGH  
Category: REFUND_REQUEST  
Order: ORD-9921-XK  
  
I received my order on October 12th and noticed that two items are  
completely missing from the box. I paid for a wireless keyboard and a  
webcam but only found the keyboard inside. This is the second time  
this has happened in three months and I'm very frustrated. I would  
like a full refund for the missing item and an explanation. Please  
escalate this to a manager if necessary.`,
  },
  {
    title: 'Technical documentation',
    docType: 'technical_doc' as const,
    content: `API Deprecation Notice  
Endpoint: /api/v1/user/settings  
Replacement: /api/v2/preferences  
Sunset date: 2025-12-31  
  
The legacy /api/v1/user/settings endpoint will be deprecated on  
December 31st, 2025. Migration guide available at /docs/migration/v1-to-v2.  
All integrations must be updated before the sunset date or requests  
will return 410 Gone.`,
  },
];

async function seed() {
  // Check for existing INPUT records to make the script idempotent
  const existing = await db.records.find({ labels: ['INPUT'], limit: 50 });
  const existingTitles = new Set(
    existing.data.map((r) => r.data['title'] as string)
  );

  const toCreate = INPUT_DOCUMENTS.filter(
    (doc) => !existingTitles.has(doc.title)
  );

  if (toCreate.length === 0) {
    console.log('\n✓ All INPUT records already exist (idempotent check passed).');
    console.log(`  ${existing.data.length} INPUT record(s) found in RushDB.\n`);
    return;
  }

  console.log(`\n🌱 Seeding ${toCreate.length} INPUT document(s)...\n`);

  const records = await db.records.createMany({
    label: 'INPUT',
    data: toCreate.map((doc) => ({
      title: doc.title,
      docType: doc.docType,
      content: doc.content,
      seededAt: new Date().toISOString(),
    })),
  });

  console.log(`✓ Created ${records.data.length} INPUT record(s).\n`);
  console.log('  Run `npm start` to process these with the reflection agent.\n');
}

seed().catch((err) => {
  console.error('Seed failed:', err);
  process.exit(1);
});
