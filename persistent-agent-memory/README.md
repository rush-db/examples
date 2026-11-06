# persistent-agent-memory

Agent memory that survives a restart, written with the published
[`@rushdb/agent-memory-contract`](https://github.com/rush-db/agent-memory-contract) package against a standalone
RushDB 3.x engine. The script starts its own engine on a fresh data directory, then:

1. **Session 1** (one Node process): three completed turns of a made-up user, Ana, become `EPISODE` records and one
   stated preference becomes a `MEMORY_FACT`. Turn 1 is sent twice, as a retry would; its deterministic `eventId`
   makes the second write an update. A second user, Ben, gets one episode.
2. **Restart:** the engine stops and starts again on the same data directory.
3. **Session 2** (a new process): recall scoped to Ana, the same question scoped to Ben, and the prompt block
   `formatRecalledMemories` produces.
4. **SQL** over the same records: episodes per session (three, not four).
5. **Supersession:** Ana changes her mind. The replacement fact alone leaves two active facts and recall returns both;
   setting the old one `active: false` fixes recall, and the history stays queryable.
6. **Forget Ana:** delete by participant hash across both labels; Ben's memory stays.

Article: [Persistent agent memory: what has to survive a session](https://rushdb.com/blog/persistent-agent-memory)

The same records are what the [OpenClaw plugin](https://docs.rushdb.com/3.x/connect/openclaw-memory)
(`@rushdb/openclaw-memory`) and the [Hermes Agent provider](https://docs.rushdb.com/3.x/connect/hermes-memory)
(`rushdb-hermes-memory`) write: all three implement AgentMemoryEvent v1.

## Prerequisites

- The `rushdb` binary (3.x) on your `PATH`, or `RUSHDB_BIN=/path/to/rushdb`. The script starts and stops it on port
  3123 (`PORT=` to change) with a data directory `.data/` here, removed at the start of each run.
- Node.js 18+ and npm (installs the two pinned packages on first run), `curl`, `jq`.

## Run

```bash
./run.sh
```

The output should match `expected-output.txt`.

## Notes

- **The embedder is a stand-in.** A standalone engine stores and searches vectors but does not create them, so the
  contract needs an `embedder`. `scripts/memory.mjs` hashes words into 256 buckets so the example runs offline and
  prints the same scores every time. Replace it with a real model (`{ dimensions, embed(texts) }`) for real use;
  scores will differ.
- **Supersession is the writer's job.** `persistFact` with `supersedesFactId` records the link but does not deactivate
  the earlier fact; step 5 shows what happens if you skip the update.
- **Readiness:** right after start the engine can answer `/health` before storage is open, so `run.sh` waits until a
  real request succeeds.
