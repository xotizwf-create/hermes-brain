# KFU official curriculum-plan research notes

Use for KFU / ИУЭиФ program comparisons where the user asks to judge programs by учебный план, not just admissions titles.

## Official source pattern

1. Start from KFU official pages:
   - institute applicant/admissions page;
   - central admissions pages;
   - `https://kpfu.ru/sveden/education/` for official education-program disclosures.
2. On `sveden/education`, search for the direction code (e.g. `38.04.02`, `38.04.05`, `38.04.08`) and inspect rows around the matching program/profile.
3. The “Учебный план” and “Описание образовательной программы” cells often link to public Yandex Disk folders, not direct PDFs.
4. Use Yandex Disk public API to list/download official files instead of relying on rendered buttons:
   - list: `https://cloud-api.yandex.net/v1/disk/public/resources?public_key=<url-encoded-public-url>&path=/&limit=200`
   - download file: `https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=<url-encoded-public-url>&path=<url-encoded-path>`
5. Prefer the newest relevant year folder/file (2026 > 2025 > 2024), but label the year actually inspected.
6. Extract text with `pdftotext -layout` when the PDF has text. If a curriculum PDF is scanned/image-only, use the corresponding ОПОП / competence-matrix PDF as supporting official evidence and say the plan itself was image-only unless OCR was performed.

## What to extract for program fit

For each candidate program, capture concrete discipline names, especially:

- data/analytics: эконометрика, методы обработки данных, аналитические системы, бизнес-анализ, большие данные;
- IT/product/process: IT-менеджмент, управление IT-проектами, корпоративные ИС, базы данных, моделирование бизнес-процессов;
- AI/digital transformation: искусственный интеллект, цифровые платформы, цифровая трансформация, сквозные цифровые технологии;
- domain specialization: финансы, госуправление, smart city, GIS, banking, risk management.

Then rank by fit to the user’s stated trajectory, not by prestige alone. For analytics + AI agents, Business Informatics / digital technologies and IT-management/business analytics tracks usually outrank pure finance/economics unless the user explicitly wants fintech or financial analytics.

## Reporting pattern

- State that the comparison is based on official KFU disclosures and name the years checked.
- Separate “best fit for AI/analytics” from “best fit if staying strictly inside ИУЭиФ”.
- Include a short table: rank, program/profile, why it fits, caveat.
- Avoid overclaiming admissions currency: intake-plan PDFs show current-cycle intake; `sveden/education` can include active/accredited programs not necessarily present in the current intake plan.
