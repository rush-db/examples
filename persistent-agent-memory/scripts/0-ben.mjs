// A second user of the same agent, so scope filtering has something to exclude.
import { createEpisodeEvent } from '@rushdb/agent-memory-contract'
import { memory, ben } from './memory.mjs'

await memory.persistEpisode(createEpisodeEvent({
  ...ben, runtime: 'custom', externalSessionId: 'ben-1', sourceEventId: 'turn-1', turnIndex: 1,
  userText: 'The billing service language for my team is Rust.', assistantText: 'Rust it is for your team.',
  summary: 'Ben wants his team\'s billing service language to be Rust.', conversationKind: 'direct',
  visibility: 'participant', trustClass: 'mixed', originClass: 'conversation',
  observedAt: '2026-10-02T11:00:00Z', provenance: 'custom:completed_turn'
}))
console.log('  wrote 1 episode for Ben')
