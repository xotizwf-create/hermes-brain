# Project audit PR continuation and CI recovery

Use this when continuing work after an initial project audit where some audit artifacts, docs, or safety patches already exist and the branch may be stale.

## Durable pattern

1. **Reconstruct from facts, not memory.** Inspect the project card, repo status, branch, existing audit artifacts, staged/untracked files, and recent local/remote commits before deciding the next step. Treat compacted conversation summaries as hints only.
2. **Update against current `main` before opening/updating PRs.** If the working copy is behind origin, stash including untracked files, fast-forward from origin, then reapply the patch and resolve conflicts. Re-run targeted tests after conflict resolution.
3. **Preserve both sides of safety conflicts.** When `main` added new tools while the audit branch added risk metadata/confirmation gates, merge the new tools into the safety model instead of choosing one side. Every newly introduced mutating/external tool needs metadata and, when appropriate, a schema/runtime `confirm=true` gate.
4. **Map open PR topology before continuing.** When the owner references “all the PRs” or asks whether they will be combined, inspect the actual PR list and branch bases. Distinguish already-merged PRs, stacked PR chains (branch N based on branch N-1), and independent PRs based on `main`. Do not assume every open PR can be merged independently; either merge a stack in order or prepare a consolidated branch/PR from the stack.
5. **Safety-gate implementation checklist for MCP tools:**
   - reject missing `confirm=true` at the top of the handler, before DB/cache/org lookups or external helpers;
   - add `confirm` to the MCP `inputSchema` and `required` fields;
   - update risk metadata (`requires_confirm`, `writes_db`, `external_action`, route hint);
   - for live runtime-behavior writes (AI instructions/prompts), require exact path/content preview and support an `expected_current_content`/stale-preview guard so a confirmed overwrite fails if the current text changed after preview;
   - add a regression test that monkeypatches downstream work and asserts it is not called before confirmation;
   - for stale-preview guards, test that the handler raises before issuing the UPDATE when current content differs;
   - update audit docs so findings reflect the newly closed risk.
6. **Verify narrow then broad.** Run the new regression test, adjacent MCP registry/contract tests, `git diff --check`/syntax checks, then the safe broader suite. Avoid live DB/external services unless the task explicitly requires them.
7. **Treat CI dependency-audit failures as part of PR readiness.** If backend/frontend tests pass but dependency audit fails, inspect whether the PR changed dependency manifests. If the failure is pre-existing but blocks the PR, prefer minimal safe dependency updates rather than ignoring the red check.
8. **Debug npm audit by dependency path.** Run audit JSON and inspect `package-lock.json` to see which package pulls the vulnerable transitive dependency. Example pattern: a Vite advisory may be resolved by Vite patch update, while remaining `esbuild` exposure can come from `tsx`; update the actual parent package, not only the package named in the advisory.
9. **Use lockfile-safe updates first.** Prefer `npm install <pkg>@<safe-range> --package-lock-only`, then `npm ci`, `npm audit --omit=dev`, `npm run lint`, and `npm run build`. Avoid `--force` unless a breaking major upgrade is intentionally accepted.
10. **Do not report PR success until GitHub checks are green.** After pushing, watch checks and inspect failed logs. Final state should include clean working tree, PR URL, merge state, and check conclusions.

## Example distilled from Albery

A post-audit branch contained Stage B/C docs plus MCP safety gates. After fetching `main`, conflicts surfaced because `main` added new Google/Bitrix-agent MCP tools. The fix was to merge the new tools into the risk metadata, add missing confirmation gates for write/external tools, add a `process_chat_ocr` confirmation test, and update the audit document to say the risk was closed. When the owner later referenced “all PRs,” the correct recovery was to inspect the PR topology and separate already-merged PRs, a stacked cleanup chain, and an independent safety/docs PR instead of guessing from compacted context.

For live AI-instruction edits, the follow-up safety fix was not just `confirm=true`: `upsert_ai_instruction` also needed tool-contract preview wording, `requires_confirm=true` risk metadata, and an `expected_current_content` guard so a confirmed overwrite is rejected if the instruction changed after preview. Tests covered “no DB connection before confirm” and “stale preview raises before UPDATE.” CI then exposed unrelated frontend dependency-audit failures; minimal updates to Vite/tsx and the lockfile made backend, frontend, and dependency-audit checks green.
