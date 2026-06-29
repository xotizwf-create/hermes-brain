---
name: travel-logistics-planning
description: "Use when Александр asks to plan or compare travel logistics: trains, flights, rideshares, buses, baggage/carry-on rules, transfer timing, cheap/comfortable route choices, or 'can I take X on a plane?'. Prioritize live source checks, practical recommendations, and concise Russian answers with concrete options."
---

# Travel logistics planning

Use this skill for route planning and travel practicalities: date-specific trains/flights, transfers between cities/airports/stations, baggage and ручная кладь rules, airline/security restrictions, BlaBlaCar/rideshare suitability, and budget-vs-comfort recommendations.

## Core workflow

1. **Anchor the travel facts first**
   - Route legs: origin → transfer city → destination.
   - Dates and acceptable alternatives (e.g. Monday vs Tuesday).
   - Passenger count and constraints: budget, comfort, luggage, arrival deadline, risk tolerance.
   - For taxi-to-airport questions, get the exact destination terminal before assessing traffic; broad "airport" answers can hide terminal/drop-off differences.
   - If the user speaks informally, answer in the same practical Russian style; do not over-formalize.

2. **Use live/current sources**
   - For trains/flights in Russia, Yandex Rasp/Travel pages are useful for schedules, prices, remaining seats, station/airport names, and duration.
   - For airline rules, prefer the airline’s official site; if blocked by anti-bot/WAF, cross-check with multiple travel references and clearly say the official site could not be opened from the server.
   - For BlaBlaCar, search can reveal route availability and starting price, but live driver/car details may require the user’s phone/app due bot protection.

3. **Extract concrete rows, not vague summaries**
   - Capture departure/arrival time, station/airport, duration, price, available seat classes/counts, and carrier/flight/train number.
   - When browser snapshots are huge, use DOM extraction such as `Array.from(document.querySelectorAll('table tr')).map(tr => tr.innerText)` to get route rows.
   - Watch for sites opening “all days” even when a date is in the URL; manually select the date and re-extract.

4. **Evaluate connections practically**
   - Calculate buffer between arrival and next departure.
   - For train → plane in Moscow, large buffers are valuable: account for station exit, metro/aeroexpress/taxi, airport security, registration, and disruption risk.
   - For taxi/traffic questions over a time window, check several planned departure times across the window in Yandex Maps or another live map (e.g. start, midpoint(s), end), not only "depart now". Report the range and then add a real-world buffer for pickup, station/airport access, and drop-off.
   - Prefer a slightly more expensive option if it materially reduces missed-connection risk.

5. **Present a decision, not just data**
   - Start with the short answer: “да, можно”, “я бы брал вторник”, “лучший вариант такой-то”.
   - Use compact tables for options.
   - Include a final recommendation with why: price, risk, comfort, timing.
   - Include links/search instructions when the source requires user-side app login or bot-protected UI.

## Airline carry-on and toiletries checklist

When asked what can be taken on a plane:

- Verify the airline’s current carry-on dimensions/weight.
- For Aeroflot economy/comfort, common rule to verify: **1 carry-on up to 10 kg, 55 × 40 × 25 cm**; business often **15 kg** with same dimensions.
- Liquids/gels/aerosols/creams/pastes in hand luggage: containers up to **100 ml** each, total generally up to **1 liter**, preferably in a transparent bag. The container size matters, not remaining liquid.
- Toiletries examples:
  - perfume/toilet water: yes if ≤100 ml;
  - shaving foam/gel: yes if canister ≤100 ml; typical 200–300 ml canisters should go in checked baggage or be bought after arrival;
  - toothpaste, cream, shampoo: ≤100 ml;
  - deodorant spray: ≤100 ml; stick/roll-on is safer.
- Razors:
  - disposable, cartridge/Gillette-style, and electric razors are normally OK in hand luggage;
  - straight razors, loose blades, and removable double-edge safety razor blades should not go in hand luggage.

## BlaBlaCar / rideshare guidance

When the user wants “cheap but in a good car”:

- Check whether the route exists and starting price/approximate number of trips via search if the app blocks live scraping.
- Explain that exact car/driver availability must be confirmed in the user’s BlaBlaCar app if bot protection blocks the site.
- Selection criteria for long rides:
  - driver has reviews and high rating;
  - car is comfortable for the distance (Camry, K5/Optima, Sonata, Superb/Octavia, Passat, Mercedes/BMW/Audi, good crossovers);
  - avoid tiny cars for 10+ hours if carrying luggage;
  - prefer “max 2 passengers in back”, comfort, clear luggage permission;
  - avoid 3 passengers in back, no reviews, no car photo, suspiciously cheap, or requests for off-platform prepayment;
  - morning departure is usually best for long intercity rides.

## Flight sale/load-check workflow

When the user asks whether a flight is likely to be cancelled because few seats are sold:

1. **Verify identity by time + date + route, not just flight number.** Multi-frequency routes can have adjacent Pobeda numbers; if the user's stated time and flight number conflict, say so clearly and orient the answer around the departure time they care about.
2. **Separate public facts from inference.** Public pages can show that a flight is in schedule/sale and sometimes price/tariffs; they usually do **not** reveal exact purchased seats.
3. **Try the seat map only when reachable without sensitive passenger data.** If the airline booking engine blocks automation or requires passenger/contact details, stop before entering personal data and say the limitation.
4. **Use aggregators as a fallback sale check.** If the official airline booking engine is blocked, open a reputable route search/airline page, set the date, search, and extract visible rows. In browser, `document.body.innerText` often captures full result cards when snapshots truncate them.
5. **Answer cancellation risk conservatively.** “Tickets still in sale at normal-looking prices” supports “low visible risk of cancellation due solely to low load,” but does not rule out weather, airport restrictions, aircraft rotation, or operational changes.

## International budget flight routing workflow

When the user asks to find a cheap international route with a transfer (e.g. Kazan → Istanbul → Morocco):

1. **Split the route into legs and destination airports.** Search both the final city and cheaper nearby entry hubs, then explain the onward ground leg if needed.
2. **Use schedule sources for leg viability.** FlightConnections is useful for route frequency, rough departure windows, direct-flight availability, operating airlines, and duration. Use `document.body.innerText.match(/... Flights[\s\S]*?Start planning/)` and schema.org event snippets from page scripts to extract the useful text when the visual calendar is hard to parse.
3. **Use OTAs/aggregators for indicative fares only unless a live result card is visible.** Trip.com/Aviasales pages may expose “from $X” or average-price data while hiding exact bookable combinations; label these as indicative and do not say “found all tickets” unless you actually opened date-specific fare cards.
4. **Rank by connection realism, not just cheapest headline.** For separate tickets, prefer 5–6+ hours minimum buffer; 7–10 hours is more comfortable; overnight transfer is often the safest budget option.
5. **Make the recommendation concrete.** Give the first date windows to check, route codes, why one destination is more practical, and what the user should search next.

## Tour-package comparison workflow

When Александр asks to compare resort destinations by price (e.g. Thailand vs Bali from Kazan):

1. **Treat it as a package-tour task, not just flights.** Anchor the comparison on city of departure, season/month, adults/children, nights, hotel class, board type, and minimum quality. If the user did not specify people/nights, use a visible aggregator default only if you label it (commonly 2 adults, 6–11 nights) and offer to recalc.
2. **Filter by the actual stated constraints.** If the user says “4★+, all inclusive, no 3★”, check `hotel_4/food_allinclusive/` and also `hotel_5/food_allinclusive/` when the 4★ result is empty. Do not mix breakfast/no-meal offers into the main answer except as a clearly marked alternative scenario.
3. **Use aggregator pages as live indicative evidence.** 1001 Тур pages often expose useful text in browser snapshots/DOM even when Travelata or tour-operator sites are blank or behind verification. Use `document.body.innerText.match(/Сортировать по:[\s\S]{0,9000}/)` to extract offer cards and quote the page’s “prices updated” timestamp when visible.
4. **State availability gaps plainly.** If `4★ + all inclusive` returns “Туров не найдено” for a destination, say that exact package shape was not available; then compare against the nearest valid alternative (e.g. 5★ all inclusive) and a relaxed alternative (4★ breakfast/no meal) separately.
5. **Present the decision first.** Start with which destination is cheaper under the user's exact constraints, then give a compact table with price for two and per-person estimate, then named hotel examples.

## Pitfalls

- Do not claim exact BlaBlaCar driver/car availability unless the live listing was actually opened.
- Do not infer date-specific schedules from an “all days” page; select the date and verify rows.
- Do not trust the user's flight number over their stated departure time when they conflict; verify both and explicitly correct the identity.
- Do not quote airline baggage rules purely from memory; verify or state the source limitation.
- Do not overclaim “how many seats are bought” unless a live seat map was actually opened and counted; sale availability is only a proxy.
- Do not over-explain when the user asks a quick voice-style travel question: answer with concrete norms/options and a clear recommendation.

## References

- `references/moscow-kievsky-sheremetyevo-taxi-2026.md` — quick taxi traffic-check example for Киевский вокзал → Шереметьево Terminal D: Yandex Maps planned-departure times across 06:20–08:00, duration table, and concise verdict style.
- `references/moscow-kazan-june-2026.md` — session notes from a Moscow/Kazan planning example: Yandex Rasp extraction pattern, Aeroflot carry-on/toiletries summary, and BlaBlaCar selection heuristics.
- `references/moscow-kazan-pobeda-june-2026.md` — session notes for Pobeda Moscow → Kazan flight identity/load check: DP6841 vs DP6843 mismatch, terminal D corroboration, Tutu fallback extraction, and cautious cancellation-risk phrasing.
- `references/kazan-morocco-routing-2026.md` — session notes for budget international routing Kazan → Istanbul → Morocco: FlightConnections extraction, indicative OTA fares, and connection-buffer recommendations.
- `references/kazan-thailand-bali-tour-packages-2026.md` — session notes for comparing package tours from Kazan under strict 4★+ all-inclusive constraints: 1001 Тур filter URLs, DOM extraction pattern, Thailand vs Bali price findings, and how to separate strict vs relaxed alternatives.