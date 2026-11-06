// Session 2 (a new process, after the engine restarted): nothing is held in
// memory by this client, so everything recalled comes from the engine's disk.
import { formatRecalledMemories } from '@rushdb/agent-memory-contract'
import { memory, ana, ben, show } from './memory.mjs'

const query = 'Which language should the billing service use?'
console.log(`  Ana asks: "${query}"`)
const recalled = await memory.recall({ ...ana, query, excludeSessionId: 'session-2', limit: 3 })
console.log(show(recalled))

console.log('\n  The same question in Ben\'s scope (same agent, different participant hash):')
console.log(show(await memory.recall({ ...ben, query, limit: 3 })))

console.log('\n  What the agent gets in its prompt (formatRecalledMemories):')
console.log(formatRecalledMemories(recalled.slice(0, 2)).replace(/^/gm, '  | '))
