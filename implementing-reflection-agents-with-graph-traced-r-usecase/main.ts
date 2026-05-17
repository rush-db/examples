/**
 * main.ts — Entry point for the graph-traced reflection agent example.
 *
 * Loads INPUT records from RushDB (created by seed.ts) and runs the
 * ReflectionAgent on each one. Prints the reasoning trace summary.
 */

import * as dotenv from 'dotenv';
import { RushDB } from '@rushdb/javascript-sdk';
import { ReflectionAgent } from './agent';

dotenv.config();

const API_KEY = process.env.RUSHDB_API_KEY;
if (!API_KEY) {
  console.error('❌ RUSHDB_API_KEY is not set in .env');
  console.error('   Copy .env.example to .env and add your API key.');
  process.exit(1);
}

async function main() {
  const db = new RushDB(API_KEY);
  const agent = new ReflectionAgent(API_KEY);

  // Load all INPUT records created by the seed script
  const { data: inputs, total } = await db.records.find({
    labels: ['INPUT'],
    limit: 20,
  });

  if (total === 0) {
    console.log('\n⚠️  No INPUT records found.');
    console.log('   Run `npm run seed` first to create test documents.\n');
    return;
  }

  console.log('\n=== Reflection Agent: Graph-Traced Reasoning ===\n');
  console.log(`Found ${total} input document(s) to process.\n`);

  for (const input of inputs) {
    const title = (input.data['title'] as string) ?? 'Untitled';
    console.log(`--- Processing: ${title} ---`);

    try {
      const trace = await agent.run(input as never);

      // Print a human-readable summary
      console.log(`  Cycles completed: ${trace.cycles}`);
      console.log(`  Critiques found: ${trace.critiques.length}`);
      console.log(`  Revisions made: ${trace.revisions.length}`);
      console.log(`  Final output: ${truncate(truncate(truncate(truncate(trace.finalOutput, 80), '\n', ' '), '  ', ' '), '\n', ' ')}`);
      console.log();

      // Persist the final output back to the INPUT record for auditability
      await db.records.update({
        recordId: input.id,
        data: {
          agentOutput: trace.finalOutput,
          traceCycles: trace.cycles,
          traceCritiques: trace.critiques.length,
          traceRevisions: trace.revisions.length,
          processedAt: new Date().toISOString(),
        },
      });
    } catch (err) {
      console.error(`  ❌ Error processing ${title}:`, err);
    }
  }

  console.log('=== All traces available in RushDB ===');
  console.log('   Query OBSERVATION, THOUGHT, CRITIQUE, REVISION, VERIFICATION labels');
  console.log('   to retrieve reasoning chains for any input.\n');
}

/** Truncate a string to maxLen characters. */
function truncate(s: string, maxLen: number): string {
  return s.length > maxLen ? s.slice(0, maxLen) + '...' : s;
}

/** Flatten a string by replacing a character with another throughout. */
function flatten(s: string, from: string, to: string): string {
  return s.split(from).join(to);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
