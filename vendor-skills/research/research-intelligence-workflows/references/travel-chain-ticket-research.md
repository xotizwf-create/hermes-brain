# Travel chain ticket research notes

Use this reference for user requests like “find the cheapest train tickets and a same-day flight with low delay risk”.

## What mattered in the Брянск → Москва → Казань session

The user wanted:

- two budget train seats together from Bryansk to Moscow;
- arrival at Moscow Kievsky railway station;
- immediate onward travel to a Moscow airport;
- same-day flight to Kazan;
- dates limited to the nearest Sunday or Monday;
- disruption-aware choice because of airport restrictions / “план Ковёр”.

The useful pattern was to compare whole chains, not individual tickets:

1. Check Bryansk-1-Orlovsky → Moscow Kievsky train schedules/prices for each candidate date.
2. Prefer trains with enough adjacent-seat inventory and arrival early enough to leave a real airport buffer.
3. Check Moscow → Kazan flights for the same date and filter by feasible departure after: train arrival + station exit + airport transfer + check-in/security buffer.
4. Present at least two options:
   - cheapest viable;
   - recommended robust option.
5. State that airport-restriction timing only changes probabilities; never promise “no delays”.

## Practical heuristics

- For a rail-to-flight connection in Moscow, assume at least 3.5–4 hours from train arrival to domestic flight departure; more if changing to Sheremetyevo/Domodedovo during busy hours.
- If the user is delay-risk-sensitive, a mid-day/early-afternoon flight is usually a better recommendation than the cheapest early-morning flight when recent context includes night/early-morning restrictions.
- If a train arrives around 06:20 and the cheapest flight is 08:00, label it too tight even if technically possible.
- If the best Monday train inventory is only expensive classes or few adjacent seats, prefer Sunday even when Monday has similar flight prices.
- Give exact train/flight numbers and times, plus booking search links; do not claim seat adjacency is guaranteed unless verified inside an authenticated seat-map/booking flow.

## Output shape that worked

Use a compact table:

| Leg | What to book | Time | Why |
|---|---:|---:|---|
| Train | train number, route, class/price | depart → arrive | budget + adjacent seat likelihood |
| Transfer | station → airport | buffer estimate | not rushed |
| Flight | flight number, airline, airport | depart → arrive | risk/budget rationale |

Then add:

- “Best overall” recommendation;
- “Cheaper but riskier” alternative;
- direct purchase/search links;
- one-line caveat about live prices and seats changing quickly.
