---
name: project-onboarding
description: Use when the user wants the agent to create or take over a project and actually work in its repo — get the project's env, production access (ip/user/password or key), and git access, then write code guided by the brain's standards. End-to-end wrapper over new-repo + add-project + secure-access; stores credential references only, real values go to the server secure store.
---

# Skill: project-onboarding

## Goal
Make a project *workable by the agent*: a repo it can clone/branch/push, production access it can
use, the project `.env` it can read — all wired through the server secure store (no secrets in the
brain) — so the agent can write code on it using the brain's `engineering/` standards.

## Where the agent gets each access (the "где брать" answer)
Everything lives in the **server secure store**, provisioned once per project; the agent reads it via
the `secure-access` skill and **never prints or commits** values.

| Need | Stored in | Referenced by name |
|---|---|---|
| Prod server (ip/user/password or key) | `/root/.hermes/secure/secrets.yaml` | `access-map.yaml` service `server-root` → `proj/<slug>/ssh/root` |
| Git access (clone/pull/push/PR) | deploy key or fine-grained PAT in `secrets.yaml` | `access-map.yaml` service `github` → `proj/<slug>/github/<token>` |
| Project `.env` (runtime config) | on the prod server in the working dir (e.g. `/var/www/<slug>/.env`), **not** in git | `secret_refs` in the project manifest; `value_path` in `secrets.yaml` if the agent must read it |

## Onboard a project (approval-gated)
1. **Repo.** New project → `new-repo` skill (private by default). Existing → record its URL.
2. **Register.** `add-project` skill: create `projects/<slug>/`, fill `project.yaml` + docs, list
   `secret_refs` (names only). Regenerate registry, validate.
3. **Provision access** (`secure-access`): add the project's `server-root`, `github`, and any env
   `value_path` entries to `access-map.yaml` (metadata + `allowed_actions`). For each real value,
   **ask the user to place it** in `/root/.hermes/secure/secrets.yaml` (the agent does not type
   secrets). Mode stays 600 root:root; verify with `scripts/check_secret_permissions.sh`.
4. **Clone onto the work host.** Clone the repo into the server working dir using the project git
   credential. Add a `.gitignore` that excludes `.env*`/keys before any commit.
5. **Verify** (prints nothing secret): `ssh`/`_deploy_helper`-style connectivity, `git rev-parse`,
   service status.

## How the agent actually writes code
- Run a coding session/cron with project context:
  `hermes --workdir <repo_path> --skill codex` (or `claude-code`) — `--workdir` injects the repo's
  `AGENTS.md`/`CLAUDE.md`/`.cursorrules` and sets cwd for file/terminal/code tools.
- Follow the brain: `engineering/coding-standards.md`, `security.md`, `testing.md`, `deployment.md`,
  and the project's own `projects/<slug>/` docs.
- **Git discipline** (same as albery): branch off `main` (`feature/…`,`bugfix/…`), one task per
  branch, push the branch, **never push to `main` without explicit ask**, open a PR with a diff
  summary.

## Forbidden
- Secret values in the brain, in git, in logs, or in command-line arguments.
- Inventing a workaround when access is missing — document the exact credential name/scope/provider
  needed and ask the user to provision it.

## Done when
Repo wired, project registered + validated, access provisioned in the secure store (values added by
the user), connectivity verified, and a first branch/PR flow proven on the repo.
