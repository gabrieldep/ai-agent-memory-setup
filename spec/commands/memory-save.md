# /memory-save

> Snapshot the current session into persistent memory. Aliases: `/save`.

## Behavior contract

When this command is invoked, the agent MUST:

1. **Summarize the session** internally:
   - Files modified (with paths)
   - Decisions made (with one-sentence justification each)
   - Open questions that didn't get resolved
   - Suggested first action for the next session

2. **Derive a slug** for the log file: kebab-case, ≤ 6 words, descriptive of the main accomplishment. Examples: `auth-refactor`, `rate-limit-investigation`, `migrate-to-server-sessions`.

3. **Write the log** to `$VAULT/logs/YYYY-MM-DD-HHMM-<slug>.md` with this structure:

   ```markdown
   ---
   title: <slug humanized>
   tags: [session, <project>, <topic>]
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   status: complete
   type: session-log
   project: <project-slug>
   source: <agent-name>  # cursor | copilot | claude-code | etc.
   ---

   # <slug humanized>

   ## What was done
   - <bullet with wikilinks to modified notes / files>

   ## Decisions
   - <one sentence per decision>

   ## Open questions
   - <unanswered questions>

   ## Next session
   - <suggested first action>
   ```

4. **Insert wikilinks** for every note, project, or concept mentioned that has a corresponding file in `$VAULT/`.

5. **Update any project notes** that need updating (e.g., add a line to `$VAULT/<project>/architecture/decisions.md` if a real decision was made).

6. **Shell out to the verification script**:

   ```bash
   ~/.copilot-memory/bin/memory-save --check
   ```

   The script verifies the log was written, has valid frontmatter, and contains at least the four required sections. If verification fails, fix the log before continuing.

7. **Git commit (if applicable)**: if the current working directory is a git repo AND the user has not asked to skip git, stage all changes and commit with message:

   ```
   session: <slug>

   <one-sentence summary>
   ```

   Do NOT push unless the user asks.

## Script fallback

For the deterministic path, the agent can do the work itself OR shell out entirely to:

```bash
~/.copilot-memory/bin/memory-save \
    --slug "<slug>" \
    --project "<project-slug>" \
    --source "<agent-name>" \
    --body-file /tmp/memory-save-body.md
```

Where `/tmp/memory-save-body.md` is the markdown body (sections 3.1–3.4 above) written by the agent. Alternatively, pipe the body in: `... | memory-save --slug <s> --stdin`. The script handles frontmatter, file placement, and git commit.

## Examples

### Good slug derivation

| Session topic | Slug |
|---|---|
| "Refactored authentication to use Supabase sessions" | `auth-refactor-supabase` |
| "Debugged a flaky test in the payments suite" | `payments-flaky-test` |
| "Added rate limiting middleware" | `rate-limit-middleware` |

### Bad slug derivation (DO NOT)

| Bad slug | Why |
|---|---|
| `session-2026-06-02` | Date is already in the filename; redundant |
| `did-some-work` | Not descriptive |
| `RefactoredAuthentication` | Not kebab-case |
| `i-fixed-the-thing-that-was-broken-yesterday-with-the-auth` | Too long |

### Bad behavior

- Skipping the verification script
- Writing the log to the project repo instead of the vault
- Pushing the git commit without asking
- Committing changes that the user didn't actually approve in this session
