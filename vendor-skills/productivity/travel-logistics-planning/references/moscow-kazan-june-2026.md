# Moscow/Kazan planning example — June 2026

This reference captures reusable details from a session planning Брянск → Москва → Казань travel and answering Aeroflot/BlaBlaCar questions. Treat prices/schedules as examples only; always re-check live data for future dates.

## Yandex Rasp extraction pattern

Yandex Rasp pages may ignore the `?date=` parameter and open in “all days” mode. If so:

1. Open the route page in browser.
2. Click the calendar date manually.
3. Extract table rows from the page rather than relying on the accessibility snapshot:

```js
Array.from(document.querySelectorAll('table tr'))
  .slice(0, 80)
  .map(tr => tr.innerText)
  .filter(Boolean)
  .join('\n---\n')
```

Useful fields to preserve: train/flight number, route, departure/arrival time, stations/airports, duration, seat classes/remaining seats, minimum price.

## Example train findings: Брянск-1-Орловский → Москва Киевская, Tue 2026-06-30

- 086Щ Новозыбков → Москва: 00:20 → 06:30, 6h10m; плацкарт 7 seats from 2,304 ₽; купе 41 from 4,252 ₽; СВ 12 from 7,442 ₽.
- 738А Брянск → Москва daytime express: 06:57 → 11:05, 4h08m; сидячие 81 from 2,629 ₽; купе 50 from 3,656 ₽.
- 240Щ: 13:21 → 17:31, not suitable for same-day afternoon Moscow flight.
- 742В: 19:02 → 23:10, evening option only.

Reasoning lesson: the 00:20 train gives a large Moscow buffer before a mid-afternoon flight, but low remaining плацкарт seats make it time-sensitive.

## Example flight findings: Москва → Казань, Tue 2026-06-30

- DP 6841 Победа: 08:00 → 09:40, from 3,884 ₽.
- DP 6843 Победа: 10:25 → 12:05, from 3,879 ₽; cheap but tighter after 06:30 train arrival.
- N4 6509 Nordwind: 12:35 → 14:05, from 4,918 ₽.
- FV/SU 6361 Россия/Аэрофлот: 15:20 → 17:00, from 5,082 ₽; good balance after train arrival.
- Later evening flights existed, including Smartavia/Nordwind/Aeroflot options.

Reasoning lesson: for train → plane in Moscow, a mid-afternoon flight can beat the cheapest morning flight because the connection risk drops sharply.

## Aeroflot hand-luggage/toiletry answer pattern

When official Aeroflot pages are blocked by WAF, search results and multiple secondary sources can still support an answer, but say the official page could not be opened from the server.

Reusable content to verify each time:

- Economy/Comfort carry-on: usually 1 item up to 10 kg, 55 × 40 × 25 cm.
- Business: usually up to 15 kg, same dimensions.
- Liquids/gels/aerosols/creams/pastes in cabin: containers up to 100 ml each, total about 1 liter, preferably transparent bag. Container capacity matters, not remaining amount.
- Perfume: OK if ≤100 ml.
- Shaving foam/gel: OK only if canister ≤100 ml; common 200–300 ml cans are not OK in hand luggage.
- Razors: disposable, cartridge/Gillette-style, electric generally OK; straight razors, loose blades, and removable double-edge blades not OK in hand luggage.

## BlaBlaCar Москва → Казань answer pattern

Search results showed a route page with roughly 44 rides and starting price around 1,250 ₽, but live listing was blocked by DataDome. Future answers should not invent drivers/cars.

Selection heuristics for long rides:

- Good budget/comfort target: roughly 1,800–2,500 ₽ per person if live prices are similar.
- Prefer comfortable sedans/crossovers: Camry, K5/Optima, Sonata, Superb/Octavia, Passat, Mercedes/BMW/Audi, Tiguan/RAV4/Sportage/Tucson/X-Trail.
- Avoid tiny cars for 10–13 hour rides with luggage.
- Prefer drivers with reviews, high rating, car photo, clear pickup point, baggage permission, and “max 2 passengers in back”.
- Avoid 3 in the back, no reviews, suspiciously cheap offers, or off-platform prepayment.
- Morning departure is usually best for Moscow → Kazan by car.

## Style lesson

For Александр’s voice-message travel questions, answer in Russian, practical and friendly. Tables are useful, but keep them compact and lead with the direct recommendation before details.