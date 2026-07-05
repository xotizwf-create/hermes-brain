# Russian TV episode / clip identification

Use when the user remembers a scene from a Russian series/show and asks for the season, episode, and where to watch.

## Workflow pattern

1. Search exact scene fragments and character names in Russian, including variants/aliases (`Сергей Иванович` / `Иваныч`, `Колян`, title variants).
2. If a short clip is found first, capture its public title, upload date, channel, and video ID/URL. Clip titles often expose the scene name even when they do not show the source episode.
3. Cross-check episode numbering across at least two schemas:
   - official/current streaming catalog (e.g. PREMIER/RUTUBE season pages);
   - reference databases (TheTVDB, Kino-teatr, VokrugTV, Wikipedia) that may split TV broadcast blocks differently.
4. Prefer the official streaming catalog for the user-facing season/episode, but mention alternate numbering if sources disagree.
5. On RUTUBE series pages, `metainfo/tv/<id>/seasonN/` pages expose episode links in the DOM. Use browser DOM extraction such as:
   ```js
   Array.from(document.querySelectorAll('a'))
     .map(a => ({text: a.innerText, href: a.href}))
     .filter(x => x.text.includes('7 сезон, 14 серия'))
   ```
6. For RUTUBE direct video API requests, 403 blocks can occur from the server. Do not turn that into a durable limitation; use browser navigation, search snippets, or mirror pages that embed the RUTUBE video ID.
7. If the user asks to watch for free, only provide legal/free pages you found (official free clip, free catalog page, ad-supported player). If the full episode is subscription-only, say so clearly and give the free clip separately.

## Example: Реальные пацаны — “Сальто” scene

Scene request: Сергей Иванович/Иваныч tells Колян to do a flip on a trampoline so he will help with money.

Findings:
- Clip title: `Реальные пацаны: Сальто`.
- Free official clip URL: `https://rutube.ru/video/1486e158fef5394c112a1a7feeaa6ab7/`.
- Mirror/embed page: `https://moltv.ru/v/1486e158fef5394c112a1a7feeaa6ab7/`.
- Official RUTUBE/PREMIER catalog numbering: `Реальные пацаны`, season 7, episode 14.
- Episode URL found from RUTUBE season page: `https://rutube.ru/video/dc2bd4b7ef57f13f76b81886399c952d/`.
- Alternate database numbering encountered: TheTVDB lists the same 2019 block as season 12; its S12E14 is `Родительский день` (aired 2019-04-11). Explain this mismatch rather than choosing silently.
