# Albery Bitrix/Hermes model routing pitfall

Use this when Albery Bitrix replies fail with empty output, `Broken pipe`, provider/model errors, or when the owner asks why Gemini/Codex is being used.

## Durable lesson

Albery can have **two different model layers**:

1. The global Hermes runtime config, usually under `/root/.hermes/config.yaml`, which can show `provider: openai-codex` and a Codex model.
2. The Albery application env, usually `/var/www/albery/.env`, whose feature-specific variables can override what a wrapper passes to Hermes or other LLM helpers.

Do not conclude “Codex is configured, so Bitrix uses Codex” from the global Hermes config alone.

## Checks

- Inspect the app env for Bitrix-specific overrides, especially `B24_TESTBOT_MODEL`.
- Inspect nearby backups such as `.env.bak*` and file mtimes to distinguish a fresh change from a legacy env value.
- Search code for the variable that launches the Bitrix wrapper; for Albery this has been handled separately from Zoom/OCR settings.
- Treat `ZOOM_PROCESSING_MODEL`, `GOOGLE_MODEL`, and Google OCR fallback defaults as separate contours unless the failure is in Zoom/OCR processing.
- Redact secrets and never print full env values.

## Interpretation pattern

If `/root/.hermes/config.yaml` is Codex but `/var/www/albery/.env` contains `B24_TESTBOT_MODEL=gemini-...`, the root cause is an app-level Bitrix override/legacy env value, not a global Hermes model switch.

When reporting to Александр, say this plainly: “Codex in the main Hermes config was not replaced; the Bitrix wrapper had a separate app env variable.”
