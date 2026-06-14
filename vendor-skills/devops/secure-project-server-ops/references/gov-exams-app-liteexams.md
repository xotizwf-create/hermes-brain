# Gov Exams App / LiteExams server notes

Non-secret operational notes from a server inspection. Do not add credentials here.

## Project identity

- Secure project slug: `gov-exams-app`
- App observed on server as LiteExams
- App directory observed: `/var/www/liteexams/app`

## Services/processes observed

- `liteexams-bot.service` — LiteExams Telegram Bot
- `liteexams.service` — LiteExams Node API
- `pm2-root.service` — PM2 process manager
- Bot runtime observed via `npm run bot:telegram` / `tsx server/telegramBot.ts`
- API runtime observed via `tsx server/index.ts`

## Support button text

When asked to change the Telegram bot “техподдержка” message, the relevant runtime source was:

- `server/telegramBot.ts`

The old support message appeared in three runtime source locations:

```text
Если у Вас возникли проблемы - пишите @alexxandrn или @lilchel2, мы всё быстро решим!
```

Requested replacement:

```text
Если у Вас возникли проблемы - пишите @lilchel2, мы всё быстро решим!
```

After editing, verify all old support-message occurrences are gone and restart only `liteexams-bot.service` unless the change clearly affects the API or frontend too.

## Token management notes

- GitHub repo: `xotizwf-create/gov-exams-app` (private), default branch `main`.
- Production working directory observed as `/var/www/liteexams/app`; during 2026-05-31 inspection it did not report a git branch/origin, so prefer changing the GitHub repo first and then deploy/sync intentionally.
- Access tokens are stored in Postgres tables created by `server/schema.ts`:
  - `access_tokens` for active desktop/mobile tokens.
  - `access_tokens_archive` for archived/deleted tokens with `archived_reason`.
  - `telegram_access_users` for allowed Telegram users.
  - `telegram_user_access_scopes` for remembered institute/direction/profile.
- Existing token behavior in `server/telegramBot.ts`: `archiveAndDeleteTokensByUsername`, `issueTokenPair`, `reissueTokenPairForUser`, `getLatestUserTokens`. Reissue currently archives and deletes the user's tokens, then issues a new desktop+mobile pair while preserving scope and last device-binding metadata from archive.
- Existing admin API behavior in `server/index.ts`: create token, list tokens, enable/disable by id, delete by id. Delete archives the token but may clear user scope/history when no active token remains, so MCP token rotation should use a dedicated shared service function rather than chaining the current admin delete endpoint blindly.
- For an MCP command like “Обнови мобильный токен @alexxandrn”, implement a tool that normalizes username, starts one DB transaction, archives only the active `mobile` token with reason like `mcp_mobile_reissue`, deletes/replaces that token, preserves institute/direction/profile from the old token or user scope, optionally clears mobile device binding if the goal is to let a new phone bind, writes an audit entry, and returns the new token only once.
- Live non-secret check on 2026-05-31: `@alexxandrn` existed as an active user with desktop and mobile tokens for ИУЭиФ / Менеджмент / Маркетинг; both had device binding, mobile had been used.

## MCP token-management implementation/deploy notes

During the 2026-05-31 implementation attempt, the safe shape was:

- Add a shared server module for token operations rather than having MCP call current admin HTTP routes directly.
- Add tests that prove rotating `mobile` archives/deletes only the old mobile token, preserves the desktop token, preserves institute/direction/profile, resets only the rotated device binding by default, and writes audit.
- Add an internal stdio MCP server entrypoint with tools such as `get_user_tokens`, `rotate_mobile_token`, and `rotate_desktop_token`.
- Add npm scripts for targeted token-management tests and the MCP server.
- Local gates used before deploy: `npm run lint`, full `npm run test:all`, and `npm run build`.
- Production host is very memory-constrained (observed about 1 GB RAM). A server-side `vite build` was killed with exit 137 after tests had passed. A 2 GB swapfile was added during the 2026-05-31 deployment to reduce OOM risk, but heavy builds/full test suites still should not run on the host. Safer deploy path is to build `dist/` locally from the tested release and upload the prebuilt `dist` with the release archive.
- Use timestamped releases under `/var/www/liteexams/releases/<timestamp>` and keep `/var/www/liteexams/app` unchanged until the release directory has dependencies, `.env.local`, lightweight smoke checks, MCP protocol smoke test, and `dist/index.html` verified. Avoid full typecheck/build on this small production box.
- If SSH or systemctl checks begin timing out after preparing a release, do not switch `/var/www/liteexams/app` or restart `liteexams.service`/`liteexams-bot.service`; stop at the safe point and resume only when management access is stable.
- Active MCP token-management deployment on 2026-05-31: branch `feat/mcp-token-management`, commit `b4cac29`, active release timestamp `20260531_094204`, rollback snapshot `app_backup_before_mcp_20260531_094204`. Hermes native MCP server `gov_exams_tokens` exposes 3 tools: safe token status, rotate mobile token, rotate desktop token.

## Hang / freeze investigation notes

- For “server hung” reports, check previous boots as well as current logs: OOM events may be in the previous boot's kernel journal, while the current boot can look clean after an external reset.
- Known incident pattern from 2026-05-30/31: 1 GB RAM host, Node process OOM-killed, database connections terminated unexpectedly, bot Telegram callbacks timed out, journald watchdog warnings, SSH management becoming unstable. A 2 GB swapfile and low OOM priority for critical services reduce recurrence, but do not make heavy on-box builds/tests safe.
- If the host has about 1 GB RAM and available memory is below the required reserve, the safe on-box heavy-work budget is effectively zero or negative. Do not build/test/migrate there; do it off-box and deploy prebuilt artifacts only.
- After an unplanned reboot, the bot may fail once on Telegram API setup due to a transient network timeout and then recover on the automatic retry. Treat this as a startup network symptom unless it repeats.
- HTTP smoke checks should follow the public redirect to `www` before concluding the site is down; the bare domain returning a redirect is normal.
- Production resource guard applied after the OOM incident: API is bounded at MemoryHigh 300 MB / MemoryMax 420 MB / swap 512 MB, bot at 220/320/384 MB, nginx at 96/160 MB, PM2 at 120/220/256 MB; API/bot/nginx/postgres are protected with low OOM score where appropriate. These limits are intended to restart a leaking Node service instead of freezing the whole 1 GB host. If normal RSS approaches the high limit, investigate memory growth before raising the cap.

## Pitfalls

- The secure `.env` for this project may contain a non-KEY=VALUE human note line. Do not `source` it directly; parse only `KEY=VALUE` lines and pass credentials via environment.
- Search output can include huge built frontend assets under `dist/`; for bot behavior, prioritize `server/telegramBot.ts` and the running service command line.
- Do not print actual token values during inspection. For MCP responses, token value may be returned only for successful creation/rotation, and should be treated as a secret shown once.
