---
name: hh-ru-semiauto-job-search
description: "Полуавтоматический поиск вакансий на hh.ru для Александра: ИИ-агенты, AI automation, внедрение ИИ; без API соискателя и без хранения аккаунта."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hh.ru, job-search, automation, browser-session, vpn]
---

# hh.ru semiauto job search

Use this when Александр asks to search hh.ru vacancies, prepare responses, or help with applications.

## Key constraints

- Do **not** plan around hh.ru applicant API/OAuth: support for applicant API was discontinued on 2025-12-15.
- Do not ask for or store hh.ru passwords, SMS codes, cookies, tokens, or browser profile data in chat or memory.
- Default safe mode: find vacancies, rank them, and draft cover letters only. Do **not** send the application or cover letter until Александр explicitly approves the exact vacancy and the exact final text.
- Browser-session workflow is allowed only after Александр approves it, but even then messages/applications must wait for final approval of the concrete draft.
- For fully automated applying, use a real browser session only after the user logs in personally. Never send mass applications without explicit per-batch approval and never send any individual message without approval of its final text.

## Network/VPN notes

- hh.ru may reject VPN egress. If hh.ru/api.hh.ru returns 403/451 or times out from the server, first suspect VPN/routing rather than the site being down.
- On the Albery/Hermes server, hh.ru is meant to go through the direct Russian IP while VPN remains enabled. Check routes before changing anything.
- If public API returns 403, ordinary hh.ru search pages may still load and can be scraped lightly as a non-authenticated user.

## Semiautomatic workflow

1. Ask for criteria if missing:
   - role/search focus;
   - full remote / city;
   - salary floor;
   - experience level;
   - stop industries/companies;
   - resume positioning / cover-letter tone.
2. Search ordinary hh.ru vacancy pages, not applicant API. If the public API returns 403/451, do not stop: open the ordinary search page in the browser and extract visible vacancy titles/salaries/links from page text/DOM.
3. Build multiple query clusters from the candidate’s actual background, not just their current title. For AI/automation roles, use:
   - `ИИ агент автоматизация`
   - `AI Automation Engineer`
   - `AI agent`
   - `внедрение ИИ`
   - `генеративный ИИ`
   - `LLM`
   - `ChatGPT автоматизация`
   - `n8n AI`
   - `Make Zapier AI`
   - `no-code автоматизация ИИ`
   - `Prompt engineer автоматизация`
   - `RAG LLM`
4. For banking/project-finance candidates (e.g. project manager in a bank evaluating projects and approving financing), do not search only `проектный менеджер`: it produces generic PM/sales noise. Search and rank by transferable finance clusters:
   - `проектное финансирование финансовая модель инвестиции`
   - `финансовый менеджер проектов`
   - `инвестиционный аналитик финансовая модель`
   - `руководитель по проектному финансированию`
   - `кредитный риск корпоративный бизнес`
   - `риск-менеджер банк корпоративный бизнес`
   - `лизинг B2B банк`
   - `project manager bank finance fintech`
   - `business analyst fintech finance`
5. Use the user’s hard filters literally. If they say “strictly from 150k”, set salary floor to 150000 and discard/flag any result whose visible lower bound is below 150k. Salary-not-shown vacancies can stay only when the search filter matched and the role is highly relevant; explicitly say salary is not disclosed and recommend stating expectations in the first contact.
6. Prefer full remote (`schedule=remote`) when requested and rank high:
   - AI agent / AI automation / AI integrator / LLM / RAG / GPT / n8n / Make / Zapier;
   - implementation/consulting/business automation roles;
   - banking/project-finance/fintech roles that turn the person’s current domain into higher pay;
   - senior ownership roles if the profile matches.
7. Downrank or exclude:
   - pure sales/account manager unless requested or clearly adjacent to the candidate’s finance domain (leasing/project sales may be acceptable but label as sales-heavy);
   - generic marketing/SEO roles unless AI implementation is central;
   - generic PM roles with no domain fit;
   - internships/junior assistant roles unless requested.
8. When Александр asks for AI-agent/AI-automation implementation roles and says to exclude “сеньеров всяких и тд”, treat this broadly and filter out:
   - `Senior`, `Lead`, `Head`, `Architect`, `Team Lead`, `руководитель`, `лидер направления`, `технический директор`;
   - roles centered on managing people/teams rather than hands-on automation;
   - client/account/customer-success roles even if they mention AI;
   - sales-heavy titles (`sales`, `продажи`, `SDR`, `outreach`, `аккаунт`) unless he explicitly changes the rule.
   Prefer hands-on or middle-level titles: `AI-инженер`, `AI Automation Engineer`, `N8N Developer`, `LLM/RAG интегратор`, `специалист по внедрению ИИ`, `prompt-инженер` when the description is not sales/client-management heavy.
8. Return a clean shortlist:
   - title + company;
   - salary if visible;
   - format/city;
   - why it fits the candidate’s actual experience;
   - link;
   - caveat if salary is hidden or the role is sales-heavy;
   - suggested positioning or cover-letter angle when useful.

## Recurring vacancy watcher workflow

Use this when Александр asks for “максимально много” suitable vacancies or wants the search to keep running after the initial shortlist. See `references/watch-only-feedback-mode.md` for the current watch-only/manual-apply mode and feedback loop.

- Prefer a semiautomatic watcher over one-time manual browsing: collect new vacancies, deduplicate them, and deliver only unseen relevant matches.
- The watcher should be script-only when possible (`no_agent=true`): it prints nothing when there are no new matches, and prints a compact human-readable digest when there are matches.
- Delivery for reminders/watchers must go to the Telegram group “Уведомления” (`telegram:-5120862157`), not to Александр’s personal chat.
- Current default for Александр’s AI-agent job search is **watch-only**: he wants new relevant vacancies sent to him, then he applies manually and gives feedback on whether the recommendation was useful.
- Treat simple feedback as filter-training input: “норм/полезно/ищи больше таких” reinforces that pattern; “не норм/продажи/маркетинг/поддержка/1С/слишком менеджерская/DS/ML” strengthens exclusions. Update the watcher rules when feedback reveals a durable pattern.
- Keep local state with at least: vacancy id/link, first_seen_at, title, company, salary text, query/source, status (`new`, `shown`, `drafted`, `approved`, `applied`, `rejected`) plus optional feedback (`good`, `bad`, reason). This prevents repeated notifications and supports later application tracking.
- Query broadly across the same class, not just one phrase. For AI/business automation searches, combine Russian and English clusters: AI agents, внедрение ИИ, AI automation, n8n, Make/Zapier, LLM/RAG, ChatGPT автоматизация, бизнес-процессы, Bitrix/CRM automation.
- On first setup, run the watcher manually once and verify both paths: it produces a digest when seeded with new matches, and stays silent on an immediate second run with the same state. It is acceptable to seed current results as already seen so the recurring job sends only genuinely new vacancies.
- Do not auto-apply from watcher output. The digest is only a candidate list; application text still requires reading the full vacancy page and explicit approval of the exact final cover letter.
- When creating/replacing persistent HH automation, pause old auto-apply or duplicate watcher cron jobs and then verify cron state: new watch-only job enabled, legacy jobs paused, delivery target is `telegram:-5120862157`.
- If this is a new persistent automation, document the watcher location, schedule, delivery target, and state file in the appropriate agent-knowledge page before reporting completion.

## Handling numbered vacancy references from digests

When Александр replies “вакансия 13” / “номер 13” to a Telegram digest, resolve the exact vacancy before drafting:

- Prefer the numbered list in the message he replied to, if visible in the chat context.
- If only the watcher state is available, do **not** assume its JSON insertion order equals the previously sent digest order. Watcher state may contain all `shown` vacancies while a digest may have been manually sorted, truncated, or assembled from multiple files/runs.
- Check any saved outbox/export files that produced the digest; if none contain that number, say clearly which vacancy you are assuming and why before drafting.
- Before writing the cover letter, open/read the vacancy page by URL and tailor to the full description, not just the watcher snippet.
- If the number cannot be resolved confidently, ask for the title/link or paste the relevant numbered item instead of silently drafting for the wrong role.

## Suggested cover-letter positioning

Default positioning for Александр when resume is not provided: practical AI automation specialist who designs AI agents and automates business processes using LLMs, integrations, prompts, workflows, and internal tools. Keep cover letters short, concrete, and human. Do not invent specific employers/projects unless the user provides them.

### Human cover-letter style for Александр

Avoid AI-sounding cover letters. Александр explicitly dislikes polished generic letters that read like ChatGPT output.

Rules:

- Write like a real person applying on hh.ru, not like a corporate brochure.
- Keep the first application letter short: 4–8 sentences is usually enough.
- Use one concrete hook from the vacancy, then one concrete matching experience from Александр.
- Prefer simple phrasing: “делал”, “собирал”, “интегрировал”, “могу показать”, “интересно обсудить”.
- Avoid inflated phrases: “практический фокус”, “ключевой собственный проект”, “на стыке”, “довести от бизнес-задачи до продакшн-сценария”, “чем могу быть полезен” unless the vacancy tone clearly fits.
- Avoid long lists of integrations in the first message. Mention 2–4 most relevant systems and add “и другие сервисы через API” if needed.
- Avoid “идеальный кандидат” tone. A little understatement is better: “похоже, мой опыт может быть близок к задаче”.
- Be transparent when appropriate: mention softly that the first draft was prepared with Александр’s own AI agent and manually reviewed/approved by him. This should sound like a demonstration of his workflow, not an apology.
- Use this only if it fits the vacancy and does not overload the letter; default wording:

```text
Честно: этот отклик я тоже готовлю через своего ИИ-агента, но финальный текст проверяю и согласовываю вручную. Для меня это как раз часть рабочего подхода: не “автоспам”, а быстрый черновик, который человек доводит до нормального вида.
```

- Shorter version for tight letters:

```text
P.S. Этот текст помог подготовить мой ИИ-агент, но отклик и формулировки я проверил вручную. Это как раз часть того, как я использую ИИ в работе.
```

- If sending after resume delivery via the separate hh.ru cover-letter textarea, verify that the page says `Сопроводительное письмо отправлено`.

Better default template:

```text
Здравствуйте. Вакансия зацепила задачами про AI-агентов и интеграции.

Я сейчас как раз делаю похожие вещи: собираю ИИ-агента для бизнеса, который работает с контекстом компании и подключается к Bitrix24, Telegram, Google Drive, 1С/WB и другим сервисам через API. Плюс есть опыт с ботами, автоматизацией отчётности и внутренними инструментами для малого бизнеса.

Понимаю, что у вас вакансия сильнее в сторону архитектуры и продакшена, но по направлению мне это очень близко. Буду рад созвониться и показать, что уже делал.
```

For a very strong/senior vacancy, do not oversell. It is acceptable to acknowledge the gap honestly while keeping the application confident.

## Timebox and recovery rules

- Александр's task budget is 60 minutes maximum. If the browser/login/apply workflow is still not finished by then, stop, report the best confirmed state, and ask whether to continue.
- After an SMS code is accepted and the resume/vacancy/apply button are verified, immediately report the result and the next safe action. Do not spend the end of the run on unrelated memory/profile edits.
- If the Telegram session is reset with `/new`, treat the previous browser work as recoverable state: inspect the current browser page and session history, then summarize what was completed instead of starting over blindly.
- Never send applications automatically unless Александр explicitly approved that batch; verifying that an apply button is available is safe, clicking through to submit is not.

## hh.ru login notes

- If hh.ru asks for phone login, the form can split the number into country code and local number. Do not type the full `+7...` into the country-code textbox and assume it worked. If a second phone textbox is present, enter the Russian local number without `+7` there (10 digits, e.g. `912...`) and only then click `Дальше`.
- Ask Александр for the SMS code only after the page clearly shows `Введите код из смс`. Never ask for or store passwords, cookies, or tokens.

## Test / approved single-application workflow

Use this when Александр explicitly asks to make a test application or approves one specific application.

How we work with hh.ru:

- Use the already-open authenticated browser session when available; preserve the session and do not ask for passwords, SMS codes, cookies, or tokens unless hh.ru itself requires the user to log in again.
- Treat “откликнись куда-нибудь на хорошую вакансию с моим резюме тестово” as a request to prepare exactly **one** carefully chosen application candidate and draft, not permission to send it immediately.
- Before any send action, show Александр: vacancy title, company, salary/remote if visible, direct link, selected resume, and the exact cover-letter text.
- Stop and wait for explicit approval such as “отправляй”, “да, отправляй”, “согласовано”, or “можно”. Do not click hh.ru send/apply buttons before this approval.
- First inspect the current browser state. If a good vacancy is already open, evaluate it before searching again.
- Prefer a high-fit remote AI/automation/agent vacancy with visible salary or strong strategic fit.
- Before applying, read the vacancy page and confirm it matches Александр’s positioning; do not apply to low-fit generic sales/marketing/junior roles.
- Use the real hh.ru browser flow, not the discontinued applicant API.
- If `hh.ru/applicant/vacancy_response?...` immediately returns the vacancy page with `Вы откликнулись` / `Резюме доставлено`, the resume was delivered even if no modal was captured.
- If a separate “Сопроводительное письмо” textarea is visible after delivery, fill and send it separately; verify the page says `Сопроводительное письмо отправлено`.
- If the first cover-letter send shows an error, retry once by setting the native textarea value, dispatching input/change events, clicking `Отправить`, and re-reading the page for the success text.
- For cover letters, tailor to the vacancy and keep it concise, human, and slightly informal. Mention AI agents, business-process automation, integrations, LLM/RAG/tool-calling only when relevant. Do not invent experience not in the resume.
- If the vacancy is senior and Александр’s resume is weaker than the requirement, do not pretend otherwise. Write honestly: “понимаю, что вакансия сильнее в сторону архитектуры/прода, но направление близкое, могу показать, что уже делал”.
- Final report must state: vacancy title, company, salary/remote if visible, link, whether resume delivery was verified, and whether the cover letter was verified.

## Verification

- Always include direct hh.ru links.
- Mention if data is based on public search pages and should be checked by opening the vacancy before applying.
- Do not claim that an application was sent unless using an authenticated browser/session and verifying the result.
- For sent applications, require on-page verification text such as `Вы откликнулись`, `Резюме доставлено`, and, if applicable, `Сопроводительное письмо отправлено`.
- If a first attempt to send the cover letter shows an error, retry once by setting the native textarea value, dispatching input/change events, clicking `Отправить`, then re-reading the page for the success text.
