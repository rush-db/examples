/**
 * TypeScript types for the graph-traced reflection agent.
 *
 * Each reasoning step is a first-class graph node (RushDB label).
 * Edges between nodes encode the causal/relational structure of the trace.
 */

// -------------------------------------------------------------------------
// Core trace node types
// -------------------------------------------------------------------------

export interface InputRecord {
  id: string;
  label: 'INPUT';
  data: {
    title: string;
    docType: 'invoice' | 'support_ticket' | 'technical_doc';
    content: string;
  };
}

export interface ObservationRecord {
  id: string;
  label: 'OBSERVATION';
  data: {
    inputId: string;
    parseTree: Record<string, unknown>;
    rawLength: number;
    keyFields: string[];
  };
}

export interface ThoughtRecord {
  id: string;
  label: 'THOUGHT';
  data: {
    observationId: string;
    content: string;
    confidence: number; // 0–1
    generationStrategy: string;
  };
}

export type FailureMode = 'incomplete' | 'incorrect' | 'hallucinated' | 'off_topic';

export interface CritiqueRecord {
  id: string;
  label: 'CRITIQUE';
  data: {
    thoughtId: string;
    failureMode: FailureMode;
    description: string;
    fixSuggestion: string;
  };
}

export interface RevisionRecord {
  id: string;
  label: 'REVISION';
  data: {
    addressesCritiqueId: string;
    originalThoughtId: string;
    patchDescription: string;
    revisedContent: string;
    failureMode: FailureMode;
  };
}

export interface VerificationRecord {
  id: string;
  label: 'VERIFICATION';
  data: {
    revisionId: string;
    checks: VerificationCheck[];
    passed: boolean;
    reason: string;
  };
}

export interface VerificationCheck {
  name: string;
  passed: boolean;
  detail: string;
}

// -------------------------------------------------------------------------
// Full reasoning trace assembled from the graph
// -------------------------------------------------------------------------

export interface ReasoningTrace {
  input: InputRecord;
  observation: ObservationRecord;
  thoughts: ThoughtRecord[];
  critiques: CritiqueRecord[];
  revisions: RevisionRecord[];
  verifications: VerificationRecord[];
  finalOutput: string;
  cycles: number; // how many think → critique → revise loops were needed
}

// -------------------------------------------------------------------------
// Agent configuration
// -------------------------------------------------------------------------

export interface ReflectionAgentConfig {
  maxCycles: number;        // max think/critique/revise loops before giving up
  confidenceThreshold: number; // min confidence to skip revision
}

export const DEFAULT_CONFIG: ReflectionAgentConfig = {
  maxCycles: 5,
  confidenceThreshold: 0.85,
};
