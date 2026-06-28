# PR cleanup fallback and dependency-audit notes

Use this when a small cleanup/refactor PR is being prepared and Codex delegation is unavailable or the CI dependency audit turns red.

## Small cleanup fallback
- Keep the change bounded enough to review manually: one pure module extraction, one helper class, one narrow test fix, etc.
- Preserve the old public import/API surface when extracting helpers so existing routes, scripts, and tests continue to call the same names.
- Move imports to normal top-level locations before final review; avoid mid-file compatibility imports unless there is a specific circular-import reason.
- Verify before PR and again after any style/dependency follow-up:
  - Python compile/import smoke for touched modules.
  - Targeted unit tests around the moved code.
  - Full quick backend test set if available.
  - Frontend lint/build if CI includes it.

## If GitHub dependency-audit fails after a refactor
- Treat a red audit as a PR blocker even if unrelated to the refactor, but keep the fix as a separate commit in the same branch.
- Prefer updating the top-level package that owns the vulnerable transitive dependency instead of forcing a low-level override.
- Example pattern from Vite/esbuild/tsx:
  - `npm audit fix` may update Vite enough to clear high-severity issues while leaving a low-severity esbuild issue through another parent package.
  - A direct `overrides.esbuild` can make `npm audit` green but break the production build because esbuild internals may be incompatible with the current bundler target.
  - Inspect which top-level dependency pulls the vulnerable esbuild; update that parent (for example `tsx`) and the bundler/plugin pair together, then run `npm audit --omit=dev`, `npm run lint`, and `npm run build`.
- Final PR evidence should include both local verification and GitHub checks: backend, frontend, and dependency-audit all green.
