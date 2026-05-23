// Core types for the knowledge graph chatbot

export interface User {
  id?: string;
  name: string;
  email: string;
  tier: 'standard' | 'premium';
  joinDate: string;
}

export interface Product {
  id?: string;
  name: string;
  category: string;
  price: number;
  features: string[];
  description: string;
}

export interface Topic {
  id?: string;
  name: string;
  keywords: string[];
}

export interface Message {
  id?: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
  intent?: string;
}

export interface Session {
  id?: string;
  userId: string;
  createdAt: number;
  status: 'active' | 'closed';
}

export interface PurchaseHistory {
  id?: string;
  userId: string;
  productId: string;
  purchasedAt: number;
  rating?: number;
}

// RushDB Record types
export interface RushDBRecord {
  __id: string;
  __label: string;
  [key: string]: unknown;
}

// Chatbot context
export interface ChatContext {
  currentSession?: Session;
  currentProduct?: Product;
  recentMessages: Message[];
  userPurchaseHistory: Product[];
  detectedIntent?: string;
}

// Query result types
export interface SemanticSearchResult {
  record: RushDBRecord;
  score: number;
}

export interface ContextQueryResult {
  similarMessages: SemanticSearchResult[];
  userHistory: User | null;
  purchaseHistory: Product[];
  relatedProducts: Product[];
}
