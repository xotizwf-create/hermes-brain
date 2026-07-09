# Albery Bitrix AI-lawyer contract-generation timeouts

Use this note when Albery’s Bitrix subagent «Агент-юрист» fails while drafting a contract/document, especially when the user sees a generic 10-minute/600-second timeout or a friendly “ИИ временно сбоит” reply.

## Symptom pattern

- User sends a substantial legal-document request in Bitrix (contract terms, parties, реквизиты, sums, acts, compensation text, etc.).
- The Bitrix bot returns a short fallback such as “Что-то временно сбоит…” or “Операция превысила лимит … сек”.
- `bitrix_bot_interactions` may show `status='ok'` because the fallback was delivered, even though the underlying Hermes/LLM run failed.
- Actual latency can be shorter than the configured 600s: two guarded attempts at ~6–7 minutes each can look like a “10 minute limit” to the user.
- Journal evidence often contains `b24 testbot: hermes run failed (attempt 1/2)` and `(attempt 2/2)` with an LLM sentinel/connection error such as `Broken pipe`.

## Diagnosis checklist

1. Read the Albery project card first (`projects/albery/servers.md`, `deploy.md`) and use the secure project env for access; do not trust stale host guesses.
2. Check service health/resources before heavy commands: `systemctl status albery`, `free -m`, `df -h`, load/processes.
3. Inspect the application journal around the user’s request time:
   - `journalctl -u albery --since '<time>' --until '<time>' --no-pager`
   - look for `hermes run failed`, `Broken pipe`, `hermes timed out`, `slot wait exceeded`.
4. Query `bitrix_bot_interactions` for the exact window. Useful fields: `id`, `created_at`, `dialog_id`, `agent_slug`, `status`, `latency_ms`, `char_length(question)`, `char_length(answer)`, `answer`, `error`.
5. Check the agent row in `agents`: displayed name, historical `slug`, `tier`, `tools`, `tools_customized`, `bitrix_bot_id`, and connected skills via `agent_selected_knowledge`.
6. Inspect `B24_TESTBOT_HERMES_TIMEOUT`, `B24_TESTBOT_HISTORY_TURNS`, `B24_CORE_TOOLSET`, `B24_EXTRA_TOOLSETS`, retry/backoff env, and the wrapper code that builds the `hermes -z ... -t agent-<slug>` command.
7. Distinguish the real failure layer:
   - app/proxy timeout;
   - queued/concurrency wait;
   - Hermes CLI timeout;
   - LLM/provider connection failure (`Broken pipe`, retries, no events);
   - oversized prompt/tool schema/history for a document task.

## Interpretation

Do **not** fix contract-generation failures by only raising `B24_TESTBOT_HERMES_TIMEOUT`. If the logs show `Broken pipe` during the guarded Hermes attempts, the request is failing inside the LLM/provider path, not because nginx or Bitrix forcibly killed the HTTP request at exactly 600s.

For AI-lawyer contract generation, the common durable root cause is an overly heavy synchronous turn:

- large Bitrix wrapper/system prompt;
- recent chat history injected into the prompt;
- legal drafting skill text;
- broad agent MCP tool schema list;
- one-shot expectation that the model drafts full legal HTML and calls `export_document` before the Bitrix reply returns.

## Recommended fix order

1. **Slim the lawyer agent first.** Keep only tools needed for legal-document work: instruction/capability/context tools, attachment/history reading, company knowledge if needed, URL fetch if needed, and `export_document`. Remove unrelated Sheets/Drive-folder/Zoom/task/webapp tools from the lawyer connector.
2. **Tighten the lawyer role/instructions.** Contract/doc requests should prefer a minimal pipeline: extract fields → produce structure → build HTML → call `export_document` once. Avoid broad web research unless the user explicitly asks or a missing legal/source issue requires it.
3. **Move long document jobs to background.** The Bitrix handler should acknowledge immediately (“Принял, готовлю документ, пришлю файл сюда”) and run generation in a background job that posts the file/result back to the same dialog. This avoids holding a synchronous Bitrix/Hermes turn for many minutes.
4. **Split generation into restartable stages.** Save extracted fields and intermediate HTML/job state so a failed document-render or LLM step can be retried without rerunning the full request.
5. **Mask sensitive data in logs.** Legal requests often contain passport, INN, bank details, accounts, phone/email. Avoid storing raw full реквизиты in `bitrix_bot_interactions` or redact them before persistence.
6. **Improve failure reporting.** User-facing fallback should distinguish: queued/busy, background job accepted, LLM/provider connection failure, and true timeout. Logs should retain enough non-secret metadata to diagnose prompt/tool size and failure layer.

## Reporting style to Александр

Report layers separately and with evidence:

- configured outer limit (e.g. `B24_TESTBOT_HERMES_TIMEOUT=600`);
- observed actual latency from `bitrix_bot_interactions`;
- journal error markers (`Broken pipe`, attempts 1/2 and 2/2);
- agent configuration (tool count, connected skill size, historical slug/display name);
- recommended fix (slim connector + background document workflow), not just “increase timeout”.

Avoid dumping personal реквизиты from the failed request back into chat; summarize them as “legal request with реквизиты/sums/service description”.
