# memory-save

Skill that snapshots the current session into persistent vault memory.

## When to use

Use proactively at the **end** of a session when:
- The user says "let's stop here", "save this", "we're done", "wrap up", "good night"
- The user is about to close the chat or switch tasks
- A meaningful chunk of work has been completed (decisions made, files modified)
- ≥ 30 minutes of substantive work has happened without a save

## Behavior

Follow the steps in `spec/commands/memory-save.md`:

1. Internally summarize: files modified, decisions, open questions, next steps
2. Derive a kebab-case slug (≤ 6 words)
3. Write the four required sections (`## What was done`, `## Decisions`, `## Open questions`, `## Next session`) to `/tmp/memory-save-body.md`
4. Shell out to:
   ```bash
   ~/.copilot-memory/bin/memory-save \
       --slug "<slug>" --project "<project>" --source cursor \
       --body-file /tmp/memory-save-body.md
   ```
5. Confirm verification passed

## Don't

- Don't push git commits — the script will `git commit` only, never push
- Don't fabricate decisions or work that didn't actually happen this session
- Don't write the log somewhere other than `$VAULT/logs/`
- Don't skip the verification step
