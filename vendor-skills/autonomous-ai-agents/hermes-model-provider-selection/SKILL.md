---
name: hermes-model-provider-selection
description: Select and configure cost-effective LLM providers for Hermes Agent, including free/cheap OpenAI-compatible APIs, routing, fallbacks, and RUB-aware price comparisons.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, llm-providers, model-routing, openrouter, deepseek, minimax, glm, groq, pricing]
---

# Hermes Model Provider Selection

Use this skill when the user wants to connect, compare, switch, or optimize LLM providers/models for Hermes Agent with emphasis on quality, cost, free tiers, Russian-ruble affordability, OpenAI-compatible endpoints, or agent suitability.

This skill complements the protected `hermes-agent` skill. Load `hermes-agent` first for canonical Hermes commands/config semantics, then use this skill for provider selection and practical routing strategy.

## Triggers

- User asks for the cheapest/free but high-quality model for Hermes.
- User mentions Kimi, DeepSeek, Qwen, GLM/Z.ai, MiniMax, Groq, OpenRouter, Together, Fireworks, local Ollama/vLLM, or custom OpenAI-compatible providers.
- User wants prices in ₽/RUB or asks what is affordable from Russia.
- User wants Hermes to show reasoning/progress while it works.
- User wants fallback providers, auxiliary models, or routing by price/latency.

## Required workflow

1. **Load canonical Hermes docs skill first**
   - Load `hermes-agent` before giving exact Hermes commands.
   - Do not edit `hermes-agent` if it is bundled/protected; put provider-selection lessons here.

2. **Check current facts before recommending**
   - Provider pricing and free tiers change often. Use web research for current prices if the answer affects real spend.
   - Use a live USD/RUB exchange-rate source or a clearly labeled approximate rate.
   - Convert costs per 1M tokens into RUB for the user.

3. **Separate three decisions**
   - **Default daily model**: low-cost, stable, good enough for most Hermes tasks.
   - **Heavy/reasoning model**: higher quality or long-context fallback for hard tasks.
   - **Free/testing route**: OpenRouter/Z.ai/Groq free tiers for experiments, never assumed stable.

4. **Prefer practical Hermes-compatible endpoints**
   - Favor OpenAI-compatible APIs because Hermes can connect them via built-in providers or `custom_providers`.
   - Keep API keys in `~/.hermes/.env`; model/base URL config in `~/.hermes/config.yaml`.
   - Never print or persist real secrets.

5. **Give a small recommendation set, not a huge catalog**
   - Usually provide 2–4 scenarios:
     1. Cheapest stable paid default.
     2. Best long-context/agentic option.
     3. Free/near-free testing route.
     4. Premium fallback for difficult coding/agent tasks.

6. **Verify after configuration when actually changing a system**
   - Run `hermes config check`, `hermes doctor`, and a small `hermes chat -q ...` smoke test when tools/server access are available.
   - Restart gateway/profile if the change affects a running Telegram/Discord/etc. bot.

## Provider selection heuristics

### Strong cheap default

As of the 2026-06 research snapshot in `references/llm-provider-pricing-2026-06-20.md`, DeepSeek official API was the best practical cheap paid default:

```yaml
model:
  provider: deepseek
  default: deepseek-chat
```

Use `deepseek-reasoner` as a heavier reasoning mode when the extra output cost is acceptable.

### Long-context / agentic work

MiniMax-M3 is a strong candidate when Hermes needs very long context, big transcripts/files, or long tool-using sessions:

```yaml
model:
  provider: minimax
  default: MiniMax-M3
```

Warn that thinking/reasoning modes can increase output-token spend.

### Free and experimental route

OpenRouter is usually the easiest way to test many models and free `:free` routes:

```yaml
model:
  provider: openrouter
  default: deepseek/deepseek-chat-v3.2:free

provider_routing:
  sort: "price"
```

Caveat: free routes can be limited, queued, degraded, or removed. For production bots, use them only as testing/fallback, not the only model.

### Z.ai / GLM route

Z.ai can be a cheap/free fallback if GLM Flash/Air models are available on the account:

```yaml
custom_providers:
  - name: zai
    base_url: https://api.z.ai/api/paas/v4/
    key_env: GLM_API_KEY

model:
  provider: custom:zai
  default: glm-4.7-flashx
```

### Groq speed route

Groq is useful as a fast OpenAI-compatible provider for Qwen/Llama/GPT-OSS/Kimi variants:

```yaml
custom_providers:
  - name: groq
    base_url: https://api.groq.com/openai/v1
    key_env: GROQ_API_KEY

model:
  provider: custom:groq
  default: qwen3-32b
```

Treat Kimi K2 via Groq/OpenRouter as a premium fallback unless current prices prove otherwise.

## Reasoning/progress visibility for Telegram bots

Do not promise raw hidden chain-of-thought. Many providers do not expose it, and Hermes should not fabricate it.

Offer two practical layers:

1. Enable display of model reasoning when Hermes/provider supports it:

```bash
hermes config set display.show_reasoning true
```

In chat:

```text
/reasoning show
/reasoning high
```

2. Add a user-facing progress-log instruction for bots:

> While working, periodically publish a concise human-readable work log: what you are checking, which option you are comparing, and what decision follows. Do not reveal hidden chain-of-thought; summarize actions and rationale.

This gives the user visible progress without relying on provider-specific hidden reasoning output.

## Config patterns

### OpenRouter with price routing

```yaml
model:
  provider: openrouter
  default: <model-id>

provider_routing:
  sort: "price"
```

### Named custom provider

```yaml
custom_providers:
  - name: provider_name
    base_url: https://example.com/openai/v1
    key_env: PROVIDER_API_KEY

model:
  provider: custom:provider_name
  default: model-name
```

### Fallbacks

```yaml
fallback_providers:
  - provider: deepseek
    model: deepseek-chat
  - provider: custom:groq
    model: qwen3-32b
```

### Cheap auxiliary models

If the default model is expensive, explicitly configure auxiliary tasks to cheaper models so summarization/extraction/compression do not burn premium tokens:

```yaml
auxiliary:
  web_extract:
    provider: openrouter
    model: google/gemini-2.5-flash
  compression:
    provider: openrouter
    model: google/gemini-2.5-flash
```

## Pitfalls

- Do not equate “free” with production-ready. Free model routes often have request/day limits, queues, changing availability, or lower reliability.
- Do not assume Kimi is the cheapest high-quality option. It may be strong but often belongs in premium fallback, depending on current route pricing.
- Do not bury the recommendation in a giant provider catalog; lead with the suggested stack and then show alternatives.
- Do not save API keys, tokens, account IDs, or billing data in skills or references.
- Do not quote old prices as current. If making a spend decision, refresh pricing first.

## References

- `references/llm-provider-pricing-2026-06-20.md` — research snapshot from the session comparing DeepSeek, MiniMax, OpenRouter, Z.ai/GLM, Groq, Kimi, Qwen, Together, and Fireworks for Hermes Agent.