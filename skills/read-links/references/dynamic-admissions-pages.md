# Dynamic university admissions pages

Use this when an official admissions site exposes rankings/entrant lists through legacy HTML forms rather than static PDFs.

## Pattern from KFU admissions
- Official current lists can live on a legacy subdomain (`abiturient.kpfu.ru`) while the public WordPress admissions site links to it.
- The page may declare UTF-8 but return Cyrillic form options in Windows-1251. If text looks like `��������`, retry decoding as `cp1251` before concluding the data is missing.
- Hidden/dynamic filters are often simple query parameters behind `<select>` elements. Read the raw HTML, extract `<select name=...>` options, then construct direct filtered URLs.
- For KFU-style filters, useful params were:
  - `p_level=2` — magistracy / магистратура
  - `p_inst=0` — Kazan Federal University
  - `p_faculty=72` — Institute of Management, Economics and Finance
  - `p_speciality=<option value>` — specific programme/profile
  - `p_typeofstudy=1|2|3` — очная / очно-заочная / заочная
  - `p_category=1` — budget; `2` — paid
- If no rows render after all filters are selected, still report the official filtered links and distinguish between: (a) live current конкурсные списки; (b) archived итоговые PDFs with проходные/summary scores; (c) missing public archive of per-person historical lists.

## Pitfalls
- Do not rely only on `web_extract` for these pages: it may summarize or miss options hidden behind controls.
- Browser snapshots may show listboxes without options; raw HTML is often more useful.
- Avoid saying the archive does not exist until you have checked both the current-list legacy endpoint and the admissions site's sitemap / documents pages.
