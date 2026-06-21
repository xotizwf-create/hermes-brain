# LLM provider pricing research snapshot — 2026-06-20

This is a condensed session-specific reference for choosing cheap/high-quality Hermes Agent providers. Refresh pricing before spending real money; provider prices, limits, and free tiers change often.

Assumed exchange rate used during the session: **~73 ₽ per $1** from a live USD/RUB lookup around 2026-06-20. Use a fresh rate for future quotes.

## Short recommendation from the session

For Hermes Agent, the best practical stack was:

1. **DeepSeek official API** as the stable cheap paid default.
2. **MiniMax-M3** for long-context or heavier agentic sessions.
3. **OpenRouter `:free` routes / Z.ai GLM free or cheap models / Groq free key** for tests and backups, not sole production capacity.
4. **Kimi/K2** only when its current route price and task quality justify it; it was not the cheapest default in the snapshot.

## Price examples converted to RUB

Approximate prices per 1M tokens from the research snapshot:

- DeepSeek-chat input cache miss: **$0.28 ≈ 20 ₽**
- DeepSeek-chat output: **$0.42 ≈ 31 ₽**
- DeepSeek-reasoner input: **$0.56 ≈ 41 ₽**
- DeepSeek-reasoner output: **$2.19 ≈ 160 ₽**
- MiniMax-M3 input: **$0.30 ≈ 22 ₽**
- MiniMax-M3 output: **$1.20 ≈ 88 ₽**
- GLM-4.5-Air input: **$0.20 ≈ 15 ₽**
- GLM-4.5-Air output: **$1.10 ≈ 80 ₽**
- GLM-4.7-FlashX input: **$0.07 ≈ 5 ₽**
- GLM-4.7-FlashX output: **$0.40 ≈ 29 ₽**
- Groq qwen3-32b input: **$0.29 ≈ 21 ₽**
- Groq qwen3-32b output: **$0.59 ≈ 43 ₽**

## Provider notes

### DeepSeek official

- Best default recommendation in the session for “quality per ruble”.
- Use `deepseek-chat` for daily Hermes work.
- Use `deepseek-reasoner` only when the task needs stronger reasoning; output tokens are much more expensive.

### MiniMax-M3

- Useful for long-context work, large transcripts/files, and long tool sessions.
- More expensive output than DeepSeek-chat but still practical for heavy tasks.

### OpenRouter

- Good as a marketplace and free testing route.
- `:free` models can be great for experiments, but availability and rate limits can shift.
- Enable price sorting if using OpenRouter routing.

### Z.ai / GLM

- GLM Flash/Air models can be cheap or free depending on current account plan.
- Good fallback/test route through an OpenAI-compatible custom provider.

### Groq

- Valuable for speed and free starting quotas.
- Use for Qwen/Llama/GPT-OSS/Kimi variants when current limits and prices fit.

### Kimi/K2

- Strong model family, but in this snapshot it was not the cheapest practical daily default.
- Position as premium fallback unless new pricing changes the economics.

## Hermes configuration patterns

### OpenRouter

```yaml
model:
  provider: openrouter
  default: deepseek/deepseek-chat-v3.2:free

provider_routing:
  sort: "price"
```

### Custom OpenAI-compatible provider

```yaml
custom_providers:
  - name: groq
    base_url: https://api.groq.com/openai/v1
    key_env: GROQ_API_KEY

model:
  provider: custom:groq
  default: qwen3-32b
```

### Fallback routing

```yaml
fallback_providers:
  - provider: deepseek
    model: deepseek-chat
  - provider: custom:groq
    model: qwen3-32b
```

## Visible reasoning/progress

When a Telegram bot “does nothing” while spending tokens, suggest both operational logging and user-visible progress summaries:

- Enable Hermes reasoning display where supported:

```bash
hermes config set display.show_reasoning true
```

- Use chat controls when applicable:

```text
/reasoning show
/reasoning high
```

- Add a bot instruction to publish concise work-log updates: what is being checked, what source/tool is being used, and the current decision. This is not hidden chain-of-thought; it is a user-facing progress summary.

## Future-use checklist

Before making a new recommendation:

1. Refresh provider pricing and free-tier limits.
2. Refresh USD/RUB conversion.
3. Ask whether the target is a production Telegram bot, CLI Hermes, or a dedicated profile.
4. If changing a running bot, test with a real prompt and check logs for token spend + response delivery.
5. If the user asks for visible thinking, configure supported reasoning display and/or progress summaries without exposing hidden chain-of-thought.
