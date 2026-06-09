---
agent: agent
description: Load persistent vault memory at the start of a session
---

# /memory-load

You are starting a new session on this workspace. Load persistent context **before** doing anything else.

## Steps

1. Run the deterministic loader and read its output:

   ```bash
   ~/.copilot-memory/bin/memory-load
   ```

2. Inspect the 3 most recent files in the user's vault `logs/` directory directly (paths come from step 1's output).

3. If the current project has a `graphify-out/graph.json`, read `graphify-out/GRAPH_REPORT.md` — do NOT read the full `graph.json`.

4. Synthesize a session-start summary (≤ 200 words) covering:
   - Current state
   - Last 3 decisions
   - Open questions
   - Suggested next action

5. **Stop** and wait for the user's first real instruction. Do not start working on anything yet.
