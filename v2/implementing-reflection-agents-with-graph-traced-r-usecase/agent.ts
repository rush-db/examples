/**
 * ReflectionAgent — implements graph-traced reasoning.
 *
 * Each step of the reasoning cycle is stored as a typed RushDB record with
 * typed edges connecting them. The graph is both the agent's memory and its
 * audit trail.
 *
 * The LLM calls are simulated with deterministic pattern-matching so the
 * example is runnable without an API key. Replace `_simulateLLM*` methods
 * with real API calls to use this in production.
 */

import RushDB from '@rushdb/javascript-sdk';
import {
  InputRecord,
  ObservationRecord,
  ThoughtRecord,
  CritiqueRecord,
  RevisionRecord,
  VerificationRecord,
  ReasoningTrace,
  FailureMode,
  VerificationCheck,
  ReflectionAgentConfig,
  DEFAULT_CONFIG,
} from './types';

type RushDBRecord = {
  id: string;
  label: string;
  data: Record<string, unknown>;
};

export class ReflectionAgent {
  private db: RushDB;
  private config: ReflectionAgentConfig;

  constructor(apiKey: string, config: ReflectionAgentConfig = DEFAULT_CONFIG) {
    this.db = new RushDB(apiKey);
    this.config = config;
  }

  /**
   * Run the full reflection cycle on an INPUT record.
   * Returns a complete reasoning trace for debugging and auditing.
   */
  async run(input: InputRecord): Promise<ReasoningTrace> {
    // ── Step 1: Observe ───────────────────────────────────────────────
    const observation = await this._observe(input);

    // ── Step 2: Generate initial thought ─────────────────────────────
    let currentThought = await this._think(observation);

    // ── Step 3–4: Critique / revise loop ─────────────────────────────
    const critiques: CritiqueRecord[] = [];
    const revisions: RevisionRecord[] = [];
    const verifications: VerificationRecord[] = [];
    let cycles = 0;

    while (cycles < this.config.maxCycles) {
      cycles++;

      // Critique the current thought
      const cycleCritiques = await this._critique(currentThought, input);
      critiques.push(...cycleCritiques);

      if (cycleCritiques.length === 0) {
        // No flaws found — move to verification
        const verification = await this._verify(currentThought, []);
        verifications.push(verification);

        if (verification.data.passed) {
          // Thought is good — we're done
          break;
        }
        // Verification failed even without critiques — regenerate
        currentThought = await this._think(observation, currentThought.id);
        continue;
      }

      // Address each critique with a targeted revision
      for (const critique of cycleCritiques) {
        const revision = await this._revise(currentThought, critique);
        revisions.push(revision);

        // Replace current thought with the revised version
        currentThought = await this._replaceThought(currentThought, revision);
      }

      // Verify the revised thought against all critiques seen so far
      const verification = await this._verify(currentThought, critiques);
      verifications.push(verification);

      if (verification.data.passed) {
        break;
      }
      // Verification failed — cycle continues
    }

    // ── Build and return the full trace ──────────────────────────────
    return {
      input,
      observation,
      thoughts: [currentThought],
      critiques,
      revisions,
      verifications,
      finalOutput: currentThought.data.content as string,
      cycles,
    };
  }

  // =========================================================================
  // Private methods — each maps to a reasoning step + graph write
  // =========================================================================

  /** Step 1: Parse the input and store the parse tree as an OBSERVATION. */
  private async _observe(input: InputRecord): Promise<ObservationRecord> {
    // Simulate LLM parsing the input document
    const parsed = this._simulateLLMObserve(input);

    // Store as a typed graph record
    const record = await this.db.records.create({
      label: 'OBSERVATION',
      data: {
        inputId: input.id,
        docType: input.data.docType,
        parseTree: parsed.parseTree,
        keyFields: parsed.keyFields,
        rawLength: input.data.content.length,
        timestamp: new Date().toISOString(),
      },
    });

    // Link observation back to its source input
    await this.db.records.attach({
      source: record as unknown as RushDBRecord,
      target: { id: input.id, label: 'INPUT' } as unknown as RushDBRecord,
      options: { type: 'OBSERVED', direction: 'in' },
    });

    console.log(
      `  Step 1/5: OBSERVED → stored as RECORD (id: ${record.id.slice(0, 8)}...)`
    );

    return record as unknown as ObservationRecord;
  }

  /** Step 2: Generate a response from the observation. */
  private async _think(
    observation: ObservationRecord,
    priorThoughtId?: string
  ): Promise<ThoughtRecord> {
    const simulated = this._simulateLLMThink(observation, priorThoughtId);

    const record = await this.db.records.create({
      label: 'THOUGHT',
      data: {
        observationId: observation.id,
        content: simulated.content,
        confidence: simulated.confidence,
        generationStrategy: simulated.strategy,
        isRevision: !!priorThoughtId,
        priorThoughtId: priorThoughtId ?? null,
        timestamp: new Date().toISOString(),
      },
    });

    // Link thought back to the observation that generated it
    await this.db.records.attach({
      source: observation as unknown as RushDBRecord,
      target: record as unknown as RushDBRecord,
      options: { type: 'GENERATED', direction: 'out' },
    });

    const suffix = priorThoughtId ? ' (revision)' : '';
    console.log(
      `  Step 2/5: Generated initial THOUGHT${suffix} (id: ${record.id.slice(0, 8)}...)`
    );

    return record as unknown as ThoughtRecord;
  }

  /** Step 3: Critique a thought, finding specific failure modes. */
  private async _critique(
    thought: ThoughtRecord,
    input: InputRecord
  ): Promise<CritiqueRecord[]> {
    const findings = this._simulateLLMCritique(thought, input);

    const critiques: CritiqueRecord[] = [];
    for (const finding of findings) {
      const record = await this.db.records.create({
        label: 'CRITIQUE',
        data: {
          thoughtId: thought.id,
          failureMode: finding.mode,
          description: finding.description,
          fixSuggestion: finding.fix,
          timestamp: new Date().toISOString(),
        },
      });

      // Link critique to the thought it reviews
      await this.db.records.attach({
        source: thought as unknown as RushDBRecord,
        target: record as unknown as RushDBRecord,
        options: { type: 'CRITIQUED', direction: 'out' },
      });

      critiques.push(record as unknown as CritiqueRecord);
    }

    const count = critiques.length;
    const plural = count === 1 ? 'flaw' : 'flaws';
    const iter = thought.data.isRevision ? ` (revision ${thought.data.priorThoughtId ? '2' : '?'})` : '';
    console.log(
      `  Step 3/5: CRITIQUED → found ${count} ${plural}${iter}`
    );

    return critiques;
  }

  /** Step 4: Generate a targeted revision that addresses one critique. */
  private async _revise(
    thought: ThoughtRecord,
    critique: CritiqueRecord
  ): Promise<RevisionRecord> {
    const patch = this._simulateLLMRevision(thought, critique);

    const record = await this.db.records.create({
      label: 'REVISION',
      data: {
        addressesCritiqueId: critique.id,
        originalThoughtId: thought.id,
        patchDescription: patch.description,
        revisedContent: patch.content,
        failureMode: critique.data.failureMode as FailureMode,
        timestamp: new Date().toISOString(),
      },
    });

    // The critical edges: what does this revision address, and what did it replace?
    await this.db.records.attach({
      source: record as unknown as RushDBRecord,
      target: critique as unknown as RushDBRecord,
      options: { type: 'ADDRESSES', direction: 'out' },
    });

    await this.db.records.attach({
      source: thought as unknown as RushDBRecord,
      target: record as unknown as RushDBRecord,
      options: { type: 'REVISED', direction: 'out' },
    });

    console.log(
      `  Step 4/5: REVISED thought (addresses: ${critique.data.failureMode})`
    );

    return record as unknown as RevisionRecord;
  }

  /** Step 5: Verify that the revised thought passes all checks. */
  private async _verify(
    thought: ThoughtRecord,
    allCritiques: CritiqueRecord[]
  ): Promise<VerificationRecord> {
    const checks = this._runVerificationChecks(thought, allCritiques);
    const passed = checks.every((c) => c.passed);

    const record = await this.db.records.create({
      label: 'VERIFICATION',
      data: {
        revisionId: thought.id,
        checks,
        passed,
        reason: passed
          ? 'All verification checks passed.'
          : `Failed: ${checks.filter((c) => !c.passed).map((c) => c.name).join(', ')}`,
        cycles: allCritiques.length,
        timestamp: new Date().toISOString(),
      },
    });

    // Link verification to the revision it checked
    await this.db.records.attach({
      source: record as unknown as RushDBRecord,
      target: thought as unknown as RushDBRecord,
      options: { type: 'VERIFIED', direction: 'in' },
    });

    const status = passed ? 'passed ✓' : 'failed ✗';
    console.log(
      `  Step 5/5: VERIFIED → ${status}`
    );

    return record as unknown as VerificationRecord;
  }

  /** Replace a thought with the content from a revision, keeping the same observation link. */
  private async _replaceThought(
    oldThought: ThoughtRecord,
    revision: RevisionRecord
  ): Promise<ThoughtRecord> {
    // The revised content lives in the REVISION node; we treat the REVISION
    // as the new "current" thought by propagating its content forward.
    // In a production system, you might update the THOUGHT record in place
    // or promote the REVISION to a THOUGHT label. Here we create a new THOUGHT
    // that represents the post-revision state and keep the chain auditable.
    const newThought = await this.db.records.create({
      label: 'THOUGHT',
      data: {
        observationId: oldThought.data.observationId,
        content: revision.data.revisedContent,
        confidence: 0.9, // assume revision improves confidence
        generationStrategy: `revision_of_${oldThought.id.slice(0, 8)}`,
        isRevision: true,
        priorThoughtId: oldThought.id,
        revisionId: revision.id,
        failureMode: revision.data.failureMode,
        timestamp: new Date().toISOString(),
      },
    });

    await this.db.records.attach({
      source: revision as unknown as RushDBRecord,
      target: newThought as unknown as RushDBRecord,
      options: { type: 'PRODUCED', direction: 'out' },
    });

    // Carry the OBSERVATION → THOUGHT edge from the original thought
    // (the original edge already exists; the new thought is linked via REVISION chain)

    return newThought as unknown as ThoughtRecord;
  }

  // =========================================================================
  // Simulated LLM methods — replace with real API calls in production
  // =========================================================================

  /** Simulate parsing an INPUT document. */
  private _simulateLLMObserve(input: InputRecord): {
    parseTree: Record<string, unknown>;
    keyFields: string[];
  } {
    const { docType, content } = input.data;

    switch (docType) {
      case 'invoice': {
        const amountMatch = content.match(/\$([\d,]+\.\d{2})/);
        const dateMatch = content.match(/(\d{1,2}\/\d{1,2}\/\d{4})/);
        const items = content.match(/\d+x\s+([^\n]+)/g) ?? [];
        return {
          parseTree: {
            type: 'invoice',
            totalAmount: amountMatch ? amountMatch[1] : null,
            date: dateMatch ? dateMatch[1] : null,
            lineItems: items.map((i) => i.replace(/^\d+x\s+/, '').trim()),
          },
          keyFields: ['totalAmount', 'date', 'lineItems'],
        };
      }

      case 'support_ticket': {
        const priorityMatch = content.match(/priority:\s*(\w+)/i);
        const categoryMatch = content.match(/category:\s*(\w+)/i);
        const orderMatch = content.match(/order[:\s#]+([A-Z0-9-]+)/i);
        return {
          parseTree: {
            type: 'support_ticket',
            priority: priorityMatch ? priorityMatch[1].toUpperCase() : 'MEDIUM',
            category: categoryMatch ? categoryMatch[1] : 'GENERAL',
            orderId: orderMatch ? orderMatch[1] : null,
          },
          keyFields: ['priority', 'category', 'orderId'],
        };
      }

      case 'technical_doc': {
        const actionMatch = content.match(/(deprecation|maintenance|migration|rollback)/i);
        const targetMatch = content.match(/endpoint[:\s]+([^\n]+)/i);
        const dateMatch = content.match(/(\d{4}-\d{2}-\d{2})/);
        return {
          parseTree: {
            type: 'technical_doc',
            action: actionMatch ? actionMatch[1] : null,
            affectedEndpoint: targetMatch ? targetMatch[1].trim() : null,
            targetDate: dateMatch ? dateMatch[1] : null,
          },
          keyFields: ['action', 'affectedEndpoint', 'targetDate'],
        };
      }

      default:
        return { parseTree: { type: docType }, keyFields: [] };
    }
  }

  /** Simulate generating an initial response from an observation. */
  private _simulateLLMThink(
    observation: ObservationRecord,
    priorThoughtId?: string
  ): { content: string; confidence: number; strategy: string } {
    const parseTree = observation.data.parseTree as Record<string, unknown>;
    const docType = observation.data.docType as string;

    if (priorThoughtId) {
      // This is a regenerated thought — start from scratch (simulating a
      // non-graph-traced baseline for comparison)
      return {
        content: this._getBaseResponse(docType, parseTree),
        confidence: 0.75,
        strategy: 'regeneration_from_observation',
      };
    }

    // Initial thought — intentionally introduce a known flaw so the
    // critique/revise loop has something to do
    return {
      content: this._getInitialThoughtWithFlaw(docType, parseTree),
      confidence: 0.6, // low because the thought is intentionally flawed
      strategy: 'first_pass_from_observation',
    };
  }

  /** Simulate critiquing a thought for specific failure modes. */
  private _simulateLLMCritique(
    thought: ThoughtRecord,
    input: InputRecord
  ): Array<{ mode: FailureMode; description: string; fix: string }> {
    const content = thought.data.content as string;
    const docType = input.data.docType;
    const findings: Array<{ mode: FailureMode; description: string; fix: string }> = [];

    // Detect hallucination: thought claims something not supported by the input
    if (docType === 'support_ticket') {
      if (content.includes('refund amount: $50') && !input.data.content.includes('$50')) {
        findings.push({
          mode: 'hallucinated',
          description:
            'The thought specifies a refund amount of $50, but no dollar value appears in the input document.',
          fix: 'Remove the specific refund amount; state that the refund amount requires verification.',
        });
      }
      if (!content.toLowerCase().includes('sentiment') && docType === 'support_ticket') {
        findings.push({
          mode: 'incomplete',
          description:
            'The thought does not include a sentiment analysis of the customer\'s tone (angry, frustrated, neutral).',
          fix: 'Add a sentiment field: positive / negative / neutral, inferred from the ticket language.',
        });
      }
    }

    // Detect incomplete extraction
    if (docType === 'invoice') {
      const hasTotal = content.includes('total') || content.includes('amount');
      if (!hasTotal) {
        findings.push({
          mode: 'incomplete',
          description: 'The thought does not include the invoice total amount.',
          fix: 'Extract and state the total invoice amount from the document.',
        });
      }
    }

    // Detect off-topic generation
    if (thought.data.isRevision && (thought.data.failureMode as string) === 'off_topic') {
      findings.push({
        mode: 'off_topic',
        description: 'The revised thought addresses the wrong aspect of the input.',
        fix: 'Re-read the input and ensure the response focuses on the document type and key fields.',
      });
    }

    return findings;
  }

  /** Simulate generating a targeted revision that patches a specific flaw. */
  private _simulateLLMRevision(
    thought: ThoughtRecord,
    critique: CritiqueRecord
  ): { description: string; content: string } {
    const original = thought.data.content as string;
    const mode = critique.data.failureMode as FailureMode;

    switch (mode) {
      case 'hallucinated': {
        // Remove the hallucinated detail and add a hedge
        const cleaned = original.replace(/refund amount: \$\d+/, 'refund amount: pending verification');
        return {
          description: 'Removed hallucinated dollar amount; replaced with "pending verification".',
          content: cleaned,
        };
      }

      case 'incomplete': {
        if (original.includes('support priority')) {
          // Add sentiment analysis
          const sentimentAdded = original + '\nSentiment: negative (implied frustration from urgent escalation language).';
          return {
            description: 'Added sentiment analysis field.',
            content: sentimentAdded,
          };
        }
        if (original.includes('Invoice analysis')) {
          // Extract total from the original thought or add placeholder
          const withTotal = original.includes('total')
            ? original
            : original + '\nTotal amount: extracted from line items (see parse tree).';
          return {
            description: 'Added total amount extraction.',
            content: withTotal,
          };
        }
        return { description: 'Patched incomplete content.', content: original };
      }

      case 'incorrect':
        return {
          description: 'Corrected the incorrect assertion based on the input document.',
          content: original, // simplified; real LLM would rewrite
        };

      default:
        return {
          description: `Applied targeted fix for ${mode} failure mode.`,
          content: original,
        };
    }
  }

  // =========================================================================
  // Verification checks
  // =========================================================================

  private _runVerificationChecks(
    thought: ThoughtRecord,
    critiques: CritiqueRecord[]
  ): VerificationCheck[] {
    const checks: VerificationCheck[] = [];

    // Check 1: Content is not empty
    const content = (thought.data.content as string) ?? '';
    checks.push({
      name: 'non_empty_output',
      passed: content.trim().length > 10,
      detail: content.trim().length > 10
        ? `Output has ${content.trim().length} characters.`
        : 'Output is too short or empty.',
    });

    // Check 2: No unresolved hallucinations — content does not claim facts
    // not implied by the document type
    const hasSpecificMoney = /\$\d+/.test(content);
    const isSupportTicket = (thought.data as Record<string, unknown>).observationId !== undefined;
    checks.push({
      name: 'no_unresolved_hallucinations',
      passed: !(hasSpecificMoney && isSupportTicket),
      detail: hasSpecificMoney && isSupportTicket
        ? 'Contains specific dollar amounts which should be verified.'
        : 'No obvious hallucinated facts detected.',
    });

    // Check 3: All previous critiques have been addressed
    const unresolvedCritiques = critiques.filter((c) => {
      // Simple check: if the thought mentions the failure mode type, it's partially addressed
      return !content.includes(c.data.failureMode);
    });
    checks.push({
      name: 'critiques_addressed',
      passed: unresolvedCritiques.length === 0,
      detail:
        unresolvedCritiques.length === 0
          ? 'All critiques addressed.'
          : `${unresolvedCritiques.length} critique(s) not addressed in output.`,
    });

    // Check 4: Output is relevant to the document type
    const docType = (thought.data as Record<string, unknown>)['observationId'];
    checks.push({
      name: 'relevant_to_doc_type',
      passed: content.length > 20,
      detail: 'Output length is sufficient for the document type.',
    });

    return checks;
  }

  // =========================================================================
  // Helper: response templates
  // =========================================================================

  private _getBaseResponse(
    docType: string,
    parseTree: Record<string, unknown>
  ): string {
    switch (docType) {
      case 'invoice': {
        const total = parseTree['totalAmount'] ?? 'unknown';
        const items = parseTree['lineItems'] as string[] ?? [];
        return `Invoice analysis complete.\nTotal amount: ${total}\nLine items (${items.length}): ${items.join('; ')}`;
      }
      case 'support_ticket': {
        const priority = parseTree['priority'] ?? 'MEDIUM';
        const category = parseTree['category'] ?? 'general';
        return `Support priority: ${priority}\nCategory: ${category}\nStatus: needs review`;
      }
      case 'technical_doc': {
        const action = parseTree['action'] ?? 'unknown';
        const endpoint = parseTree['affectedEndpoint'] ?? 'unspecified';
        const date = parseTree['targetDate'] ?? 'no date specified';
        return `Technical action required: ${action}\nAffected endpoint: ${endpoint}\nTarget date: ${date}`;
      }
      default:
        return 'Analysis complete.';
    }
  }

  /** Initial thought with a deliberate flaw for demonstrating the critique loop. */
  private _getInitialThoughtWithFlaw(
    docType: string,
    parseTree: Record<string, unknown>
  ): string {
    switch (docType) {
      case 'invoice': {
        // Flaw: no total amount
        const items = parseTree['lineItems'] as string[] ?? [];
        return `Invoice document received.\nLine items identified: ${items.length}\nDate: ${parseTree['date'] ?? 'unknown'}\nItems: ${items.join('; ')}`;
      }
      case 'support_ticket': {
        // Flaws: hallucinated refund amount + missing sentiment
        const priority = parseTree['priority'] ?? 'MEDIUM';
        const category = parseTree['category'] ?? 'general';
        return `Support priority: ${priority}\nCategory: ${category}\nOrder ID: ${parseTree['orderId'] ?? 'not found'}\nRefund amount: $50\nStatus: awaiting customer response`;
      }
      case 'technical_doc': {
        // Flaw: no target date
        const action = parseTree['action'] ?? 'review required';
        const endpoint = parseTree['affectedEndpoint'] ?? 'unspecified';
        return `Technical action: ${action}\nAffected endpoint: ${endpoint}\nNo sunset date specified — check with team.`;
      }
      default:
        return 'Document processed.';
    }
  }

  // =========================================================================
  // Public: retrieve traces from the graph
  // =========================================================================

  /** Retrieve all traces for a given input record. */
  async getTraceForInput(inputId: string): Promise<ReasoningTrace | null> {
    const [observationResult, thoughtResult] = await Promise.all([
      this.db.records.find({ labels: ['OBSERVATION'], where: { inputId } }),
      this.db.records.find({ labels: ['THOUGHT'], where: { observationId: inputId } }),
    ]);

    if (observationResult.data.length === 0) return null;

    const observation = observationResult.data[0];
    const thoughts = thoughtResult.data;

    const thoughtIds = thoughts.map((t) => t.id);

    const [critiqueResult, revisionResult, verificationResult] = await Promise.all([
      this.db.records.find({
        labels: ['CRITIQUE'],
        where: { thoughtId: { $in: thoughtIds } },
      }),
      this.db.records.find({
        labels: ['REVISION'],
        where: { originalThoughtId: { $in: thoughtIds } },
      }),
      this.db.records.find({
        labels: ['VERIFICATION'],
        where: { revisionId: { $in: thoughtIds } },
      }),
    ]);

    const inputRecord = await this.db.records.findById(inputId);

    return {
      input: inputRecord as unknown as InputRecord,
      observation: observation as unknown as ObservationRecord,
      thoughts: thoughts as unknown as ThoughtRecord[],
      critiques: critiqueResult.data as unknown as CritiqueRecord[],
      revisions: revisionResult.data as unknown as RevisionRecord[],
      verifications: verificationResult.data as unknown as VerificationRecord[],
      finalOutput: thoughts[thoughts.length - 1]?.data['content'] as string ?? '',
      cycles: thoughts.filter((t) => t.data['isRevision']).length,
    };
  }
}
