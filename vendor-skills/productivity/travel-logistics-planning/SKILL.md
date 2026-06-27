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

## Pitfalls

- Do not claim exact BlaBlaCar driver/car availability unless the live listing was actually opened.
- Do not infer date-specific schedules from an “all days” page; select the date and verify rows.
- Do not quote airline baggage rules purely from memory; verify or state the source limitation.
- Do not over-explain when the user asks a quick voice-style travel question: answer with concrete norms/options and a clear recommendation.

## References

- `references/moscow-kazan-june-2026.md` — session notes from a Moscow/Kazan planning example: Yandex Rasp extraction pattern, Aeroflot carry-on/toiletries summary, and BlaBlaCar selection heuristics.