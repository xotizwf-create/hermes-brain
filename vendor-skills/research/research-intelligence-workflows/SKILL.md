---
name: research-intelligence-workflows
description: "Use when gathering, monitoring, synthesizing, or writing research/intelligence from arXiv, papers, blogs/RSS, prediction markets, LLM wikis, and source-backed web/media content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, arxiv, papers, blogs, monitoring, synthesis, polymarket]
    related_skills: []
---

# Research & Intelligence Workflows

## Overview

Class-level research workflow for finding sources, monitoring feeds, querying domain datasets, synthesizing evidence, and producing source-backed writeups. Keep raw evidence separate from conclusions and cite where claims came from.

## When to Use

- Search arXiv or academic papers.
- Draft ML/AI research papers or experiment sections.
- Monitor blogs/RSS feeds.
- Query prediction-market data.
- Build/query an LLM wiki or local knowledge base.
- Turn YouTube/blog/source material into summaries, threads, or reports.
- Find official/authoritative sources for narrow public-fact claims, including municipal documents and infrastructure schemes.
- Research regulatory standards and legal/normative deadlines, distinguishing what a source actually regulates from adjacent requirements.
- Find and deliver source-backed public images/media from the web.
- Check local retail availability or delivery eligibility for a product at a specific address.
- Collect Russian public cadastral-map/НСПД parcel data around a cadastral number and produce source-backed neighbour/distance tables.
- Build Russian corporate ownership / beneficiary schemes from official evidence such as ЕГРЮЛ extracts, issuer disclosures, and shareholder-register extracts.

## Workflow

1. Define the research question and inclusion/exclusion criteria.
2. Collect sources with tool-specific queries; save IDs/URLs/metadata.
3. Extract only the relevant evidence; distinguish quoted facts from interpretation.
4. Synthesize into the requested format with citations/source links.
5. If monitoring, make the watcher quiet unless there is a new actionable item.

## Subdomains

### Local Retail / Delivery Availability

For address-specific grocery/retail questions, do not infer availability from a generic product page. Check in this order when possible:

1. Official store/delivery site with the exact address selected.
2. Official delivery aggregator page for the same retailer and address.
3. Public API or network endpoints only if they return store/address-scoped data.
4. Search-indexed or third-party catalog pages only as evidence that the item exists in the chain, not that it is orderable at the address.

If bot protection, captcha, or login blocks the address-scoped check, say exactly what was and was not verified. A valid conclusion can be: “the item appears in the retailer/aggregator catalog, but I could not confirm current orderability for this address.” Ask for a screenshot/app result only after exhausting accessible sources.

For dynamic retailer sites, inspect the frontend bundle/network model before giving up: Nuxt/SPA apps often expose official `/webgate` or API endpoints that can return address/store-scoped data even when the rendered page is blocked. Keep the method source-backed and live: geocode the address, identify the serving store, then query the store-scoped catalog. Magnit-specific endpoint notes live in `references/magnit-delivery-api-checks.md`.

### Official Municipal / Public-Fact Evidence

When the user needs an official source for a narrow claim, do not stop at search snippets. Prefer official domains, download attachments/archives, and search inside DOCX/PDF files. Quote exact passages with document title, issuing body, date/number, page/book/attachment, and direct URL. Keep direct evidence separate from interpretation: if the document supports a term but does not literally use it, say so instead of presenting the inference as a verbatim official statement. Detailed notes and the Sarapul sewerage example live in `references/official-municipal-source-evidence.md`.

### Russian Public Cadastral Map / НСПД Parcel Tables

When the user asks for land parcels around a кадастровый номер, treat this as a source-backed geodata extraction task, not a visual estimate from a screenshot. Use public cadastral-map/НСПД data where available, filter for land parcels, compute distances from parcel geometries (not centroids), and produce the requested Excel/table columns. If the official interactive map is slow, use the same public data exposed through map/search endpoints and verify the workbook contents before sending. **Run the ready script** `scripts/nspd_parcels.py` with the venv python (`/usr/local/lib/hermes-agent/venv/bin/python .../scripts/nspd_parcels.py 18:30:000423:1789 --radius 100 --objects land|all`) — do not hand-build the geometry/Excel each time. nspd.gov.ru/pkk.rosreestr.ru are IP-blocked for our servers (even via the RU eth0); use the kadastrmapp.online mirror, never the official map. For the COMPLETE list (every garage/ОКС), use `scripts/nspd_parcels_local.py` (pynspd spatial search) from a Russian residential IP/proxy — the official НСПД caps a single intersects call at ~300, so it tiles; the mirror script is partial fallback only. Full method, confirmed endpoints, CRS/UTM fix and caveats are in `references/russian-cadastral-parcel-extraction.md`.

### Regulatory Standards / Legal-Normative Evidence

When the user asks whether a law, ГОСТ, СанПиН, methodology, or agency rule sets a deadline or procedural requirement, search and report at the level of the exact regulatory mechanism:

1. Start with the class-level governing standard/regulation, then sector-specific examples.
2. Separate adjacent requirements that are easy to conflate (e.g. sample storage or start-of-analysis deadlines vs. final protocol issuance deadlines).
3. Quote what the source actually requires and say explicitly when it does **not** establish the requested fixed term.
4. If no universal term is found, identify the likely controlling documents: contract, request/TZ, internal quality-management procedure, or a specific administrative regulation for that context.
5. Give the user a practical request/claim wording when the research is meant for a dispute or compliance check.

Lab/protocol examples and Russian ГОСТ notes live in `references/regulatory-standards-evidence.md`.

### Russian Corporate Ownership / Beneficiary Schemes

For Russian company ownership reports, use official evidence hierarchy: ФНС ЕГРЮЛ extracts first, issuer disclosures second, shareholder-register extracts for AO/PAO shareholder percentages. Commercial aggregators and media are discovery aids only unless the user explicitly allows them. For non-public AOs, do not infer exact shareholders from ЕГРЮЛ: ЕГРЮЛ usually names the registrar, not the shareholder list. If the official trail stops at an AO or registrar, state that boundary and list the exact register extracts needed for full beneficiary disclosure. Detailed workflow and report fields live in `references/russian-corporate-ownership-evidence.md`.

### Public Image / Media Retrieval

When the user asks for internet photos or source-backed media, optimize for delivering usable media, not just links:

1. Prefer open/traceable sources first (Wikimedia Commons, official pages, reputable media libraries). If those are sparse, use image search to discover candidates.
2. For Bing Images, extract original image URLs from `a.iusc` JSON metadata (`m.murl`) rather than downloading base64 thumbnails from the rendered page.
3. Download selected files to `/tmp` with a browser-like user agent; if a hotlinked/media-bank URL returns 410/403, pick another result instead of reporting failure after the first candidate.
4. Verify the file is a real image (`file`, PIL dimensions) and, when relevance matters, inspect with vision before sending.
5. On Telegram, send as native media using `MEDIA:/absolute/path` because the user expects actual attachments, not bare local paths or only web links.

### Academic Search and Paper Writing

Use arXiv/paper metadata, then read abstracts/full text as needed. For paper writing, maintain claims→evidence→experiment mapping.

### Blog/RSS Monitoring

Prefer scheduled, quiet watchers. De-duplicate posts and alert only on new matches.

### Prediction Markets

Report market id, price/probability, liquidity/volume context, and retrieval time.

### Knowledge Bases / LLM Wiki

Preserve link structure and provenance when building local wikis. Do not invent missing citations.

## Pitfalls

- Treating a search result title as if the paper was read.
- Mixing stale market prices with current claims.
- Monitoring feeds noisily on every tick.
- Writing polished conclusions before evidence is collected.
- Overclaiming that a regulatory source sets a deadline when it only governs adjacent steps (e.g. sample storage/start of analysis) or protocol contents/approval.
- Failing to state a negative finding precisely: if no universal fixed deadline was found, say what documents would control instead (contract, internal procedure, administrative regulation).
- Treating a chain-level or city-level product listing as proof of address-level availability. For delivery questions, availability must be scoped to the selected address/store; otherwise label it unconfirmed.
- Sending image-search thumbnails or stale hotlinks without verifying the downloaded file and visual relevance.
- Returning only URLs when the user asked to “скинь фотки”; on Telegram, attach real files with `MEDIA:` when possible.
- For cadastral radius reports, using screenshot proximity or centroid-to-centroid distance instead of public parcel geometry distance from the target contour.
- For cadastral/НСПД work, stopping at an official-site IP block. Try the documented public mirror endpoints with proper `Origin`/`Referer`, then clearly label the data source and caveats.
- Producing a first narrow cadastral table from only the target card/same visible area; a radius request needs a buffer around the target geometry and deduped parcel collection from quarter searches plus targeted GetFeatureInfo sampling.
- Mixing buildings/premises into land-parcel lists; filter cadastral-map features to land parcels unless the user explicitly asks for all objects.
- For Russian ownership charts, filling AO shareholder gaps with plausible beneficiary claims from unofficial sources. If official ЕГРЮЛ/disclosure evidence stops at an AO/registrar, report the gap and required shareholder-register extracts instead.

## Verification Checklist

- [ ] Sources/IDs/URLs recorded.
- [ ] Retrieval time noted for current data.
- [ ] Claims backed by evidence.
- [ ] Output matches requested format.
