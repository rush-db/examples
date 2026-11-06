// Ana asks to be forgotten: delete every memory carrying her participant hash.
import { db, ana, ben } from './memory.mjs'

const count = async (scope) => {
  const where = { participantScopeHash: scope.participantScopeHash }
  const [e, f] = await Promise.all(['EPISODE', 'MEMORY_FACT'].map((label) => db.records.find({ labels: [label], where, limit: 1000 })))
  const n = (k, w) => `${k} ${w}${k === 1 ? "" : "s"}`
  return `${n(e.data.length, "episode")}, ${n(f.data.length, "fact")}`
}
console.log(`  before: Ana ${await count(ana)}; Ben ${await count(ben)}`)
for (const label of ['EPISODE', 'MEMORY_FACT'])
  await db.records.delete({ labels: [label], where: { participantScopeHash: ana.participantScopeHash } })
console.log(`  after:  Ana ${await count(ana)}; Ben ${await count(ben)}`)
