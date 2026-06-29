# Kazan → Morocco via Istanbul routing notes (June 2026)

Use this as an example pattern for budget international routing when live booking pages are partly blocked or only expose indicative prices.

## User goal

Russian-speaking user wanted the cheapest practical near-term way from Kazan to Morocco, preferably Kazan → Istanbul → Morocco, plus visa/travel basics.

## Useful source pattern

- Use current date first (`date`) to frame “near-term”.
- Search broad route options, then verify leg viability with schedule pages.
- FlightConnections route pages gave durable operational facts:
  - KZN → IST: 5 flights/week, departure window about 07:20–13:35, duration about 5h25m; airlines shown included Nordwind and Turkish Airlines.
  - IST → CMN: 4 flights/week, departure window about 11:45–18:20, duration about 4h50m; Royal Air Maroc and Turkish Airlines.
  - IST → RAK: 2 flights/week, departure window about 11:50–19:30, duration about 5h15m; Turkish Airlines.
- DOM extraction worked better than snapshots for the summary block:
  - `document.body.innerText.match(/Istanbul to Casablanca Flights[\s\S]*?Start planning/)?.[0]`
  - `document.body.innerText.match(/Kazan to Istanbul Flights[\s\S]*?Start planning/)?.[0]`
- Schema.org event snippets in scripts exposed active week windows such as 2026-07-05 → 2026-07-12, but not always exact weekdays/times. Treat them as “weeks to check”, not confirmed itinerary rows.
- Trip.com exposed an indicative KZN → CMN “from ~$430 one-way” style fare, but did not expose a fully bookable convenient connection in the scraped page. Label as indicative.

## Recommendation logic from the session

- Prefer **Kazan → Istanbul → Casablanca (KZN → IST → CMN)** for practicality because Casablanca has more direct flights from Istanbul than Marrakech.
- Consider **Kazan → Istanbul → Marrakech (KZN → IST → RAK)** when tourism value matters more than frequency, but warn that IST → RAK is less frequent.
- For separate tickets, avoid tight self-connects. Recommend 5–6+ hours minimum, 7–10 hours comfortable, or overnight in Istanbul if the user prioritizes reliability.
- If the Morocco entry hub is Casablanca, explain onward domestic train/bus to Marrakech/Fes/Rabat rather than forcing a more expensive direct Marrakech itinerary.

## Communication pattern

- Be explicit about confidence: “schedule source says frequency/windows” vs “OTA shows indicative fare”.
- Do not claim “all tickets found” if booking engines did not expose exact live fare cards.
- Give route codes and first date windows to check rather than vague advice.
