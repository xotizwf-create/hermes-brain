---
name: update-knowledge
description: Use when changing the brain itself — adding/editing knowledge, classifying inbox items, or syncing to the Hermes server. Enforces approval-gated, logged, validated edits.
---

# Skill: update-knowledge

## Goal
Evolve the brain safely: classify → edit → validate → confirm if needed → commit → log → sync.

Owner standing preference (2026-05-30): when the agent discovers or performs a new non-trivial
procedure that is not yet documented, it should update the closest matching instruction/skill on its
own; if none exists, create a new instruction. Do not ask separately whether to document it.

## Classify new information into one area
- **profile** — user, preferences, communication, hard rules.
- **engineering** — universal how-to-build.
- **project** — belongs to a specific project (`projects/<slug>/`).
- **connector** — an MCP connector.
- **personal** — education, side-jobs, life knowledge.
- **skill** — a repeatable procedure.
- If unclear, drop into `inbox/unsorted.md` and propose classification later.

## Algorithm
0. **Start clean.** Before editing, run `git status --short` in the brain repo. If there are unrelated
   dirty files, stop and resolve them first: inspect the diff, then either commit the previous approved
   change with its changelog line or explicitly revert junk. Do not mix unrelated brain edits in one
   commit and do not leave the repo dirty after answering the owner.
   **One-off scripts and task outputs go ONLY to `tmp/` (gitignored) — never the repo root.** The
   2026-07-02 cleanup moved ~30 `_*_tmp.*` / `.xlsx` leftovers out of the root; one of them was even
   breaking `validate.py`. If a scratch script proves reusable, promote it to `scripts/` with a real
   name and docstring instead of leaving it in the root.
1. Decide the target file (or new file). New docs MUST have valid frontmatter
   (`id`, `type`, `updated`, optional `tags`/`secret_refs`/`aliases`) per `schema/frontmatter.schema.yaml`.
2. Make the edit. Bump `updated`. Never write secret values — references only.
3. If a project manifest changed: `python scripts/build_registry.py`.
4. If docs or frontmatter changed, rebuild and verify the section index before validation:
   `python3 scripts/build_section_index.py && python3 scripts/build_section_index.py --check`.
   Index generation reads frontmatter strictly: `tags` must be strings (quote numeric-looking tags such
   as `"217"`), and every indexed doc needs valid frontmatter. If you edit `logs/changelog.md` after
   rebuilding, rebuild the section index again because the changelog itself is indexed.
5. `python scripts/validate.py` — must pass.
6. Approval gate: if the owner has not already explicitly authorized the documentation update, show the
   diff and wait for confirmation. If the owner explicitly says to add/update without showing the diff
   (for example, "ничего не надо показывать, просто добавляй"), treat that as approval and proceed.
7. Append a line to `logs/changelog.md`. For architectural choices, add to `logs/decisions.md`;
   for lessons, `logs/learning-log.md`; for errors, `logs/mistakes.md`. Then rerun step 4 so
   `section-index.md` includes the changelog entry.
8. Commit only the intended files, push, then verify `git status --short` is clean. If push is rejected
   because remote advanced, use `git pull --rebase`, resolve only real conflicts, rerun index+validate,
   then continue with `GIT_EDITOR=true git rebase --continue` when Git asks for an editor in a dumb
   terminal. If any local-only operational file remains, explain it to the owner and either add it to
   the proper repo/skill or move it outside the brain.

## Self-improvement loop (how the agent gets smarter over time)
The brain is the agent's long-term memory; improvement = reliable retrieval + reusable tools +
visible failures, not a bigger model. Four habits, always on:

1. **Search before you decide you don't know or pick a skill.** Run
   `python3 /root/.hermes/agent-knowledge/scripts/brain_search.py "<keywords>"` — one search across
   BOTH trees (versioned brain + Hermes' bundled skills in `/root/.hermes/skills/`). Open the top hit.
   (The 2026-06-14 Росреестр flail happened because the agent skipped this and opened the wrong skill.)
2. **Capture repeatable work as a TOOL, not just prose.** When a non-trivial multi-step task is likely
   to recur, ship a ready-to-run script under `scripts/` (clear docstring + the gotchas) and point the
   nearest skill/reference at it — so next time it's one command, not a re-invention under an iteration
   cap. Example: `scripts/nspd_parcels_local.py` turned a 1.5 h flail into one call.
3. **Make failures visible, then turn them into triggers/tools.** Silent degradations are caught by the
   hourly `self-check` cron (`scripts/hermes_selfcheck.py`: SOUL-blocked / codex token_invalidated /
   provider-unhealthy / compression-fail / media-drop → Telegram). Every real failure gets a
   `logs/mistakes.md` entry whose "avoid next time" is a concrete **trigger keyword, script, or skill
   edit** — not advice. The weekly `self-review` digests these.
4. **Keep retrieval honest.** If `brain_search` can't surface something that should exist, that's a gap
   — add/clarify the doc or skill (good title + frontmatter `description`/`tags`) so it ranks next time.

## Sync model: two-way git (single source of truth)
Canonical = the GitHub repo `hermes-brain`. Both the local working copy
(`g:\OneDrive\Рабочий стол\Мои проекты\Hermes Brain`; the old `C:\hermes-brain` clone was removed
2026-07-02 as stale) and the server brain (`/root/.hermes/agent-knowledge`, a **git clone**) are
checkouts of it. Sync = git.

- **Local edit → everywhere:** commit locally → `git push` → on the server `git -C
  /root/.hermes/agent-knowledge pull --ff-only`.
- **Server/Hermes edit → everywhere:** Hermes commits+pushes on the server (see self-scaling) →
  locally `git pull`.
- Hermes `config.yaml` system_prompt points only at `…/agent-knowledge/INDEX.md`; knowledge files
  are read on demand, so **no gateway restart** is needed after a content sync.

**Deployed 2026-05-30.** The server brain is a clone authenticated by a repo-scoped **read-write
deploy key**:
- key: `/root/.ssh/hermes_brain_deploy` (ed25519); registered on the GitHub repo as deploy key
  `hermes-server-rw` (read_only=false).
- `/root/.ssh/config` routes `github.com` through that key; the clone also pins
  `core.sshCommand`. Remote: `git@github.com:xotizwf-create/hermes-brain.git`.
- commit identity: `hermes-server <hermes-server@users.noreply.github.com>`.
- Verified round-trip: server `pull` + `push` work; local `pull` picks up server commits.

To rebuild from scratch (e.g. new server): generate the key, add it as a read-write deploy key
(`gh api repos/<owner>/hermes-brain/keys -f key=... -F read_only=false`), write `~/.ssh/config`, then
`git clone git@github.com:xotizwf-create/hermes-brain.git /root/.hermes/agent-knowledge`. Bootstrap
transport before any clone exists = tar via `_deploy_helper.py new --put` (see git history).

## Self-scaling: Hermes edits its own brain (autonomous, still approval-gated)
When Hermes (on the server) needs to add/update an instruction or skill:
1. Edit the file under `/root/.hermes/agent-knowledge/` (or add a new doc with valid frontmatter).
2. `python scripts/validate.py` in that dir — must pass. If a manifest changed, `build_registry.py`.
3. Approval gate in Telegram: show the diff and wait for "да/ок" unless the owner already explicitly
   authorized this exact update without a diff in the current conversation.
4. After approval: `git add -A && git commit` (end message with the Co-Authored-By trailer) and
   `git push`. Append one line to `logs/changelog.md`.
5. Tell the owner it's live; the local copy picks it up on the next `git pull`.

If unsure whether a change is warranted, drop a note in `inbox/unsorted.md` and ask the owner instead
of editing core docs.

## References
- `references/brain-index-autocommit-blockers.md` — recovery recipe for `build_section_index.py` failures, stale `section-index.md`, and brain push/rebase conflicts.

## Rule
No silent unapproved edits. Validate + owner approval + changelog every time — locally or on the server.
Showing a diff is the default approval path, but explicit owner instructions to update without showing it are valid approval.
