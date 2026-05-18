/**
 * Main demonstration script
 * 
 * Shows how to implement reranking with RushDB's hybrid query capabilities.
 * Run with: npm start
 * Or: npx ts-node src/main.ts --query "machine learning" --show-scores
 */

import * as dotenv from 'dotenv';
import { HybridSearcher, createHybridSearcher } from './search';
import type { RerankingWeights, SearchFilters } from './types';
import { DEFAULT_WEIGHTS } from './types';

// Load environment variables
dotenv.config();

/**
 * Parse command line arguments
 */
function parseArgs(): {
  query: string;
  category?: string;
  tags?: string[];
  author?: string;
  limit: number;
  weights?: RerankingWeights;
  showScores: boolean;
} {
  const args = process.argv.slice(2);
  
  const result = {
    query: 'machine learning',
    limit: 10,
    showScores: false
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--query':
      case '-q':
        result.query = args[++i];
        break;
      case '--category':
      case '-c':
        result.category = args[++i];
        break;
      case '--tags':
        result.tags = args[++i].split(',').map(t => t.trim());
        break;
      case '--author':
        result.author = args[++i];
        break;
      case '--limit':
      case '-l':
        result.limit = parseInt(args[++i], 10);
        break;
      case '--show-scores':
      case '-s':
        result.showScores = true;
        break;
      case '--weights':
        // Format: --weights 0.7,0.2,0.1 (semantic, recency, popularity)
        const [wSem, wRec, wPop] = args[++i].split(',').map(parseFloat);
        result.weights = { semantic: wSem, recency: wRec, popularity: wPop };
        break;
      case '--help':
      case '-h':
        printUsage();
        process.exit(0);
    }
  }

  return result;
}

/**
 * Print usage information
 */
function printUsage(): void {
  console.log(`
RushDB Hybrid Search with Reranking Demo

Usage: npx ts-node src/main.ts [options]

Options:
  --query, -q <text>        Search query (default: "machine learning")
  --category, -c <name>    Filter by category
  --tags <tag1,tag2>       Filter by tags (comma-separated)
  --author <name>          Filter by author
  --limit, -l <number>     Maximum results (default: 10)
  --weights <w1,w2,w3>     Scoring weights: semantic,recency,popularity
                           (default: 0.5,0.3,0.2)
  --show-scores, -s        Show detailed score breakdown
  --help, -h               Show this help message

Examples:
  npx ts-node src/main.ts --query "deep learning"
  npx ts-node src/main.ts -q "python" -c technology --show-scores
  npx ts-node src/main.ts -q "data science" --tags ai,ml --weights 0.6,0.3,0.1
`);
}

/**
 * Build filters from parsed arguments
 */
function buildFilters(args: ReturnType<typeof parseArgs>): SearchFilters {
  const filters: SearchFilters = {};
  
  if (args.category) filters.category = args.category;
  if (args.tags) filters.tags = args.tags;
  if (args.author) filters.author = args.author;
  
  return filters;
}

/**
 * Main execution
 */
async function main(): Promise<void> {
  console.log('\n🚀 Starting RushDB Hybrid Search with Reranking Demo\n');
  console.log('   Make sure to run `npm run seed` first if this is your first run.\n');

  // Check for API key
  if (!process.env.RUSHDB_API_KEY) {
    console.error('❌ Error: RUSHDB_API_KEY environment variable is not set');
    console.error('\nPlease create a .env file based on .env.example');
    console.error('Get your API key at: https://dash.rushdb.com\n');
    process.exit(1);
  }

  // Parse command line arguments
  const args = parseArgs();
  
  // Create searcher
  const searcher = createHybridSearcher();

  // Build filters and weights
  const filters = buildFilters(args);
  const weights = args.weights ?? DEFAULT_WEIGHTS;

  try {
    // Perform hybrid search
    const result = await searcher.search({
      query: args.query,
      limit: args.limit,
      filters,
      weights,
      showScores: args.showScores
    });

    // Summary
    console.log(`\n📊 Summary:`);
    console.log(`   Query: "${result.query}"`);
    console.log(`   Initial candidates: ${result.initialResults.length}`);
    console.log(`   After filters: ${result.totalCandidates}`);
    console.log(`   Final results: ${result.rerankedResults.length}`);

    if (result.rerankedResults.length > 0) {
      console.log(`\n🏆 Top Result:`);
      const top = result.rerankedResults[0];
      console.log(`   "${top.record.title}"`);
      console.log(`   Category: ${top.record.category} | Tags: ${top.record.tags.join(', ')}`);
      console.log(`   Published: ${top.record.publishedAt} | Views: ${top.record.views}`);
      console.log(`   Final Score: ${top.finalScore.toFixed(3)}`);
    }

  } catch (error) {
    console.error('\n❌ Search failed:', error);
    process.exit(1);
  }
}

// Run main function
main().catch(console.error);
