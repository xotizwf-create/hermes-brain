# Watch-only HH vacancy digest with owner feedback

Session learning from 2026-06-12: Александр wants HH vacancy monitoring for AI-agent / AI-automation roles as a **candidate feed**, not an auto-apply system.

## Operating mode

- Send only new, deduplicated vacancies; stay silent when there are no new matches.
- Александр applies manually himself. Do not draft/send applications unless he later asks for a specific vacancy.
- Treat Telegram replies as training feedback for the filter:
  - `1 норм`, `полезно`, `ищи больше таких` → increase weight for that vacancy’s title/keywords/domain.
  - `не норм`, `это продажи`, `слишком менеджерская`, `1С`, `поддержка`, `маркетинг`, `DS/ML` → add or strengthen exclusion rules.
  - If feedback names a concrete pattern, update the watcher query/exclusion list and document it.
- Initial watcher setup may seed current search results as already seen so future digests contain genuinely new vacancies rather than a large repeated first batch.

## Delivery and cron hygiene

- Delivery target for this watcher is the Telegram group `Уведомления` (`telegram:-5120862157`).
- If replacing an older auto-apply/digest cron, explicitly pause the old jobs before reporting completion to avoid duplicate notifications or accidental auto-applications.
- Verify cron state after changes: new watch-only job enabled, legacy auto-apply jobs paused, delivery target correct.

## Good final report

State clearly:

- no auto-apply is enabled;
- watcher frequency;
- delivery target;
- silence-on-no-new behavior;
- how Александр can give feedback and what you will do with it.
