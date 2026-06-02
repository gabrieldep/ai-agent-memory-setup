# /memory-load

Load persistent memory at the start of this session.

## Instructions

1. Run the deterministic loader to get a structured snapshot of vault state:

   ```bash
   ~/.copilot-memory/bin/memory-load
   ```

2. Read the 3 most recent files in `$VAULT/logs/` directly with the Read tool.

3. Read `$VAULT/<current-project>/architecture/decisions.md` if it exists. Use the current working directory's basename as `<current-project>`.

4. If `graphify-out/graph.json` exists in the current working directory, read `graphify-out/GRAPH_REPORT.md`. Do NOT read the full `graph.json` — query it on demand.

5. Synthesize a session-start summary (≤ 200 words) covering:
   - Current state
   - Last 3 decisions
   - Open questions
   - Suggested next action

6. Stop and wait for the user's first real instruction. Do NOT start working yet.

## Reference

Full behavior contract: see `spec/commands/memory-load.md` in the copilot-memory-setup repo.
