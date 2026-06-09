---
agent: agent
description: Snapshot the current session into persistent vault memory
---

# /memory-save

The user is ending the session. Snapshot what happened into the persistent vault.

## Steps

1. Internally summarize: files modified, decisions made, open questions, suggested next session start.

2. Derive a kebab-case slug (≤ 6 words) for the log filename. Examples: `auth-refactor-supabase`, `rate-limit-investigation`.

3. Write the body to `/tmp/memory-save-body.md` with exactly these four sections:

   ```markdown
   ## What was done
   - <bullet list with paths>

   ## Decisions
   - <one sentence per decision>

   ## Open questions
   - <unanswered items>

   ## Next session
   - <suggested first action>
   ```

4. Run the writer (it handles frontmatter, file placement, and `git commit`):

   ```bash
   ~/.copilot-memory/bin/memory-save \
       --slug "<slug>" \
       --project "<project-slug>" \
       --source copilot \
       --body-file /tmp/memory-save-body.md
   ```

5. Verify the exit code is 0. If it failed, fix the body and retry. Do NOT push the git commit — the script will not push.
