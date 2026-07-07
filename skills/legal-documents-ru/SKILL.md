---
name: legal-documents-ru
description: Generate polished Russian legal/business documents (договоры, акты, соглашения) as BOTH .docx and .pdf with GOST-style formatting, then deliver them straight to the owner's Telegram. Use when the owner asks for a contract, agreement, act, or any formal RU document "по ГОСТу / красиво оформленный / в Word и PDF".
---

# Russian legal/business documents (GOST-style, DOCX + PDF)

When the owner asks for a formal Russian document (договор, акт, соглашение, претензия,
коммерческое предложение) "по ГОСТу", "красиво оформленный", "юридически грамотный",
or "в Word и PDF" — follow this. Proven on 2026-06-21 (договор оказания услуг, 150 000 ₽).

## Toolchain on server 217 (what is and isn't available)
- **No pandoc, no python-docx, no reportlab.** Do NOT try to `pip install` them — wastes tokens.
- **LibreOffice is installed** (`soffice` / `libreoffice`). It is the converter.
- Best source format = **flat OpenDocument Text `.fodt`** (single XML file): full control over
  margins, fonts, spacing, indents, tables; converts cleanly to both DOCX and PDF.

## Method (do this)
1. If drafting from scratch, write the document as a `.fodt` XML file in a writable scratch dir (`/tmp/...`).
   **Not** `/root/claude-agent/...` or the brain clone working tree (guard / dirty-state noise).
2. Convert to BOTH formats:
   ```bash
   cd /tmp/<dir>
   soffice --headless --convert-to docx:"MS Word 2007 XML" doc.fodt
   soffice --headless --convert-to pdf doc.fodt
   ```
3. Verify: `pdfinfo doc.pdf` (pages, A4 595×842 pt) and that the .docx size is non-zero.
4. Rename to a human Russian filename, then deliver (see Delivery).

## When the owner provides a contract template (`.doc` / `.docx`)
Use the supplied template rather than rebuilding the contract from scratch.
1. Put work files under `/tmp/<job>/`; final user files under `/root/.hermes/outbox/`.
2. For old binary `.doc`, first convert it with LibreOffice:
   ```bash
   libreoffice --headless --convert-to docx --outdir /tmp/<job> /path/to/template.doc
   ```
3. Inspect the converted DOCX structurally with `python-docx`: print paragraph texts and table rows/cells before editing. Contract data often lives in tables and appendix cells, not only paragraphs.
4. Replace all requested business fields everywhere they appear: contract number/date, preamble, product name, quantity, unit price, total, VAT wording, specification table, technical-description table, appendix headers.
5. If the owner says to remove procurement boilerplate like `ИКЗ`, `идентификатор закупки`, or `на основании протокола`, remove both the standalone line and embedded mentions in paragraphs/tables. Do not leave an orphaned blank procurement line at the top.
6. Verify before delivery by reopening the saved DOCX and checking:
   - required new values are present;
   - old contract number/product/amount are absent;
   - banned phrases (`ИКЗ`, `идентификационный код закупки`, `на основании протокола`) are absent;
   - the DOCX is non-zero and LibreOffice can convert it to PDF as a smoke test.
7. Send the final `.docx` as a real Telegram attachment and only report success after the send helper returns `OK`.

## GOST-style formatting defaults (unless owner overrides)
Based on GOST R 7.0.97-2016 for organizational documents; safe defaults for contracts:
- Page A4, portrait. Margins: **left 30 mm, right 15 mm, top 20 mm, bottom 20 mm**.
- Font **Times New Roman 14 pt** (12 pt acceptable for signature/requisites block).
- Line spacing **1.5**, body text **justified** (`text-align: justify`).
- First-line indent **1.25 cm** for body paragraphs.
- Title and section headings: **bold, centered**; headings `keep-with-next`.
- Requisites/signatures: a **2-column borderless table** (Заказчик | Исполнитель), each with
  Наименование, ИНН/КПП, ОГРН(ИП), Адрес, Р/с, Банк, К/с, БИК, тел./e-mail, подпись, М.П.

## Contract skeleton (договор возмездного оказания услуг, ГК РФ гл. 39)
Header (№, город, дата) → преамбула (Заказчик/Исполнитель, «на основании») → then numbered:
1. Предмет договора (ТЗ/календарный план как приложения, результат, акт).
2. Цена и порядок расчётов (сумма прописью; аванс/постоплата; безнал; твёрдая цена).
3. Права и обязанности сторон.
4. Порядок сдачи и приёмки (акт, срок приёмки, мотивированный отказ, односторонний акт).
5. Исключительные права (переход к Заказчику после оплаты; гарантия чистоты прав).
6. Ответственность (неустойка 0,1 %/день, кэп 10 %; кэп общей ответственности = цена).
7. Конфиденциальность.
8. Форс-мажор.
9. Срок действия, изменение, расторжение (ст. 782 ГК — односторонний отказ).
10. Разрешение споров (претензионный порядок + арбитражный суд по месту ответчика).
11. Заключительные положения (2 экз., применимое право — гл. 39 ГК РФ, приложения).
12. Адреса, реквизиты и подписи (таблица + М.П.).
Leave fill-in blanks as `____`. Money: digits **и** прописью («150 000 (Сто пятьдесят тысяч) рублей 00 копеек»).
Adapt sections to the document type; reuse the formatting defaults always.

## Delivery — send files straight into the owner's Telegram
```bash
python3 /root/.hermes/agent-knowledge/scripts/send_telegram_file.py \
  "/tmp/<dir>/Имя файла.pdf" --caption "Короткое описание"
```
- Sends via the @GoogleDeck_Bot Bot API; token read from `/root/.hermes/secure/claude_code/bot_token`
  (never printed/committed). Default chat = owner DM (`1451982360`); `--chat <id>` to override.
- Works for any file type (PDF, DOCX, images). This is how the agent puts artifacts "прямо сюда".
- Send each file as its own call; returns `OK` on success.

## Auditing app-generated legal DOCX/export pipelines
When the complaint is that an in-app legal agent produces an ugly/low-quality contract, inspect the whole chain, not only the legal prompt:
1. Read the actual conversation/user ask and the agent's response to separate **content quality** from **export/rendering quality**.
2. Find the export function that turns the answer into `.docx`/`.pdf`. If it treats contracts as generic Markdown, fix the exporter: prompts alone cannot enforce Word margins, paragraph styles, table borders, or first-line indents after conversion.
3. Add a contract/official-document mode keyed by terms like `договор`, `соглашение`, `акт`, `контракт`, `оферта`, `ГОСТ`.
4. In that mode, force the document properties in code: A4, GOST-style margins, Times New Roman 14 pt, 1.5 spacing, justified body paragraphs, first-line indent, centered bold title/section headings, and visible table borders.
5. Verify the generated artifact structurally, not only visually: inspect DOCX XML for margins, font size (`w:sz=28`), justification (`w:jc=both`), first-line indent, table presence/borders, and absence of generic Word heading/title styles in the contract body. Then restart/deploy the app and smoke-test the live service.

## Pitfalls
- Don't write the source file under the agent's own runtime (`/root/claude-agent`) — the safety
  guard blocks it. Use `/tmp`.
- Don't edit the agent's Telegram bridge to attach files — that's the blocked runtime. The Bot-API
  helper above sidesteps it entirely.
- Don't assume a bad-looking contract is purely a lawyer-agent prompt problem. Generic Markdown→DOCX exporters often destroy legal formatting; fix the renderer/exporter when the layout is wrong.
- Verify `pdfinfo` reports A4 and the expected page count before reporting success.
