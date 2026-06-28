# Moscow → Kazan Pobeda flight check, June 2026

Session pattern for checking a specific Pobeda flight when the official booking engine is blocked or incomplete.

## What happened

User asked about a Pobeda flight Moscow → Kazan, Tuesday 30 June 2026, supposedly 10:25 from Sheremetyevo: terminal, sold seats/load, and cancellation risk.

Findings from live/public sources:

- Pobeda route page showed nearby schedule rows where **DP6841** was the early flight around 08:00, while **DP6843** was the **10:25** flight.
- Search result/card for `DP 6843` showed Sheremetyevo, **terminal D**.
- The official Pobeda ticket host `ticket.flypobeda.ru/websky` returned 403 from the server session; do not conclude the flight is unavailable from that alone.
- Tutu search page accepted a date edit and displayed live sale options for 30 June:
  - Pobeda 08:00 → 09:40, from about 4,310 ₽ without baggage;
  - Pobeda 10:25 → 12:05, from about 4,310 ₽ without baggage;
  - baggage add-on about +2,600 ₽ / with baggage from about 6,910 ₽.

## Reusable workflow

1. Cross-check flight number against the **time**, not only route/date. On this route, a user-provided number could be off by one daily frequency: 10:25 was DP6843, not DP6841.
2. If the airline booking engine is blocked, check an aggregator sale page rather than stopping:
   - open a route/airline page such as Tutu;
   - set date in the visible search field;
   - click search;
   - use `document.body.innerText` in browser console to extract all displayed rows when the accessibility snapshot truncates cards.
3. Treat available public sale + normal price as evidence that the flight is being sold, but **not** as exact load factor.
4. Explain load/cancellation carefully:
   - exact number of purchased seats is not public;
   - seat-map availability can estimate but may require entering booking flow and passenger/contact data;
   - if tickets are still sold on reputable public pages, cancellation solely due to low sales is usually low probability, while operational/weather/airspace factors remain possible.

## User-facing phrasing

Be explicit when correcting flight identity:

> “For 10:25, I’m seeing DP6843. DP6841 appears to be the earlier ~08:00 flight. So for your departure time, ориентируемся на DP6843.”

Do not overclaim “X seats sold” unless a live seat map was actually opened and counted.
