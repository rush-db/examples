// A minimal MCP stdio client: starts @rushdb/mcp-server, sends initialize, then each [method, params]
// pair from calls.json (or argv[2]), and prints one JSON line per response.
import { spawn } from 'node:child_process'
import { readFileSync } from 'node:fs'
const calls = JSON.parse(process.argv[2] ?? readFileSync('calls.json', 'utf8'))
const server = spawn('node', ['node_modules/@rushdb/mcp-server/build/index.js'], { env: process.env, stdio: ['pipe', 'pipe', 'ignore'] })
let buffer = ''
let nextId = 0
const waiting = new Map()
server.stdout.on('data', (chunk) => {
  buffer += chunk
  for (let i; (i = buffer.indexOf('\n')) >= 0; ) {
    const line = buffer.slice(0, i)
    buffer = buffer.slice(i + 1)
    if (!line.trim()) continue
    const message = JSON.parse(line)
    waiting.get(message.id)?.(message)
    waiting.delete(message.id)
  }
})
const send = (method, params) =>
  new Promise((resolve) => {
    const id = ++nextId
    waiting.set(id, resolve)
    server.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n')
  })
const init = await send('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'probe', version: '0' } })
console.log(JSON.stringify({ method: 'initialize', result: init.result }))
server.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n')
for (const [method, params] of calls) {
  const response = await send(method, params)
  console.log(JSON.stringify({ method, tool: params?.name, arguments: params?.arguments, result: response.result ?? response.error }))
}
server.kill()
