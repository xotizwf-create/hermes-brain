---
name: himalaya
description: "Himalaya CLI: ЧТЕНИЕ почты (IMAP) с терминала. ВАЖНО: на этом сервере отправка через himalaya НЕ РАБОТАЕТ - исходящий SMTP заблокирован хостером; для отправки писем используй скилл send-email (Gmail API)."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)
- `references/legacy-word-attachment-extraction.md` (recovering text from old `.doc`/OLE or inline `application/octet-stream` attachments)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### Gmail → Telegram: find a message by person/date, read it, and forward attachments

Use this workflow when Александр asks in Russian to find a Gmail message like “Гузель писала вчера, скинь полное сообщение со вложением в этот чат”. Default to the configured Gmail account unless he names another mailbox.

1. Determine the date in Moscow time when the user uses relative words like “вчера”:
   ```bash
   TZ=Europe/Moscow date '+%Y-%m-%d %H:%M:%S %Z; yesterday=%Y-%m-%d' -d 'yesterday'
   TZ=Europe/Moscow date '+today=%Y-%m-%d'
   ```

2. Confirm Himalaya and folders if needed:
   ```bash
   himalaya account list --output json
   himalaya folder list --output json
   ```

3. Search both `INBOX` and `[Gmail]/All Mail`. Prefer Latin transliteration for IMAP search if Cyrillic search fails with “Could not parse command”:
   ```bash
   himalaya envelope list --folder INBOX --page-size 20 --output json date 2026-05-31 and from Guzel order by date desc
   himalaya envelope list --folder '[Gmail]/All Mail' --page-size 20 --output json date 2026-05-31 and from Guzel order by date desc
   ```
   Also list all messages for that date if the person search is uncertain:
   ```bash
   himalaya envelope list --folder INBOX --page-size 20 --output json date 2026-05-31 order by date desc
   ```

4. Read the selected message with useful headers and preview mode:
   ```bash
   himalaya message read --folder INBOX --preview -H From -H To -H Date -H Subject <id>
   ```

5. Download attachments even if the envelope says `has_attachment:false`. Gmail/Himalaya may still show an attachment marker in the message body (`<#part ... filename=...>`):
   ```bash
   mkdir -p /tmp/gmail_message_<id>_attachments
   himalaya attachment download --folder INBOX --downloads-dir /tmp/gmail_message_<id>_attachments --output json <id>
   ```

6. Inspect downloaded files and normalize odd filenames before sending to Telegram. Tabs or broken punctuation in MIME filenames can make Telegram delivery ugly:
   ```bash
   python3 - <<'PY'
   from pathlib import Path
   root = Path('/tmp/gmail_message_<id>_attachments')
   for p in root.rglob('*'):
       if p.is_file():
           print(p, p.stat().st_size)
   PY
   ```
   If needed, copy to a clean `/tmp/...` filename and send that path as `MEDIA:/tmp/clean_name.ext`.

7. Final response to Александр: include sender, recipient, date, subject, full visible message body, and each attachment as a native Telegram media/file line:
   ```text
   MEDIA:/tmp/clean_attachment_name.docx
   ```

Pitfalls for this workflow:
- Do not trust `has_attachment:false` alone; always try `attachment download` if the body contains a part marker or the user asked for attachments.
- `message read --preview` can inline binary `application/octet-stream` parts, producing multi-megabyte mixed text/binary output. Save it for context, but extract attachments separately; for old Word/OLE `.doc` files use LibreOffice/soffice first and `strings -el -n 2` as a fallback (see `references/legacy-word-attachment-extraction.md`).
- For forwarded commercial-offer requests, do not summarize only the visible email body. If the body says «согласно прилагаемой спецификации», extract the attachment/specification, recover product rows and links, then hand off to the relevant «Простые поставки» КП workflow (see `prostye-postavki-price-lookup/references/commercial-offers-from-email-specs.md`).
- Cyrillic IMAP search terms can fail; retry with email address, Latin transliteration, date-only listing, or `[Gmail]/All Mail`.
- Message IDs are folder-relative; use the ID from the folder you will read/download from.
- Avoid exposing tool names, raw paths, command output, or technical errors in the chat; send only a short human status while working and the final email content.

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
