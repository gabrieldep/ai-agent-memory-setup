# /memory-save

Snapshot the current session into persistent memory.

## Instructions

1. Internally summarize the session: files modified, decisions made, open questions, next steps.

2. Derive a slug for the log: kebab-case, ≤ 6 words, descriptive (e.g. `auth-refactor-supabase`, `rate-limit-investigation`).

3. Write the markdown body for the log with these four required sections:

   ```markdown
   ## What was done
   - <bullet with wikilinks to modified notes / files>

   ## Decisions
   - <one sentence per decision>

   ## Open questions
   - <unanswered questions>

   ## Next session
   - <suggested first action>
   ```

4. Save the body to `/tmp/memory-save-body.md` then shell out to the writer:

   ```bash
   ~/.copilot-memory/bin/memory-save \
       --slug "<slug>" \
       --project "<project-slug>" \
       --source cursor \
       --body-file /tmp/memory-save-body.md
   ```

   The script handles frontmatter, file placement under `$VAULT/logs/`, verification, and (if in a git repo) `git commit -m "session: <slug>"`. It does NOT push.

5. Confirm the verification passed (script exits 0 on success).

## Reference

Full behavior contract: see `spec/commands/memory-save.md` in the copilot-memory-setup repo.
