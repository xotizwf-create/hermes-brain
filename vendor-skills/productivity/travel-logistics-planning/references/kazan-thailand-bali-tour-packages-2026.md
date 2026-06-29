# Kazan → Thailand vs Bali package-tour comparison, 2026

Session pattern: Александр asked in voice for an autumn resort comparison from Kazan, only good 4★+ hotels, no 3★, all inclusive, price in rubles.

## Useful extraction pattern

1001 Тур pages were readable through browser when some other aggregators were blank/behind verification. After opening a filtered page, use:

```js
document.body.innerText.match(/Сортировать по:[\s\S]{0,9000}/)?.[0]
```

This captures visible offer cards, board type, dates, nights, prices, and the “Цены обновлены...” timestamp.

## URLs that exposed useful package filters

- Thailand 4★ all inclusive from Kazan: `https://kazan.1001tur.ru/tailand/tury/hotel_4/food_allinclusive/`
- Bali 4★ all inclusive from Kazan: `https://kazan.1001tur.ru/indonezia/tury/bali/hotel_4/food_allinclusive/`
- Bali 5★ all inclusive from Kazan: `https://kazan.1001tur.ru/indonezia/tury/bali/hotel_5/food_allinclusive/`
- General Bali from Kazan: `https://kazan.1001tur.ru/indonezia/tury/bali/`
- Thailand 4★ from Kazan: `https://kazan.1001tur.ru/tailand/tury/hotel_4/`

## Findings from 28.06.2026 run

Aggregator default visible on the pages: generally 2 adults, July window, 6–11 nights depending offer. Treat as live indicative pricing, not a guaranteed quote.

### Thailand 4★ all inclusive

Found real all-inclusive 4★ offers, mostly Phuket / Khao Lak / Koh Chang. Examples visible:

- Zenseana Resort 4★, Phuket, all inclusive, 6 nights from ~239,978 ₽ for two.
- Chanalai Hillside Resort 4★, Phuket, all inclusive, 7 nights from ~240,743 ₽ for two.
- Chanalai Flora Resort 4★, Phuket, all inclusive, 6 nights from ~250,678 ₽ for two.
- Kantary Beach Hotel Villas & Suites 4★, Khao Lak, all inclusive, 6 nights from ~254,990 ₽ for two.
- Chanalai Garden Resort 4★, Phuket, all inclusive, 6 nights from ~255,422 ₽ for two.
- Novotel Phuket Kamala Beach 4★, Phuket, all inclusive, 6 nights from ~274,396 ₽ for two.

Practical conclusion: under strict 4★+ all-inclusive constraints, Thailand starts around 240k ₽ for two; comfortable planning range 270–330k ₽ for two.

### Bali 4★ all inclusive

Filtered page returned no offers for `4★ + all inclusive + from Kazan`:

> Туров не найдено ... туры в Индонезию в отели 4 звезды все включено из Казани.

Do not fill this gap with breakfast/no-meal offers in the main comparison. Mention those only as a relaxed alternative.

### Bali 5★ all inclusive

Only one visible all-inclusive valid alternative:

- Grand Mirage Resort & Thalasso Bali 5★, Nusa Dua, 1st line, all inclusive, 9 nights from ~430,102 ₽ for two.

Practical conclusion: strict all-inclusive Bali is much more expensive; minimum observed around 430k ₽ for two.

### Bali 4★ relaxed board

General Bali offers existed around 173–181k ₽ for two, but mostly breakfast/no meal and often with lower-rated or 3★-ish options. Examples included 4★-rated properties with breakfast/no board, but this does not satisfy “all inclusive.”

## Answering style that worked

- Start with the verdict: Thailand is cheaper under exact constraints.
- Give price table: destination, exact package match, price for two, approximate per-person.
- Separate strict requirement from relaxed alternative.
- Say plainly that Bali’s all-inclusive concept is rare and mostly 5★, while Thailand has more package inventory.
- Avoid overloading with raw URLs/commands in the final user-facing reply unless requested.
