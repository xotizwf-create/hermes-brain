---
id: gov-exams-app-incidents
type: project
project: gov-exams-app
tags: [incidents]
updated: 2026-05-31
secret_refs: []
---

# Лёгкие экзамены / LiteExams — incidents

- 2026-05-30/31: Server-side Node/Vite work previously caused production OOM and DB connection drops, leading to user-facing token/device-binding issues. Standing rule: no heavy builds/tests/migrations on prod without preflight and safe memory budget; prefer off-server builds.
