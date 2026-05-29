---
id: optimization
type: engineering
tags: [performance,caching,tuning]
updated: 2026-05-29
secret_refs: []
---

# Optimization Standards

Use this guide for performance work across backend, database, frontend, and infrastructure.

## Workflow

1. Define the bottleneck with evidence: timing, logs, traces, query plans, bundle size, or user-visible symptom.
2. Make the smallest change that targets the bottleneck.
3. Measure before and after using the same method.
4. Keep correctness tests in place while optimizing.
5. Document the tradeoff if the optimization adds complexity.

## Database

- Use `EXPLAIN` or `EXPLAIN ANALYZE` for slow SQL.
- Add indexes for proven query paths, not speculative ones.
- Watch for N+1 queries, unbounded result sets, and missing pagination.
- Cache only after query and schema issues are understood.

## Backend

- Avoid global caches that can return stale user-specific data.
- Put timeouts around external API calls.
- Batch independent remote calls when the provider supports it.
- Log enough context to debug latency without logging secrets.

## Frontend

- Optimize actual user paths first.
- Avoid unnecessary client-side work for data that can be prepared server-side.
- Keep loading, empty, and error states fast and predictable.
- Verify responsive behavior after layout changes.
