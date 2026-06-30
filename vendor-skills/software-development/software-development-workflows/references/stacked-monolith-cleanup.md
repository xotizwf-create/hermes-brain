# Stacked monolith cleanup without behavior changes

Use this reference when the user wants a large application made more readable while preserving all existing functionality.

## Proven pattern

- Treat readability cleanup as a chain of small PRs, not one broad rewrite.
- If earlier cleanup PRs are still open, base each new branch on the previous cleanup branch (`phase N` on `phase N-1`) so reviewers can inspect one cohesive change at a time.
- Pick one pure/helper category per PR: datetime helpers, LLM utilities, spreadsheet formatting helpers, Drive payload formatting helpers, transcript parsing helpers, etc.
- Avoid production deploys and avoid merging to `main` unless explicitly requested.
- Preserve public/internal function names at call sites during extraction when the goal is readability only; semantic renames and call-site rewrites should be a separate explicit PR.
- Add focused unit tests for the extracted helper behavior, especially formatting, locale, timestamp, transcript parsing, and structured-text edge cases.
- In behavior-preserving cleanup, tests are characterization tests: if a focused test reveals an odd existing behavior (for example a leading transcript metadata line is kept as a text segment), preserve and document that behavior instead of “improving” it inside the extraction PR.
- Run targeted tests first, then the broader relevant suite, then syntax/import checks.
- Open the PR only after local checks pass; then wait for GitHub checks and fix failures before reporting done.
- After extracting helpers from a monolith, verify both sides explicitly: run a search that old `def ...` declarations are gone from the monolith, and keep compatibility imports so existing call sites still resolve the same names.
- For stacked PR creation, tolerate older GitHub CLI versions: if `gh pr create --json ...` fails with `unknown flag: --json`, run plain `gh pr create` first, then `gh pr view ... --json ...` as a separate verification step.

## Good PR scope

A good cleanup PR should be explainable in one sentence: "extract pure Google Drive payload helpers" or "extract timestamp formatting helpers". If the summary needs several unrelated bullets, split it.

## Report format

Report in terms the owner cares about:

- what was extracted;
- confirmation that functionality, production, and `main` were not touched;
- tests run and actual pass counts;
- PR URL and stack base;
- next safe candidate.

## Pitfalls

- Do not present cleanup as feature work.
- Do not bundle API/database/network behavior with pure helper extraction.
- Do not say checks are green until both local checks and CI are verified.
- Do not let a coding-agent/auth hiccup block the work if the next safe extraction is small enough to do directly with normal file tools.
