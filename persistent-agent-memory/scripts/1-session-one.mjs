// Session 1 (process 1): Ana works with the agent; each completed turn becomes
// an EPISODE and one stated preference becomes a MEMORY_FACT.
import { createEpisodeEvent, createFactEvent } from '@rushdb/agent-memory-contract'
import { memory, ana } from './memory.mjs'

await memory.ensureIndexes()

const turns = [
  ['Our billing service should be TypeScript, not Go.', 'Noted: TypeScript for the billing service.',
    'Ana wants the billing service written in TypeScript, not Go.'],
  ['Deploys go out on Tuesdays only.', 'Understood, Tuesday deploys.',
    'Ana says deploys for billing happen on Tuesdays only.'],
  ['Invoices must keep 10 years of history for the auditors.', 'I will keep invoice retention at 10 years.',
    'Ana needs invoice history retained for 10 years for auditors.']
]
const episodes = turns.map(([userText, assistantText, summary], i) =>
  createEpisodeEvent({
    ...ana, runtime: 'custom', externalSessionId: 'session-1', sourceEventId: `turn-${i + 1}`, turnIndex: i + 1,
    userText, assistantText, summary, conversationKind: 'direct', visibility: 'participant', trustClass: 'mixed',
    originClass: 'conversation', observedAt: `2026-10-0${i + 1}T09:00:00Z`, provenance: 'custom:completed_turn'
  })
)
for (const e of episodes) await memory.persistEpisode(e)
// A retry after a timeout sends the same turn again: same eventId, so the upsert
// updates the one record instead of adding a second.
await memory.persistEpisode(episodes[0])

const fact = createFactEvent({
  ...ana, runtime: 'custom', text: 'Billing service language: TypeScript', kind: 'preference',
  subjectKey: 'billing.language', confidence: 0.9, active: true, sourceEventId: episodes[0].eventId,
  validFrom: '2026-10-01T09:00:00Z', visibility: 'participant', trustClass: 'trusted', provenance: 'custom:explicit_write'
})
await memory.persistFact(fact)

console.log(`  wrote ${episodes.length} episodes (+1 retry of turn 1) and 1 fact`)
console.log(`  turn-1 eventId ${episodes[0].eventId.slice(0, 16)}…  factId ${fact.factId.slice(0, 16)}…`)
