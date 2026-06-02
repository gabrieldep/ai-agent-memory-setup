# /memory-load

> Load persistent memory at the start of a session. Aliases: `/resume`.

## Behavior contract

When this command is invoked, the agent MUST:

1. **Read the 3 most recent files in `$VAULT/logs/`** (sorted by filename, which encodes ISO date+time). If fewer than 3 exist, read all of them.

2. **Read `$VAULT/<current-project>/architecture/decisions.md`** if it exists, where `<current-project>` is inferred from:
   - The basename of the current working directory, OR
   - The `project` field in the most recent log's frontmatter, OR
   - Ask the user if ambiguous.

3. **Check for `graphify-out/graph.json`** in the current working directory. If present:
   - Read `graphify-out/GRAPH_REPORT.md` (god nodes, metrics) if it exists
   - Do NOT read the full graph.json — query it only when needed

4. **Read any pinned project notes** matching `$VAULT/<current-project>/*.md` that have `status: active` in their frontmatter.

5. **Synthesize a session-start summary** (≤ 200 words) covering:
   - Current state of the project
   - Last 3 decisions made
   - Open questions / pending work
   - Suggested next action

6. **Stop and wait** for the user's first real instruction. Do NOT start working on anything yet.

## Script fallback

For the deterministic path, shell out to:

```bash
~/.copilot-memory/bin/memory-load [--project <slug>] [--vault <path>]
```

The script prints the same context to stdout in a structured form the agent can consume directly. Useful for cron / non-interactive contexts and as a sanity check.

## Examples

### Good output

```
Current project: example-app (React + Supabase)

Last 3 sessions:
- 2026-06-01: shipped auth refactor (#auth-v2), 4 files modified, see [[2026-06-01-1843-auth-refactor]]
- 2026-05-30: investigated rate limit bug — root cause is Supabase RLS, see [[rate-limit-investigation]]
- 2026-05-29: planned migration to server-side sessions, see [[server-sessions-plan]]

Open questions:
- Should we keep client-side token refresh or move it to a worker?
- Migration window: blocked on staging env (see [[staging-env-blocker]])

Suggested next: continue server-sessions migration — first task is wiring the worker.
```

### Bad output (DO NOT)

- Re-reading every file in the project to "orient yourself"
- Asking the user "what would you like to work on?" without reading logs first
- Writing a 1000-word essay summarizing everything
