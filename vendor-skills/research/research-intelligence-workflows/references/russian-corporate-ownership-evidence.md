# Russian corporate ownership evidence (ЕГРЮЛ + shareholder registries)

Use this when the owner asks for a reliable ownership/beneficiary scheme for a Russian company or holding/division.

## Evidence hierarchy

1. Official ЕГРЮЛ extracts from ФНС for legal entities and intermediate owners.
2. Official issuer disclosures (e-disclosure / issuer site) for lists of affiliated persons, annual reports, material facts, registrar identity, and shareholder-meeting materials.
3. Extracts from shareholder registers for non-public JSCs/AOs — required to prove exact shareholder percentages when ЕГРЮЛ only identifies the registrar.
4. Commercial aggregators, news, and company pages are discovery aids only; do not use them as proof for exact ownership unless the user explicitly permits non-official sources.

## Reporting rules

- Distinguish exact ЕГРЮЛ ownership (ООО participant shares, company-controlled LLC stakes) from unavailable JSC shareholder composition.
- For AO/PAO chains, ЕГРЮЛ generally gives the registrar/reestr holder, not the shareholders. Do not invent ultimate beneficial owners from media, sanctions lists, or aggregators.
- If the user asks for “до конечных бенефициаров” but official shareholder-register extracts are unavailable, state the boundary explicitly: “officially traceable to X; further disclosure requires register extract for AO Y.”
- Record for each node: full legal name, INN/OGRN if available, source type, source date/extract date, owner, stake %, and confidence/limitation.
- For divisions/АПК holdings, define the included companies from official holding pages/disclosures, then verify each entity via ЕГРЮЛ. If the division perimeter is not formally defined in a registry document, label it as “operational perimeter from official holding materials,” not a legal subgroup.

## Practical workflow

1. Identify the head company and division perimeter from official company materials/disclosures.
2. Pull ФНС ЕГРЮЛ extracts for the head company, subsidiaries, and every intermediate owner discovered in the extracts.
3. Parse participant/share sections for ООО and ownership stakes; for AOs, capture registrar and note missing shareholder register data.
4. Cross-check issuer disclosure pages for affiliated-person lists and current registrar details.
5. Build a tree/table that separates confirmed ownership from unresolved AO shareholder layers.
6. In the final report, include a “needed for full beneficiary disclosure” list naming the exact shareholder-register extracts still required.

## ФНС ЕГРЮЛ recursive extraction pattern

When a Russian ownership task asks for maximum depth and official-only evidence, use a recursive closure loop rather than a one-pass search:

1. Download official ФНС ЕГРЮЛ PDFs for the seed companies (search by INN/OGRN/name through `egrul.nalog.ru`, then trigger the extract/download request) and convert them to text for parsing.
2. From every extract, collect all legal-entity INNs/OGRN that appear in participant/founder blocks, predecessor/successor blocks, pledgee blocks where relevant, and registrar blocks. Keep pledgees/registrars labelled separately so they do not become “owners” by mistake.
3. Download official extracts for every newly discovered legal entity and repeat until the control pass finds no referenced legal entities without an extract.
4. Report the closure check explicitly, e.g. “official extracts checked: N; referenced legal entities: M; missing extracts: 0”. This is stronger than saying “searched thoroughly”.
5. Separate current operational perimeter from historical/reorganization perimeter. If an old ООО was transformed/merged into a current entity, include it as historical evidence but do not mix its old participants into the current cap table.
6. For товарищество на вере/partnership entities, ЕГРЮЛ may disclose nominal contributions without a percentage; show the official contribution amounts and, if useful, label any percentages as calculated from contributions rather than official ЕГРЮЛ percentages.

## Pitfall

Do not present a polished “ultimate beneficiary” chart if the only official evidence stops at a non-public AO or registrar. The correct deliverable is a source-backed partial tree with explicit gaps, not a plausible-but-unsourced beneficiary narrative.
