# Hermes / Codex credential pool checks

Use this when Александр asks which ChatGPT/Codex account Hermes is using, whether it switched accounts after a limit, or whether the account is the one "with email" or "without email".

## Safe inspection

1. Load `hermes-agent` for the official commands, but do not edit that bundled skill.
2. Check the pool with a redacted command such as:
   ```bash
   hermes auth list 2>/dev/null \
     | sed -E 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[email]/g; s/(token|key|secret|password)[^[:space:]]*/[secret]/Ig'
   ```
3. Interpret the active marker (`←`) as the currently selected credential.
4. Treat `rate-limited`, `usage_limit_reached`, or an explicit remaining cooldown as the reason the previous credential was skipped/rotated.
5. If the user asks for the cooldown time, convert it to Moscow time before answering; Александр’s default timezone is MSK.

## How to explain it to Александр

- Be concise and operational.
- Do not reveal email addresses, tokens, OAuth details, or raw credential IDs unless specifically safe and necessary.
- Use the user's labels when known: “аккаунт с почтой” vs “аккаунт без почты”.
- Explain the direction of the switch: e.g. “с почтового аккаунта ушли на безпочтовый, потому что почтовый сейчас на лимите”.
- Distinguish subscription-expiry watcher from short-term usage limits: the watcher removes expired subscriptions; runtime credential-pool rotation handles 429/usage-limit recovery.

## Pitfalls

- Do not infer the active account from memory or a prior turn; always check live state.
- Do not say a limit “кончился” if the pool shows it is still rate-limited. Say when it should release.
- Do not persist raw emails, tokens, or credential dumps into memory/skills/session notes.
