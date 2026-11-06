// Prints getSchemaMarkdown for a self-hosted engine, through the JavaScript SDK in direct mode
// (the same Markdown the RushDB MCP tool getSchemaMarkdown returns).
// Usage: node schema-markdown.mjs [label...]   (RUSHDB_URL, RUSHDB_TOKEN from env)
import RushDB from '@rushdb/javascript-sdk'

const db = new RushDB(process.env.RUSHDB_TOKEN ?? 'local-token', {
  direct: true,
  engineUrl: process.env.RUSHDB_URL ?? 'http://127.0.0.1:3000'
})
const labels = process.argv.slice(2)
const result = await db.ai.getSchemaMarkdown(labels.length ? { labels } : {})
process.stdout.write(String(result.data) + '\n')
