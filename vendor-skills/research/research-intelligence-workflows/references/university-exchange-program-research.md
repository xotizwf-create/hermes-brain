# University Exchange / Academic Mobility Research Notes

Use this reference when a user asks how a university exchange or academic mobility program works: where to apply, eligibility, documents, costs, deadlines, and practical sequence.

## Source strategy

1. Prefer the university's official student/academic mobility pages over generic search snippets.
2. Find the full navigation cluster, not just the landing page: catalog/program list, eligibility, before applying, application procedure, after selection, FAQ, documents/templates, contacts, and deadlines.
3. If the deadlines page looks stale, report that explicitly and route the user to the official coordinator instead of presenting old dates as current.
4. Extract the catalog systematically: countries, partner universities, language of instruction, level, and fields. For paginated catalogs, scrape all pages or use the browser DOM to collect visible cards.
5. Convert bureaucratic pages into a practical checklist: choose program → verify courses/language → coordinate with department → estimate budget → submit documents → selection → nomination → invitation → visa/housing/travel → formal leave/return paperwork.

## KFU / Казанский федеральный университет example

Official student site cluster used in the 2026-07 session:

- Landing: `https://students.kpfu.ru/node/30736` — exchange with partner universities for 1–12 months; tuition abroad is free under the exchange, but living/travel/visa/insurance usually paid by the student unless scholarship exists.
- Catalog: `https://students.kpfu.ru/academic+mobility/exchange-program/catalog` — filter by country, level, language, direction. The catalog was paginated; collecting all pages yielded about 42 partner entries.
- Eligibility: `https://students.kpfu.ru/node/30436` — budget/paid students, any citizenship; bachelor/specialist full-time after at least 2 semesters and not final year; first-year master's students. Selection criteria: grades, language, motivation, research/social activity, quotas; preference for students who have not participated before.
- Before applying: `https://students.kpfu.ru/node/30437` — study partner-university courses and requirements; participation is possible only when there are courses in the student's specialty and language; discuss selected courses with department/program head.
- Application: `https://students.kpfu.ru/node/30438` — apply about 6 months before planned study; max 3 applications per semester. Typical documents: institute/faculty nomination/presentation, Europass CV in foreign language, motivation letter, language proof, transcript/extract from gradebook. TOEFL/IELTS required for USA programs; other programs may accept teacher language certificate.
- After selection: `https://students.kpfu.ru/node/30439` — KFU coordinator assists nomination/registration; host university may make final admission decision; after invitation handle housing, visa, insurance, tickets, and officially formalize absence from KFU.
- FAQ: `https://students.kpfu.ru/node/308` — scholarships were listed for Free University of Berlin, Giessen, Granada, Heilongjiang; expenses include accommodation, food, travel, consular/visa fees, registration fee, study literature.
- Contacts: `https://students.kpfu.ru/node/30450` — Department of External Relations / Academic Mobility, mobility@kpfu.ru, +7 (843) 233-74-67, Кремлевская 18, корпус 6, к. 214.

## Output pattern

For Russian chat users, present:

1. Short bottom line: what the program is and whether tuition is free.
2. Table of countries/universities only when it helps scanning; do not dump every catalog field if the user did not specify a major.
3. Clear eligibility and money sections.
4. A step-by-step application sequence with who to contact.
5. Caveat on stale deadlines and the exact email/office to confirm current calls.

## Pitfalls

- Do not treat old deadline pages as current. Say they are stale if dates are historical.
- Do not imply scholarship is guaranteed; it is program-specific and often unavailable.
- Do not skip department/course-matching: exchange is viable only if host courses fit the student's curriculum and language.
- Do not stop at a single FAQ page; academic mobility sites often split the actual procedure across 5–8 small pages.
