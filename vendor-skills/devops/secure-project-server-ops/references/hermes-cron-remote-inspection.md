# Remote Hermes Cron Inspection Pattern

Use this reference when the owner asks to connect to a project server and inspect which Hermes Agent scheduled jobs / cron automations are enabled.

## Goal

Produce an operational summary of enabled Hermes automations without changing the server and without exposing secrets.

## Safe sequence

1. Load `secure-project-server-ops` and the relevant top-level project operations skill/runbook.
2. Read non-secret project docs or Hermes Brain pointers for:
   - active server / project slug;
   - Hermes home path;
   - service names;
   - secure credential reference.
3. Parse the local secure env file by key/value without printing values. Do **not** assume exact key names such as `Host_IP`; inspect available key names and map common variants like `IP`, `USER`, `PASSWORD`.
4. Connect using credentials only through process environment/in-memory variables, never visible command arguments.
5. Run read-only preflight first:
   - hostname;
   - CPU/RAM/swap/load/disk;
   - `systemctl` status for Hermes gateway;
   - Hermes CLI path/version/home if available.
6. Inspect Hermes scheduled jobs with `hermes cron list` when available, and read `/root/.hermes/cron/jobs.json` (or the configured Hermes home equivalent) for structured fields.
7. For each job, summarize only safe fields:
   - name and active/enabled state;
   - schedule and timezone if inferable;
   - next run / last run / status;
   - delivery target at a high level;
   - script name and mode (`no_agent` vs agent-run);
   - short human description derived from prompt/script preview, with secrets and URLs redacted.
8. If a job uses a script, preview the script only after redacting env assignments, tokens, passwords, connection strings, and URLs. Do not dump full prompts unless explicitly requested.
9. Optionally list related system cron files separately and label them clearly as **not Hermes scheduled jobs**.
10. When migrating project report automations from a local fallback agent back to the production project agent, verify the production jobs and delivery destination first, then pause the local fallback jobs. Include any local recovery/watchdog job that can re-enable the fallback automations; otherwise duplicate reports may return after the next health-check tick. Do not manually run report-generation jobs just to test routing — use a model ping and a harmless Telegram `getChat`/test message instead.
11. Final answer should be natural and concise, without the `Готово:` prefix, and emphasize: connected, Hermes found/running, cron jobs listed, no server changes made.

## Useful read-only remote probes

```bash
hostname
free -m
uptime
 df -Pm / /root 2>/dev/null || df -Pm /
systemctl list-units --type=service --all --no-pager | grep -Ei 'hermes|gateway|agent' || true
systemctl status hermes-gateway.service --no-pager -l 2>/dev/null || true
command -v hermes || true
hermes --version 2>/dev/null || true
hermes cron list 2>/dev/null || true
python3 - <<'PY'
from pathlib import Path
import json
p = Path('/root/.hermes/cron/jobs.json')
print(p if p.exists() else 'jobs.json not found')
if p.exists():
    data = json.loads(p.read_text())
    jobs = data.get('jobs', data if isinstance(data, list) else [])
    if isinstance(jobs, dict):
        jobs = list(jobs.values())
    for j in jobs:
        print('---')
        for k in ['id','name','enabled','schedule','repeat','deliver','script','no_agent','last_run_at','last_status','next_run_at']:
            if isinstance(j, dict) and k in j:
                print(f'{k}: {j[k]}')
PY
```

## Communication template

```text
Подключился к серверу <project>, Hermes найден и работает.

Включённые Hermes cron-автоматизации:

1. <name>
- Статус: включена
- Расписание: <schedule>
- Следующий запуск: <next>
- Последний запуск: <last/status>
- Как работает: <1-3 bullets>

Дополнительно увидел системные cron: <...>. Это не Hermes Scheduled Jobs.

Секреты не выводил, ничего на сервере не менял — только read-only проверка
```
