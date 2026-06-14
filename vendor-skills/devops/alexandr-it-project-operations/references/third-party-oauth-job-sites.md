# Third-party OAuth job-site automation notes

Use for flows like hh.ru where Александр wants the agent to search vacancies, prepare cover letters, and potentially apply on his behalf.

## Safety model

- Prefer official OAuth/API access over collecting passwords, cookies, or browser sessions.
- Never ask for or store the account password in chat.
- Treat `client_secret`, authorization codes, access tokens, refresh tokens, cookies, and session links as secrets. Redact them in summaries and never echo values back.
- Send applications/responses only after explicit user confirmation unless a separate operating mode has been clearly approved.
- Before any external action, show the vacancy/employer, selected resume, cover-letter text, and intended action.

## hh.ru OAuth shape observed 2026-06-02

- Developer cabinet: `https://dev.hh.ru/admin`
- OAuth authorization URL from API spec: `https://hh.ru/oauth/authorize`
- Token URL from API spec: `https://api.hh.ru/token`
- API docs/spec page: `https://api.hh.ru/openapi/redoc`, spec source `https://api.hh.ru/openapi/specification/public`
- Token request supports `authorization_code`, `client_secret`, `redirect_uri`, and optional PKCE fields (`code_verifier` when `code_challenge` was used).
- Redirect URI can be validated against the application settings. A practical callback for manual/agent-assisted auth is `http://127.0.0.1:8765/hh/oauth/callback`, but only use a listener if the environment can receive the redirect. Otherwise ask the user to paste only the final redirected URL/code, then exchange immediately.

## Recommended workflow

1. Verify site/API reachability from the current network. If hh.ru blocks VPN egress, load `secure-project-server-ops` and apply per-destination route triage instead of disabling VPN.
2. Ask Александр to create an hh.ru developer app in `https://dev.hh.ru/admin` and provide the `client_id` and `client_secret` through the safest available secret channel. If he sends them in chat, treat them as secrets and do not repeat them.
3. Build an authorization URL using the created app and redirect URI.
4. Александр opens it locally, logs in, and approves access. He should not send his password.
5. If the callback cannot be captured automatically, have him paste the redirected URL/code. Exchange the authorization code immediately for tokens.
6. Store tokens only in the approved secret store; do not put token values in memory, skills, session summaries, or final messages.
7. Smoke-test access with safe reads first: current user/profile, `resumes/mine`, and vacancy search.
8. Configure search criteria and ranking before applying: role, city/remote, salary, experience, exclusions, stop words, selected resume, and cover-letter tone.
9. For each application batch, show a concise approval list and send only approved responses.

## Pitfalls

- Do not fall back to password-in-chat login just because OAuth setup has friction.
- Do not assume public vacancy API access works from every egress route; hh.ru may respond differently through VPN vs the server's original Russian IP.
- Do not mass-apply automatically from a first search result set; reputation risk is high.
- Do not record exact tokens, authorization codes, cookies, or app secrets in durable artifacts.
