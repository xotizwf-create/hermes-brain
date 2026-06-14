# Albery Bitrix REST dispatch troubleshooting

Use this as a concise case note for Albery Zoom → Bitrix task dispatch failures.

## Symptom

- `dispatch_zoom_operational_tasks(confirm=true)` times out at the MCP client layer (120s).
- `list_pending_zoom_operational_dispatches` still shows the same calls.
- `search_tasks(query="Итоги созвона", date_from=..., date_to=...)` returns no created tasks.

## Safe triage pattern

1. Do **not** retry blindly after a timeout.
2. First verify whether side effects happened:
   - pending queue still contains the call?
   - Bitrix search has tasks titled `Итоги созвона` for the date?
3. If no tasks were created and the call is still pending, inspect the production app logs around the attempt, redacting URLs/tokens/secrets.
4. For Albery, `journalctl -u albery --since ...` can reveal the real internal error even when the MCP client only reports a timeout.

## Known durable error class

Bitrix may return:

```text
RuntimeError: tasks.task.add: HTTP 401 {"error":"ACCESS_DENIED","error_description":"REST is available only by subscription."}
```

This means task creation reached Bitrix, but Bitrix rejected REST access because the portal tariff/subscription does not allow REST. This is not a prompt/report formatting issue and not a recipient-matching issue.

## User-facing explanation

Say plainly:

- tasks were not created;
- queue is still open, so it can be retried later without duplicates;
- Bitrix rejected `tasks.task.add` because REST is only available by subscription;
- action needed: restore/enable Bitrix REST subscription/tariff, then retry dispatch.

Avoid dumping webhook URLs, path tokens, `.env` values, or full command output.
