// Ana changes her mind. A new fact supersedes the old one; the old one has to be
// deactivated by whoever writes the replacement (the contract leaves that to the adapter).
import { createFactEvent } from '@rushdb/agent-memory-contract'
import { memory, db, ana, show } from './memory.mjs'

const old = (await db.records.find({ labels: ['MEMORY_FACT'], where: { ...ana, subjectKey: 'billing.language', active: true } })).data[0]
const replacement = createFactEvent({
  ...ana, runtime: 'custom', text: 'Billing service language: Go', kind: 'preference',
  subjectKey: 'billing.language', confidence: 0.9, active: true, sourceEventId: 'session-2:turn-1',
  supersedesFactId: old.data.factId, validFrom: '2026-10-20T14:00:00Z',
  visibility: 'participant', trustClass: 'trusted', provenance: 'custom:explicit_write'
})
await memory.persistFact(replacement)

const query = 'billing service language'
const facts = async () => (await memory.recall({ ...ana, query, limit: 5 })).filter((m) => m.label === 'MEMORY_FACT')
console.log('  Step 1, replacement written, old fact still active: recall returns both')
console.log(show(await facts()))

await db.records.update({ target: old.data.__id, label: 'MEMORY_FACT', data: { active: false, validUntil: replacement.validFrom } })
console.log('\n  Step 2, old fact set active=false: recall returns the current one only')
console.log(show(await facts()))

console.log('\n  History is still there for audit (all facts on the subject, oldest first):')
const history = await db.records.find({ labels: ['MEMORY_FACT'], where: { ...ana, subjectKey: 'billing.language' }, orderBy: { validFrom: 'asc' } })
for (const r of history.data)
  console.log(`  ${r.data.validFrom}  active=${String(r.data.active).padEnd(5)} ${r.data.text}${r.data.supersedesFactId ? '  (supersedes ' + r.data.supersedesFactId.slice(0, 8) + '…)' : ''}`)
