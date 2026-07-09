# Albery Bitrix/Hermes model routing and timeout pitfall

Use this when Albery Bitrix replies fail with empty output, `Broken pipe`, provider/model errors, `Операция превысила лимит ... сек`, very slow simple requests, or when the owner asks why Gemini/Codex is being used.

## Durable lessons

Albery can have **two different model layers**:

1. The global Hermes runtime config, usually under `/root/.hermes/config.yaml`, which can show `provider: openai-codex` and a Codex model.
2. The Albery application env, usually `/var/www/albery/.env`, whose feature-specific variables can override what a wrapper passes to Hermes or other LLM helpers.

Do not conclude “Codex is configured, so Bitrix uses Codex” from the global Hermes config alone.

A slow Bitrix answer is not automatically a slow database/MCP tool. The wrapper may launch a full `hermes -z ... --continue <session> -t <toolset> --yolo` turn for a very small user request. That turn can include a large system prompt, injected recent history, session continuation, a full MCP tool list, and mandatory “start_here” tool instructions. If the model backend silently stalls inside that turn, the outer Bitrix timeout can make a simple request look like a 300–600s MCP failure.

## Checks

- Inspect the app env for Bitrix-specific overrides, especially `B24_TESTBOT_MODEL`, `B24_TESTBOT_HERMES_TIMEOUT`, `B24_TESTBOT_HISTORY_TURNS`, `B24_HERMES_MAX_CONCURRENCY`, `B24_HERMES_QUEUE_WAIT_S`, and `B24_CORE_TOOLSET`.
- Inspect nearby backups such as `.env.bak*` and file mtimes to distinguish a fresh change from a legacy env value.
- Search code for the variable that launches the Bitrix wrapper; for Albery this has been handled separately from Zoom/OCR settings.
- Treat `ZOOM_PROCESSING_MODEL`, `GOOGLE_MODEL`, and Google OCR fallback defaults as separate contours unless the failure is in Zoom/OCR processing.
- Redact secrets and never print full env values.
- Before blaming Bitrix, DB, or MCP, run a layered timing check:
  - server resources/load/memory/swap;
  - VPN/OpenAI reachability;
  - bare `hermes -z 'Ответь ровно: OK' --yolo`;
  - the same with `-t albery-faq`;
  - the same with the failing agent toolset such as `-t agent-agent-sklad` or `-t agent-agent-razrabotchik`.
- Inspect recent Hermes request dumps under `/root/.hermes/sessions/request_dump_*.json` without exposing secrets. Useful evidence: request size, prompt length, tool count/names, tool outputs, and `error.message` entries such as “Non-streaming API call timed out after 90s with no response”.
- Inspect `bitrix_bot_interactions` for status, question length, answer length, and exact user-visible timeout/error messages; do not infer from chat text alone.

## Interpretation pattern

If `/root/.hermes/config.yaml` is Codex but `/var/www/albery/.env` contains `B24_TESTBOT_MODEL=gemini-...`, the root cause is an app-level Bitrix override/legacy env value, not a global Hermes model switch.

If a direct list/read operation is fast but the Bitrix agent says the same request hit a 300–600s timeout, the root cause is usually the **agent wrapper path**, not the underlying data source. Look for:

- over-large prompt/history + full toolset for a simple service query;
- `--continue` used together with manually injected history;
- mandatory first-tool behavior causing extra tool calls;
- model backend silent stalls/retries;
- an outer timeout that is much larger than the model no-event timeout.

When reporting to Александр, separate the layers plainly:

- “Список/БД читается быстро.”
- “Сервер и сеть сейчас живые.”
- “Зависает полноценный агентский прогон Hermes/Codex, который запускается вокруг простого вопроса.”
- “Для служебных запросов нужен быстрый прямой путь или короткий timeout/fallback, а не 600-секундный чатовый ход.”

## AI-lawyer / heavy document-generation add-on

For Albery Bitrix «Агент-юрист» failures while drafting contracts or official documents, use the dedicated note `references/albery-bitrix-legal-document-timeouts.md`. Durable lesson: a user-visible “10 minute limit” may actually be two guarded Hermes/LLM attempts failing earlier with `Broken pipe`; the fix is usually slimming the lawyer connector and moving document generation to a background job, not merely increasing `B24_TESTBOT_HERMES_TIMEOUT`.

## Safer design for simple Bitrix service questions

For questions like “какие агенты есть?”, “кто активен?”, “статус агентов?”, avoid routing through a full creative/reasoning turn if the answer is deterministic.

Prefer:

1. A direct read-only backend/MCP/database path for known service intents.
2. A short chat timeout for normal synchronous answers (tens of seconds, not 600s).
3. Background execution for long document/table/report jobs.
4. Provider/model fallback when Codex produces no stream/no events for the backend timeout window.
5. A friendly short user message that distinguishes “long job moved to background” from “AI backend temporarily stalled”.
