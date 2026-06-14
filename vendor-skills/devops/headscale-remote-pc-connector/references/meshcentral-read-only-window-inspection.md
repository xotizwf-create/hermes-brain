# MeshCentral read-only window inspection

Use this when Александр asks to connect to his PC and say what is currently open. The goal is a consent-based, read-only inspection: list visible window titles first, without clicking, typing, screenshots, file reads, uploads/downloads, or settings changes.

## Safety rules

- Use only the known owner PC/device and only for the exact owner request.
- If MeshCentral local consent prompts appear on the PC, wait for the user/PC owner to approve. Do not bypass consent.
- Prefer listing window titles before taking a screenshot. Screenshot only if the user explicitly asks or if titles are insufficient.
- Do not print MeshCentral URL keys, passwords, device tokens, session keys, or invite links.
- Do not disclose private message contents beyond practical window/app titles unless the user asked for a visual description and the content is necessary.

## Lightweight preflight

Before remote actions, check that the MeshCentral path is alive and the host is not overloaded. Keep it light on memory-constrained production hosts.

Required services for this setup:

- `meshcentral.service`
- `andigital-pc-gate.service`
- `nginx`

## MeshCtrl path

MeshCentral includes the CLI at:

```bash
node /opt/meshcentral/node_modules/meshcentral/meshctrl.js
```

The admin credential file is stored outside docs/skills. Read it only inside the command wrapper and never echo values. For local CLI access, prefer the internal websocket URL:

```text
ws://127.0.0.1:3001
```

`wss://127.0.0.1:3001` can fail because this deployment is TLS-offloaded by nginx; the local MeshCentral listener is plain websocket.

## Device discovery

Use `ListDevices` to confirm the owner PC is online. For the current personal PC, the known device name is `DESKTOP-FSKTPR4`; do not hard-code the device id in the skill because it may change after reinstall.

A good output has `conn = 1` and `pwr = 1`.

## Window-title inspection technique

Use `RunCommand --powershell --runasuser --reply` with a PowerShell script that:

1. Uses `EnumWindows`, `IsWindowVisible`, `GetWindowTextW`, and `GetWindowThreadProcessId` from `user32.dll`.
2. Keeps only visible windows with non-empty titles.
3. Includes the process name and title.
4. Encodes each title as UTF-8 Base64 before returning it.

Why Base64: raw Russian/Cyrillic window titles can arrive through MeshCtrl with mojibake. Base64 each title separately to avoid truncation and decoding problems from one huge JSON line.

Output format recommendation from the remote script:

```text
<ProcessName>\t<Base64Utf8WindowTitle>
```

Then decode locally and summarize into a clean numbered/bulleted list for Александр.

## Active window caveat

A separate foreground-window probe may return noisy output if the MeshCtrl reply includes extra service text. If the visible-window list is enough for the owner’s request, do not keep retrying and do not disturb the PC with repeated probes.

## Final response style

Keep the final answer practical and natural, without the `Готово:` prefix:

- state whether the PC is online;
- list the visible apps/windows in Russian-friendly names;
- explicitly say no clicks/typing/file actions were performed;
- offer screenshot/visual description only as the next step if needed.
