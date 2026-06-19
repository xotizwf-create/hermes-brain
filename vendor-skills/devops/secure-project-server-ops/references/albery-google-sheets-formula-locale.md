# Albery Bitrix AI agent — Google Sheets formula locale validation

Use this reference when investigating or fixing bad Google Sheets created by the Albery Bitrix AI agent.

## Durable lesson

Google Sheets created through the Albery agent may use a Russian spreadsheet locale. In that locale, formulas that look correct in English examples can be invalid because function arguments must be separated with semicolons (`;`) instead of commas (`,`). A broken sheet can still be created and shared successfully, so “created and link returned” is not enough verification.

## Investigation pattern

1. Start with Albery MCP instructions, then inspect the Bitrix bot session for the user/request that created the sheet.
2. Identify the created spreadsheet title/link from the bot transcript or server logs.
3. On the Albery server, inspect the Google Sheets integration code and the exact write path used by the agent/tool, not just the prompt text.
4. Check both the created values and rendered formulas for formula parse errors after writing.

## Fix pattern

1. Normalize formula separators according to the spreadsheet locale before writing formulas.
   - Russian/semicolon locales: convert top-level formula argument commas to semicolons.
   - Do not blindly replace commas inside quoted strings or decimal literals.
2. After write/update, perform a verification pass against the sheet cells that were written.
3. If any formulas evaluate to parse errors, return an error to the agent instead of letting it tell the user the sheet is ready.
4. Repair the already-created sheet if the user complained about a concrete generated file.
5. Restart only the affected Albery services and verify they are active.
6. Push the production hotfix back to the canonical GitHub repo; if the production host cannot push because its remote is HTTPS without credentials, apply the same patch from a local clone with configured `gh` auth, then reset/fetch production to `origin/main` so prod and repo share the same commit.

## Verification checklist

- `python3 -m py_compile` passes for changed Python files.
- A real temporary Google Sheet created in the same flow has no formula errors.
- The user’s original bad sheet is repaired if possible.
- `albery.service` and `hermes-gateway.service` are active after restart.
- `git status -sb` on production shows no ahead divergence from `origin/main` after the repo sync.

## Reporting to the owner

Report practical outcomes: session found, root cause, original sheet repaired, guard added, real test passed, services healthy, repo synced. Do not dump spreadsheet credentials, env values, or internal links unless asked.