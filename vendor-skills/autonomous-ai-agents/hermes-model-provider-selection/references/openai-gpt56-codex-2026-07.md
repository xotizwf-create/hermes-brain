# OpenAI GPT-5.6 in Hermes via `openai-codex` — 2026-07 check

Context: checking whether the current Hermes profile could use the newly released GPT-5.6 family through the `openai-codex` provider.

## Durable findings

- Hermes' static model catalog may lag new OpenAI releases. Absence from `_PROVIDER_MODELS` or the interactive picker is not enough to conclude a model is unavailable.
- The bare alias `gpt-5.6` can fail on `openai-codex` even when a concrete GPT-5.6 SKU works.
- For the 2026-07 OpenAI GPT-5.6 family, the public docs exposed these model ids:
  - `gpt-5.6-sol` — flagship / complex reasoning and coding.
  - `gpt-5.6-terra` — quality-cost balance.
  - `gpt-5.6-luna` — cost-sensitive / high-volume workloads.
- In the checked profile, `hermes chat -q 'Ответь одним словом: OK' --provider openai-codex --model gpt-5.6 -Q` returned HTTP 400: the bare `gpt-5.6` model was not supported with the Codex ChatGPT account.
- `hermes chat -q 'Ответь одним словом: OK' --provider openai-codex --model gpt-5.6-sol -Q` succeeded and returned `OK`.

## Recommended verification workflow for new OpenAI/Codex models

1. Load `hermes-agent` plus this provider-selection skill.
2. Check current model config safely without printing secrets.
3. Check Hermes' static model catalog, but treat it only as a hint.
4. Check official model docs or provider model list for exact ids.
5. Smoke-test exact ids without changing the live config:

```bash
hermes chat -q 'Ответь одним словом: OK' --provider openai-codex --model gpt-5.6-sol -Q
```

6. Only after a successful smoke test and user approval, change `model.default` / provider config and restart the gateway if a live Telegram bot is affected.

## Communication note

When reporting to Alexander, separate:

- “visible in Hermes picker/static list” — may be no;
- “usable if passed explicitly by model id” — may be yes;
- “safe to switch production profile now” — requires confirmation because it changes behavior and spend.
