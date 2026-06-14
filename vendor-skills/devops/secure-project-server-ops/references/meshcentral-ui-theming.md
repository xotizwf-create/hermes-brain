# MeshCentral UI theming without weakening security

Use this reference when the owner complains that MeshCentral looks old/cheap after login and asks for the internal panel to match the Andigital/Vault style.

## Durable lesson

MeshCentral already loads `public/styles/custom.css` and `public/scripts/custom.js` on the web UI. Prefer these official custom static hooks for visual polish instead of editing large templates or MeshCentral control logic.

This is a cosmetic layer only. It may style:

- native login shell;
- masthead/header and title area;
- sidebar icons/menu;
- devices page hero/card/list/toolbar;
- forms, buttons, dropdowns, context menus, modals;
- general app background and panels.

It must not change:

- authentication, cookies, session handling, password hashing, or 2FA;
- websocket/agent relay paths;
- nginx secret-gate routing;
- local-consent prompts, notify flags, privacy bar, or permissions;
- remote desktop fullscreen/canvas behavior, except minimal non-invasive styling that preserves control.

## Safe workflow

1. Load the MeshCentral remote-PC runbook and run server preflight; these boxes can be memory constrained.
2. Back up only the custom files before overwriting:
   - `/opt/meshcentral/node_modules/meshcentral/public/styles/custom.css`
   - `/opt/meshcentral/node_modules/meshcentral/public/scripts/custom.js`
3. Write CSS/JS as static files; no build step is needed.
4. Keep the JS idempotent: add classes/hero elements only if they do not already exist, and use a MutationObserver only for light re-application after MeshCentral swaps views.
5. Do not restart MeshCentral just for these files unless caching or runtime behavior requires it; verify the files are served directly first.
6. Verify with secret-safe checks:
   - `node --check .../public/scripts/custom.js`;
   - local fetch of `/styles/custom.css` and `/scripts/custom.js` from MeshCentral;
   - external fetch through the secret path without printing the secret URL;
   - old public paths still closed;
   - `nginx`, `meshcentral`, and `andigital-pc-gate` active;
   - consent flags (`desktop/terminal/file prompt`, desktop privacy bar) still enabled.
7. Update project docs/brain with the theming rule but never with the secret URL/key.

## Pitfalls

- A pretty landing gate is not enough: if the user sends a screenshot of the post-login devices page, theme the internal MeshCentral UI too.
- Do not fully rewrite the MeshCentral app or proxy it through a new SPA just for visual polish; that risks breaking remote-control flows.
- Do not style full remote desktop mode with overlays/backgrounds that can interfere with mouse/keyboard/canvas interaction.
- Browser cache may keep old CSS/JS; tell the owner to hard-refresh or log out/in if the server checks show the assets changed.
