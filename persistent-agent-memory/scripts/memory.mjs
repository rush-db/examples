// Shared setup: one RushDBAgentMemory client against a standalone engine, a
// stand-in embedder, and the scope of the two made-up users.
import RushDB from '@rushdb/javascript-sdk'
import { RushDBAgentMemory, hashScope } from '@rushdb/agent-memory-contract'

export const engineUrl = process.env.RUSHDB_URL ?? 'http://127.0.0.1:3123'
export const engineToken = process.env.RUSHDB_TOKEN ?? 'local-token'

// A stand-in for a real embedding model, so the example runs offline and
// prints the same scores every time: each word is hashed into one of 256
// buckets. Swap in your provider (OpenAI, Voyage, a local model) for real use.
const DIM = 256
const bucket = (word) => {
  let h = 2166136261
  for (const c of word) h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  return (h >>> 0) % DIM
}
const STOP = new Set(['the', 'a', 'an', 'for', 'this', 'to', 'of', 'and', 'is', 'in', 'on', 'i', 'we', 'will', 'does', 'which', 'what', 'user', 'use'])
export const embedder = {
  dimensions: DIM,
  embed: async (texts) =>
    texts.map((text) => {
      const v = new Array(DIM).fill(0)
      for (const w of text.toLowerCase().match(/[a-z0-9]+/g) ?? []) if (!STOP.has(w)) v[bucket(w)] += 1
      const n = Math.hypot(...v) || 1
      return v.map((x) => x / n)
    })
}

export const memory = new RushDBAgentMemory({ engineUrl, engineToken, embedder })
export const db = new RushDB(engineToken, { direct: true, engineUrl })

// Scope comes from trusted host metadata (the chat platform's account and user
// ids), never from model output. The salt makes the hash deployment-specific.
const salt = 'example-salt'
const scopeFor = (userId) => ({
  agentId: 'support-agent',
  profileId: 'default',
  privacyScope: 'private',
  participantScopeHash: hashScope(['slack', 'acme', userId], salt),
  sandboxEligible: false
})
export const ana = scopeFor('U-ana')
export const ben = scopeFor('U-ben')

export const show = (memories) =>
  memories.length
    ? memories.map((m) => `  ${m.label.padEnd(11)} ${m.score.toFixed(3)}  ${m.text}`).join('\n')
    : '  (nothing recalled)'
