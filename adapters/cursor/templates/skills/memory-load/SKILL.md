# memory-load

Skill that loads persistent vault memory at the start of a session.

## When to use

Use proactively at the **start** of a session when:
- The user has just opened a new chat
- The user says "let's continue", "where were we", "resume", "what was the plan"
- The user asks a question about the current project's state, recent decisions, or open work
- You don't yet have context about what was done in previous sessions

Use ONLY at the start; do not re-invoke mid-session.

## Behavior

Follow the steps in `spec/commands/memory-load.md`:

1. Shell out to `~/.copilot-memory/bin/memory-load` for a structured snapshot
2. Read the 3 most recent files in `$VAULT/logs/`
3. Read `$VAULT/<current-project>/architecture/decisions.md` if it exists
4. If `graphify-out/graph.json` exists, read `graphify-out/GRAPH_REPORT.md`
5. Summarize state in ≤ 200 words
6. Stop and wait for the user's first real instruction

## Don't

- Don't run this skill more than once per session
- Don't read the full `graph.json` — query on demand
- Don't start implementation work after running this skill — wait for instructions
