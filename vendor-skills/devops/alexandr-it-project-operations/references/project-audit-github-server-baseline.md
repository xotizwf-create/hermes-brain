# Project audit: GitHub vs live server baseline

Use this pattern when Александр asks for a full audit of a project that is already deployed and may have been hotfixed directly on the server. The goal is to establish a trustworthy baseline before cleanup/refactoring.

## Principle

Do the first pass **read-only**. Compare the canonical GitHub repo with the actual live checkout before proposing code cleanup. A project can have green CI in GitHub while production is ahead, dirty, or surrounded by server-only artifacts.

## Checklist

1. **Load project registry/runbooks first.** Resolve the project slug, repository, live host, code path, service names, deploy path, and secret-reference location from Hermes Brain/project docs. Do not ask the owner for facts already documented.
2. **Clone/fetch GitHub locally.** Record branch, HEAD, remotes, recent commits, manifests, CI workflows, docs, tests, and major component sizes.
3. **Read-only production preflight.** Check host, time, resources, running services, code path, git branch/status, remotes, HEAD, and top-level files. Do not source arbitrary secure env files; parse only required SSH keys/fields and never print secret values.
4. **Compare repo vs server.** Run `git fetch --prune`, `git rev-list --left-right --count origin/main...HEAD`, `git log origin/main..HEAD`, `git diff --stat/name-status origin/main..HEAD`, and inspect untracked files. Treat any server-ahead commit as a blocking baseline issue before refactoring.
5. **Classify server dirt.** Separate tracked code differences, untracked runtime state, exports/cache/logs, `.bak`/`.predeploy` hotfix artifacts, `.env` backups, and real local-only operational files. Do not delete anything during audit; propose archive/removal as a later controlled operation.
6. **Verify away from production.** Run unit/static/frontend checks on a local clone or CI-like environment, not on the live server. Missing test tools on production are not a product failure; avoid installing dev dependencies on prod during audit.
7. **Audit dependencies as a separate signal.** Run Python/frontend audits locally when practical and report vulnerabilities separately from code-structure risks.
8. **Produce phased recommendations.** First: make GitHub match production. Then: document architecture, clean server artifacts, define PR/CI/deploy workflow, add tests around risky behavior, and only then split monoliths.

## Reporting template

- **Baseline:** GitHub repo/branch/HEAD; server branch/HEAD; ahead/behind; dirty/untracked summary.
- **What is safe now:** which test/build/audit checks passed in the local clone.
- **Critical before cleanup:** server-only commits, dirty tracked files, missing source-of-truth, unsafe direct hotfix pattern.
- **Important but not urgent:** monolithic files, stale docs, dependency advisories, bundle size, legacy surfaces.
- **Do not do yet:** broad refactor, deletion of server backups, prod installs, deploy from GitHub until server-only code is preserved.
- **Next PRs/operations:** small ordered list, one purpose per PR.

## Albery example distilled

During the Albery audit, GitHub tests/build passed locally, but the live checkout was `ahead 1` with a production hotfix in `mcp/context_server.py` and many untracked `.bak`/`.predeploy` files. The correct recommendation was not immediate cleanup; it was:

1. preserve the server-only hotfix in GitHub first;
2. make GitHub the source of truth;
3. archive/remove server-only backup artifacts later;
4. keep future changes in small PRs with CI before deploy.
