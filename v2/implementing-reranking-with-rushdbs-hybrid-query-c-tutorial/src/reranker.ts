/**
 * Reranking logic and scoring functions
 * 
 * This module implements a multi-signal reranking system that combines:
 * - Semantic similarity (from vector search)
 * - Recency/time decay
 * - Popularity/engagement metrics
 */

import type {
  ArticleRecord,
  RerankingWeights,
  SignalScores,
  ScoredResult,
  SearchFilters
} from './types';
import { DEFAULT_WEIGHTS, RECENCY_CONFIG } from './types';

/**
 * Calculate time decay score based on publish date
 * Uses exponential decay: score = 0.5^(daysSincePublish / halfLife)
 * 
 * @param publishedAt - ISO date string of publication
 * @returns Score between 0 and 1 (1 = most recent)
 */
export function calculateRecencyScore(publishedAt: string): number {
  const publishDate = new Date(publishedAt);
  const now = new Date();
  const daysSincePublish = Math.floor(
    (now.getTime() - publishDate.getTime()) / (1000 * 60 * 60 * 24)
  );

  // If older than max age, return 0
  if (daysSincePublish >= RECENCY_CONFIG.maxAgeDays) {
    return 0;
  }

  // Exponential decay with half-life
  const decayFactor = daysSincePublish / RECENCY_CONFIG.halfLifeDays;
  return Math.pow(0.5, decayFactor);
}

/**
 * Calculate popularity score based on views and likes
 * Normalizes to 0-1 range using a logarithmic scale
 * 
 * @param views - Number of article views
 * @param likes - Number of article likes
 * @returns Score between 0 and 1
 */
export function calculatePopularityScore(views: number, likes: number): number {
  // Log scale to dampen extreme values
  const logViews = Math.log10(Math.max(views, 1) + 1);
  const logLikes = Math.log10(Math.max(likes, 1) + 1);
  
  // Weighted combination (views matter more than likes)
  const rawScore = (logViews * 0.7) + (logLikes * 0.3);
  
  // Normalize assuming max ~6 log10 views = 1,000,000 views
  const maxLogViews = 6;
  return Math.min(rawScore / maxLogViews, 1);
}

/**
 * Calculate all signal scores for an article
 * 
 * @param record - The article record
 * @param semanticScore - Similarity score from vector search (0-1)
 * @returns Object containing all individual signal scores
 */
export function calculateAllSignals(
  record: ArticleRecord,
  semanticScore: number
): SignalScores {
  return {
    semantic: semanticScore,
    recency: calculateRecencyScore(record.publishedAt),
    popularity: calculatePopularityScore(record.views, record.likes)
  };
}

/**
 * Calculate final score by combining all signals with weights
 * 
 * @param signals - Individual signal scores
 * @param weights - Weights for each signal
 * @returns Combined final score (0-1)
 */
export function calculateFinalScore(
  signals: SignalScores,
  weights: RerankingWeights = DEFAULT_WEIGHTS
): number {
  const { semantic, recency, popularity } = signals;
  const { semantic: wSem, recency: wRec, popularity: wPop } = weights;

  // Validate weights sum to 1
  const weightSum = wSem + wRec + wPop;
  if (Math.abs(weightSum - 1) > 0.001) {
    throw new Error(`Weights must sum to 1, got ${weightSum}`);
  }

  return (wSem * semantic) + (wRec * recency) + (wPop * popularity);
}

/**
 * Apply structured filters to search results
 * 
 * @param results - Raw search results from vector search
 * @param filters - Filter criteria
 * @returns Filtered results
 */
export function applyFilters(
  results: ArticleRecord[],
  filters: SearchFilters
): ArticleRecord[] {
  return results.filter(record => {
    // Category filter
    if (filters.category && record.category !== filters.category) {
      return false;
    }

    // Tags filter - must have ALL specified tags
    if (filters.tags && filters.tags.length > 0) {
      const hasAllTags = filters.tags.every(tag => 
        record.tags.includes(tag)
      );
      if (!hasAllTags) return false;
    }

    // Author filter
    if (filters.author && record.author !== filters.author) {
      return false;
    }

    // Date range filter
    if (filters.dateFrom) {
      const publishDate = new Date(record.publishedAt);
      const fromDate = new Date(filters.dateFrom);
      if (publishDate < fromDate) return false;
    }

    if (filters.dateTo) {
      const publishDate = new Date(record.publishedAt);
      const toDate = new Date(filters.dateTo);
      if (publishDate > toDate) return false;
    }

    // Minimum views filter
    if (filters.minViews !== undefined && record.views < filters.minViews) {
      return false;
    }

    return true;
  });
}

/**
 * Rerank results using weighted signal combination
 * 
 * @param results - Results with semantic scores (from vector search)
 * @param weights - Weights for each signal (optional)
 * @returns Reranked results with all scoring information
 */
export function rerankResults(
  results: Array<{ record: ArticleRecord; score: number }>,
  weights: RerankingWeights = DEFAULT_WEIGHTS
): ScoredResult[] {
  // Calculate scores for each result
  const scoredResults: ScoredResult[] = results.map(({ record, score }) => {
    const signals = calculateAllSignals(record, score);
    const finalScore = calculateFinalScore(signals, weights);

    return {
      record,
      signals,
      finalScore,
      rank: 0 // Will be set after sorting
    };
  });

  // Sort by final score descending
  scoredResults.sort((a, b) => b.finalScore - a.finalScore);

  // Assign ranks
  scoredResults.forEach((result, index) => {
    result.rank = index + 1;
  });

  return scoredResults;
}

/**
 * Format score breakdown for display
 * 
 * @param result - A scored result
 * @returns Formatted string with score details
 */
export function formatScoreBreakdown(result: ScoredResult): string {
  const { record, signals, finalScore } = result;
  
  return [
    `┌─────────────────────────────────────────────────────────────┐`,
    `│ ${record.title.substring(0, 58).padEnd(58)} │`,
    `│   Semantic: ${signals.semantic.toFixed(3).padStart(6)} | Recency: ${signals.recency.toFixed(3).padStart(6)} | Popularity: ${signals.popularity.toFixed(3).padStart(6)} │`,
    `│   Final: ${finalScore.toFixed(3).padStart(6)}                                     │`,
    `└─────────────────────────────────────────────────────────────┘`
  ].join('\n');
}

/**
 * Compare initial vs reranked rankings
 * Useful for understanding how reranking affects results
 * 
 * @param initialResults - Results before reranking (ordered by semantic score)
 * @param rerankedResults - Results after reranking
 * @returns Comparison showing position changes
 */
export function compareRankings(
  initialResults: ArticleRecord[],
  rerankedResults: ScoredResult[]
): Array<{ record: ArticleRecord; initialRank: number; newRank: number; change: number }> {
  return rerankedResults.map(result => {
    const initialRank = initialResults.findIndex(r => r.id === result.record.id) + 1;
    const newRank = result.rank;
    
    return {
      record: result.record,
      initialRank,
      newRank,
      change: initialRank - newRank // Positive = moved up
    };
  });
}
