# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

# albery
- **albery** (`.claude/skills/albery/SKILL.md`) — очередь задач Albery в Битриксе (тег `Claude`):
  выполнить, написать результат в задачу, закрыть, прислать мини-отчёт в Telegram.
  Триггер: `/албери` (кириллицей) или `/albery`.
When the user types `/албери` or `/albery`, invoke the `albery` skill (Skill tool, name `albery`)
before doing anything else. Имя скилла латиницей — слэш-команды не принимают кириллицу,
поэтому кириллический триггер маршрутизируется через это правило.
