// node-postgres 8 against RushDB's pgwire. Run: npm install pg@8 && node node_pg_probe.mjs
import pg from 'pg'
const c = new pg.Client({ host: '127.0.0.1', port: Number(process.env.PGPORT ?? 5432), user: 'rushdb', database: 'rushdb',
  password: process.env.RUSHDB_TOKEN ?? 'local-token' })
await c.connect()
const r = await c.query('SELECT code, tier FROM supplier WHERE region = $1 ORDER BY code', ['flood-zone-07'])
console.log('select:', JSON.stringify(r.rows), '(INT8 arrives as a string)')
const i = await c.query('INSERT INTO supplier (code, name, tier) VALUES ($1, $2, $3)', ['S-403', 'Sedge Metals (example)', 4])
console.log('insert:', i.command, 'rowCount', i.rowCount)
const d = await c.query('DELETE FROM supplier WHERE code = $1', ['S-403'])
console.log('delete:', d.command, 'rowCount', d.rowCount)
try { await c.query('BEGIN') } catch (e) { console.log('BEGIN:', e.code, e.message) }
await c.end()
