# Hermes Vault — per-project secret manager (web UI)

A small, dependency-free web UI to store project secrets and tie them to GitHub repos. Lives only on
the server; the agent reads the same store. Built 2026-05-30; first live instance = `andigital`.

## What it is
- `secrets_ui.py` — stdlib-only (no pip) HTTP app. Lists the owner's GitHub repos, lets them store/edit
  a `.env` per project. Values live under `/opt/hermes/secure/projects/<slug>/.env`.
- Served at `https://<domain><base_path>/<url_token>/` — e.g. `https://www.andigital.ru/andigital/secret/<token>/`.

## Security model
- **Two factors:** (1) unguessable `url_token` in the path (wrong/missing → 404), (2) password stored
  only as a **scrypt** hash. After login: HMAC-signed `httponly`+`Secure`+`SameSite=Strict` session
  cookie (1h). CSRF token on every mutating form. Per-IP login lockout (6 fails → 5 min).
- **Least privilege:** runs as `hermesvault` (no root, `nologin`), bound to `127.0.0.1:8787`, behind
  nginx TLS. systemd hardening (`ProtectSystem=strict`, `ProtectHome`, `ReadWritePaths` = only the
  secure store + its data dir, syscall filter). If the app is popped, the attacker is not root.
- **Shared store:** `/opt/hermes/secure/projects` is `2770 hermesvault:hermessec` (setgid); the agent
  runs as root (in `hermessec`) and reads/writes the same files (660). Real secrets never enter git.
- nginx `access_log off` on the location → the URL token is not written to logs.

## Where things live (server)
| Thing | Path | Perms |
|---|---|---|
| App code | `/opt/hermes/vault/secrets_ui.py` | 640 root:hermessec |
| Config (token, scrypt hash, session secret) | `/opt/hermes/vault/data/config.json` | 600 hermesvault |
| GitHub token (for the repo list) | `/opt/hermes/vault/data/gh_token` | 660 |
| Public URL (delivered to the owner) | `/opt/hermes/vault/data/PUBLIC_URL.txt` | 640 |
| Secret store (shared with the agent) | `/opt/hermes/secure/projects/<slug>/.env` | 660, dir 2770 |
| systemd unit | `/etc/systemd/system/hermes-vault.service` | — |
| nginx location | in the domain's TLS server block (`nginx-location.conf`) | — |

Canonical source of all of the above is this brain dir; deploy = copy to `/opt` (below).

## First-run / operate
- **Set the password:** open the secret URL (in `PUBLIC_URL.txt`, delivered to the owner's PC, never
  via chat) → first-run page → set a password (≥10 chars). Done. Subsequent visits: URL + password.
- **Use:** dashboard lists GitHub repos; click one → see variable NAMES → "Редактировать значения" →
  paste/edit `KEY=VALUE` lines → save. "Добавить проект вручную" for non-repo projects.
- **Restart / logs:** `systemctl restart hermes-vault`; `journalctl -u hermes-vault` (no secrets logged).
- **Rotate the URL token:** `runuser -u hermesvault -- env VAULT_CONFIG=/opt/hermes/vault/data/config.json
  python3 /opt/hermes/vault/secrets_ui.py set-url-token` → writes a new URL (stdout); update nginx is
  not needed (base path unchanged), redeliver the new URL to the owner.
- **Reset the password:** edit `config.json` → set `"password": null` (as hermesvault) → restart → the
  first-run page lets you set a new one.

## Install on a fresh server (turnkey — for resale)
Nothing is hardcoded to andigital except `config.json` + the nginx `base_path`. Steps:
```bash
# 1. user + dirs
groupadd -f hermessec
useradd --system --no-create-home --shell /usr/sbin/nologin -g hermessec hermesvault
usermod -aG hermessec root
install -d -m750 -o root -g hermessec /opt/hermes
install -d -m2770 -o hermesvault -g hermessec /opt/hermes/secure /opt/hermes/secure/projects
install -d -m2750 -o root -g hermessec /opt/hermes/vault
install -d -m2770 -o hermesvault -g hermessec /opt/hermes/vault/data
# 2. code + github token + config (token written to data only)
install -m640 -o root -g hermessec skills/secure-access/vault/secrets_ui.py /opt/hermes/vault/
install -m660 -o hermesvault -g hermessec <your-gh-token-file> /opt/hermes/vault/data/gh_token
runuser -u hermesvault -- env VAULT_CONFIG=/opt/hermes/vault/data/config.json \
  python3 /opt/hermes/vault/secrets_ui.py init --base-path /<brand>/secret --instance <brand> --port 8787
# 3. service
cp skills/secure-access/vault/hermes-vault.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now hermes-vault
# 4. nginx: add nginx-location.conf into the domain's 443 server block (match base_path), nginx -t, reload
#    keep backups OUT of sites-enabled/ (nginx includes that dir → duplicate-config errors).
```
Per-client branding = the `init` flags + the nginx `base_path`. The GitHub token is per-client (their
account). One codebase, many instances.
