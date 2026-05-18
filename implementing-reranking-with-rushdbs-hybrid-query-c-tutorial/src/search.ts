/**
 * Hybrid search implementation
 * 
 * Combines RushDB's vector search with structured filtering and reranking
 */

import RushDB from '@rushdb/javascript-sdk';
import type {
  ArticleRecord,
  HybridSearchOptions,
  HybridSearchResult,
  RerankingWeights,
  ScoredResult
} from './types';
import { DEFAULT_WEIGHTS } from './types';
import {
  applyFilters,
  rerankResults,
  formatScoreBreakdown,
  compareRankings
} from './reranker';

/**
 * HybridSearcher class
 * 
 * Provides methods for performing hybrid search with reranking
 * using RushDB's vector search capabilities.
 */
export class HybridSearcher {
  private db: RushDB;
  private indexId: string | null = null;

  constructor(apiKey: string, url?: string) {
    this.db = new RushDB(apiKey, url ? { url } : undefined);
  }

  /**
   * Find or create the vector index for articles
   */
  async ensureIndex(): Promise<string> {
    if (this.indexId) return this.indexId;

    // Try to find existing index
    const indexes = await this.db.ai.indexes.find();
    const articleIndex = indexes.data.find(
      idx => idx.label === 'ARTICLE' && idx.propertyName === 'body'
    );

    if (articleIndex) {
      this.indexId = articleIndex.id;
      return this.indexId;
    }

    // Create new index
    const created = await this.db.ai.indexes.create({
      label: 'ARTICLE',
      propertyName: 'body',
      sourceType: 'external',
      dimensions: 384, // all-MiniLM-L6-v2 produces 384-dim vectors
      similarityFunction: 'cosine'
    });

    this.indexId = created.data.__id;
    return this.indexId;
  }

  /**
   * Perform hybrid search with reranking
   * 
   * @param options - Search configuration
   * @returns Complete search results with scoring
   */
  async search(options: HybridSearchOptions): Promise<HybridSearchResult> {
    const {
      query,
      limit = 20,
      filters = {},
      weights = DEFAULT_WEIGHTS,
      showScores = false
    } = options;

    console.log(`\n=== RushDB Hybrid Search with Reranking Demo ===\n`);
    console.log(`Query: "${query}"`);
    if (Object.keys(filters).length > 0) {
      console.log(`Filters: ${JSON.stringify(filters)}`);
    }
    console.log(`Weights: semantic=${weights.semantic}, recency=${weights.recency}, popularity=${weights.popularity}\n`);

    // Stage 1: Semantic vector search
    console.log('--- Stage 1: Initial Semantic Search ---');
    
    let searchResults: Array<{ record: ArticleRecord; score: number }> = [];
    
    try {
      const results = await this.db.ai.search({
        propertyName: 'body',
        query: query,
        labels: ['ARTICLE'],
        limit: limit * 2 // Fetch more than needed to allow for filtering
      });

      searchResults = results.data.map(record => ({
        record: record as unknown as ArticleRecord,
        score: record.score ?? 0
      }));

      console.log(`Found ${searchResults.length} initial candidates\n`);

      // Display initial top results
      searchResults.slice(0, 5).forEach(({ record, score }, i) => {
        console.log(`  [${score.toFixed(3)}] ${record.title.substring(0, 50)}...`);
      });

    } catch (error) {
      console.error('Vector search failed:', error);
      console.log('\nFalling back to structured search...\n');

      // Fallback: Use structured search if vector search fails
      const structuredResults = await this.db.records.find({
        labels: ['ARTICLE'],
        where: filters,
        limit: limit
      });

      searchResults = structuredResults.data.map(record => ({
        record: record as unknown as ArticleRecord,
        score: 0.5 // Default score for non-vector results
      }));
    }

    if (searchResults.length === 0) {
      console.log('No results found. Try running the seed script first:\n');
      console.log('  npm run seed\n');
      return {
        query,
        initialResults: [],
        rerankedResults: [],
        totalCandidates: 0,
        filtersApplied: filters
      };
    }

    // Stage 2: Apply structured filters
    console.log('\n--- Stage 2: Applying Structured Filters ---');
    const hasFilters = Object.keys(filters).some(k => filters[k as keyof typeof filters] !== undefined);
    
    let filteredResults = searchResults;
    if (hasFilters) {
      filteredResults = searchResults
        .map(({ record, score }) => ({ record, score }))
        .filter(({ record }) => {
          if (filters.category && record.category !== filters.category) return false;
          if (filters.tags && filters.tags.length > 0) {
            if (!filters.tags.every(tag => record.tags.includes(tag))) return false;
          }
          if (filters.author && record.author !== filters.author) return false;
          if (filters.minViews && record.views < filters.minViews) return false;
          return true;
        });
      
      console.log(`Filtered from ${searchResults.length} to ${filteredResults.length} candidates`);
    } else {
      console.log('No filters applied');
    }

    // Stage 3: Rerank by structured criteria
    console.log('\n--- Stage 3: Reranking by Multiple Signals ---');
    const rerankedResults = rerankResults(filteredResults, weights);

    // Take top N results
    const topResults = rerankedResults.slice(0, limit);

    console.log('\n--- Final Reranked Results ---');
    topResults.forEach(result => {
      const movement = result.rank <= 5 ? '' : ` (was #${result.rank})`;
      console.log(
        `  #${result.rank.toString().padStart(2)} [${result.finalScore.toFixed(3)}] ${result.record.title.substring(0, 45)}${movement}`
      );
    });

    // Show score breakdown if requested
    if (showScores && topResults.length > 0) {
      console.log('\n--- Score Breakdown (Top 3) ---');
      topResults.slice(0, 3).forEach(result => {
        console.log(formatScoreBreakdown(result));
      });
    }

    // Show ranking changes if we have both initial and final rankings
    if (filteredResults.length > 1) {
      console.log('\n--- Position Changes (moved up = positive) ---');
      const initialOrdered = filteredResults
        .map(({ record, score }) => record)
        .sort((a, b) => {
          const scoreA = searchResults.find(r => r.record.id === a.id)?.score ?? 0;
          const scoreB = searchResults.find(r => r.record.id === b.id)?.score ?? 0;
          return scoreB - scoreA;
        });

      const comparison = compareRankings(initialOrdered, topResults);
      
      comparison.slice(0, 5).forEach(({ record, initialRank, newRank, change }) => {
        const changeStr = change > 0 ? `+${change}` : change.toString();
        console.log(
          `  #${newRank.toString().padStart(2)} "${record.title.substring(0, 35)}..." | was #${initialRank} | ${changeStr > 0 ? '+' + changeStr : changeStr}`
        );
      });
    }

    console.log('\n' + '='.repeat(66));

    return {
      query,
      initialResults: searchResults.map(r => r.record),
      rerankedResults: topResults,
      totalCandidates: filteredResults.length,
      filtersApplied: filters
    };
  }

  /**
   * Get database instance for direct operations
   */
  getDb(): RushDB {
    return this.db;
  }
}

/**
 * Factory function to create a configured hybrid searcher
 */
export function createHybridSearcher(): HybridSearcher {
  const apiKey = process.env.RUSHDB_API_KEY;
  if (!apiKey) {
    throw new Error('RUSHDB_API_KEY environment variable is required');
  }

  return new HybridSearcher(apiKey, process.env.RUSHDB_URL);
}
