---
name: apple-macos-personal-tools
description: "Use when operating Apple/macOS personal-information tools: Notes, Reminders, iMessage/SMS, Find My, and GUI computer-use automation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [apple, macos, notes, reminders, imessage, findmy, computer-use]
    related_skills: []
---

# Apple/macOS Personal Tools

## Overview

Class-level playbook for user-facing Apple ecosystem tasks on macOS. Treat the Apple apps as one personal-information domain: discover tool availability, verify target account/device/list/chat, make the smallest safe change, then read back the result.

## When to Use

- Apple Notes: create, search, edit, append, or summarize notes through memo-style CLIs.
- Apple Reminders: add/list/complete reminders, especially date-aware reminders.
- Messages/iMessage/SMS: send or read messages through `imsg`-style CLIs.
- Find My: locate Apple devices/AirTags from the local macOS account.
- macOS GUI/computer-use automation where Apple app state matters.

## General Workflow

1. Confirm this environment is macOS and the app/tool exists (`uname`, `command -v`, or the configured MCP/tool).
2. Prefer read-only discovery first: list accounts, folders/lists/devices/chats before mutating.
3. Resolve ambiguous names explicitly (note title, reminder list, contact, device label).
4. For sends/completions/deletions, show the exact target and final text/action before doing it unless the user has already been specific.
5. Verify by reading back the created/changed item or latest state.

## Subdomains

### Notes

Search before creating duplicates. Preserve existing formatting when appending. If a note title is ambiguous, list candidates and ask once.

### Reminders

Normalize dates with timezone awareness. Prefer the user's default list only when they did not name a list and the tool exposes a default.

### Messages

Do not guess recipients from nicknames when multiple contacts match. Send message text verbatim after confirmation.

### Find My

Treat locations as sensitive. Report only the needed device state and timestamp; do not over-share coordinates unless requested.

### macOS Computer Use

Use GUI automation only when APIs/CLIs are unavailable. After clicking/typing, verify visible state or app output.

## Pitfalls

- Assuming Linux container state reflects the user's Mac; always probe the live macOS target.
- Editing an Apple Note by title without checking duplicates.
- Sending iMessage/SMS to a fuzzy contact match.
- Reporting stale Find My locations without their timestamp.

## Verification Checklist

- [ ] Tool/app availability checked.
- [ ] Target account/list/contact/device resolved.
- [ ] Side effects confirmed or unambiguous.
- [ ] Result read back after the change.
