# VK bridge latency and allowlist diagnostics

Use this when a VK user is added to bot access or complains that replies are very slow.

## Durable lessons

- Check the real allowlist key used by the bridge, not only the legacy singular key. The bridge may support both `VK_ALLOWED_USER_ID` and `VK_ALLOWED_USER_IDS`; the active multi-user configuration is usually `VK_ALLOWED_USER_IDS`.
- Resolve a VK short link / screen name to numeric user id with the VK API, then verify that numeric id is present in the effective allowlist. Profile names alone are not what the bridge authorizes.
- After editing allowlist/config, restart only the VK bridge service and then verify: service active, health endpoint ok, and logs no longer show `Ignored non-allowlisted user` for that numeric id.
- For latency complaints, separate VK delivery time from Hermes processing time. VK Callback API can deliver quickly while the bridge is slow because it starts/queues Hermes work.
- Add or check per-request timing logs: callback received, Hermes response started, Hermes response finished/sent. Without request-correlated timestamps, service restarts can make old "start" and later "answer" lines look related when they are not.

## Common slow-answer causes in this MVP bridge

- The bridge launches Hermes work per VK answer instead of running as a first-class gateway like Telegram.
- A single serialized queue means one long Hermes response blocks later VK messages.
- VK has no response streaming/typing experience equivalent to the owner seeing Hermes work in Telegram.
- Small servers with about 1 GB RAM and swap pressure make process startup and large contexts visibly slower.

## Reporting pattern

Tell the owner explicitly:

- whether the VK profile was resolved to a numeric id;
- whether that id is in the active allowlist;
- whether the service was restarted/healthy after the change;
- whether logs show ignored messages before or after the restart;
- the likely latency cause and the practical next fix.

Avoid claiming that VK itself is slow unless the timing logs prove VK callback delivery is delayed. In this MVP, the usual bottleneck is Hermes processing/queueing behind the bridge.