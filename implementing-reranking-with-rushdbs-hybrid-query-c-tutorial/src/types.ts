/**
 * Type definitions for the reranking tutorial
 */

import type { Record as RushDBRecord } from '@rushdb/javascript-sdk';

/**
 * Article record structure stored in RushDB
 */
export interface ArticleRecord extends RushDBRecord {
  title: string;
  body: string;
  summary: string;
  category: string;
  tags: string[];
  author: string;
  publishedAt: string;
  views: number;
  likes: number;
  readingTimeMinutes: number;
}

/**
 * Search filter options for hybrid queries
 */
export interface SearchFilters {
  category?: string;
  tags?: string[];
  author?: string;
  dateFrom?: string;
  dateTo?: string;
  minViews?: number;
}

/**
 * Weights for the reranking scoring function
 */
export interface RerankingWeights {
  semantic: number;      // Weight for vector similarity score
  recency: number;        // Weight for time decay score
  popularity: number;    // Weight for engagement score
}

/**
 * Individual signal scores for a result
 */
export interface SignalScores {
  semantic: number;
  recency: number;
  popularity: number;
}

/**
 * A search result with all scoring information
 */
export interface ScoredResult {
  record: ArticleRecord;
  signals: SignalScores;
  finalScore: number;
  rank: number;
}

/**
 * Search options for the hybrid search
 */
export interface HybridSearchOptions {
  query: string;
  limit?: number;
  filters?: SearchFilters;
  weights?: RerankingWeights;
  showScores?: boolean;
}

/**
 * Result of a hybrid search operation
 */
export interface HybridSearchResult {
  query: string;
  initialResults: ArticleRecord[];
  rerankedResults: ScoredResult[];
  totalCandidates: number;
  filtersApplied: SearchFilters;
}

/**
 * Default reranking weights
 */
export const DEFAULT_WEIGHTS: RerankingWeights = {
  semantic: 0.5,
  recency: 0.3,
  popularity: 0.2
};

/**
 * Time decay parameters for recency scoring
 */
export const RECENCY_CONFIG = {
  // Half-life in days - after this many days, recency score is 0.5
  halfLifeDays: 90,
  // Maximum age in days to consider (older = 0 score)
  maxAgeDays: 365
};

/**
 * Category definitions for the sample data
 */
export const CATEGORIES = [
  'technology',
  'research',
  'tutorials',
  'opinion',
  'news'
] as const;

/**
 * Available tags for articles
 */
export const TAGS = [
  'ai', 'ml', 'python', 'javascript', 'data-science',
  'deep-learning', 'nlp', 'computer-vision', 'devops',
  'cloud', 'database', 'api', 'security', 'performance'
] as const;

/**
 * Author names for sample data
 */
export const AUTHORS = [
  'Elena Rodriguez', 'Marcus Chen', 'Priya Sharma',
  'James Wilson', 'Sofia Andersson', 'Raj Patel',
  'Emma Thompson', 'Lucas Garcia', 'Yuki Tanaka', 'Anna Kowalski'
] as const;
