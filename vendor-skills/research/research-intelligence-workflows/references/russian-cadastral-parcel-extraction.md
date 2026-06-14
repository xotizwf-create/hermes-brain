# Russian public cadastral parcel extraction notes

Use when the user asks to collect land parcels/objects around a cadastral number, fill
addresses/VRI/distances/compass side, or produce an Excel table from the public cadastral
map (Росреестр / НСПД / ПКК).

## TL;DR — there are two engines; pick by what egress IP you have

| Engine | Source | Completeness | Needs |
|---|---|---|---|
| **`nspd_parcels_local.py`** (preferred) | official НСПД via `pynspd` | **complete** (every object) | a **Russian residential/mobile IP** |
| `nspd_parcels.py` (fallback) | public mirror `kadastrmapp.online` | **partial** (mirror caps at 81/quarter) | any IP that can reach the mirror |

Run BOTH with a Python that has shapely/pyproj/openpyxl/pynspd (the `terminal` tool's
`/usr/bin/python3` does NOT; the hermes venv `/usr/local/lib/hermes-agent/venv/bin/python` does).

```
# complete (from a RU residential IP or via a RU proxy):
.../venv/bin/python nspd_parcels_local.py 18:30:000423:1789 --radius 100 --objects all
# fallback (partial, from the server's normal egress):
.../venv/bin/python nspd_parcels.py       18:30:000423:1789 --radius 100 --objects all
```
`--objects land` = land parcels only (matches the "земельный участок/ВРИ" columns);
`--objects all` = + buildings/structures (garages are usually ОКС here). Output `.xlsx` →
deliver as `MEDIA:`.

## The IP problem (this is the whole ballgame) — confirmed 2026-06-14

- **nspd.gov.ru / pkk.rosreestr.ru are unreachable from our servers** (`http=000`/timeout),
  even via the Russian `eth0`. НСПД blocks **datacenter IPs in general** (not only foreign
  ones), so "route via a RU server" does NOT help. A RU VPS/datacenter proxy also fails.
- НСПД answers only from **residential/mobile** IPs. Options, best first:
  1. **RU residential/mobile proxy** → `Nspd(client_proxy="http://user:pass@host:port")`. Store
     the secret in the secure zone. This is the only fully-automated, server-side, 24/7 path.
  2. **The owner's home PC with the VPN OFF** (its real RU home IP). The PC also runs AmneziaVPN
     (egress was CZ `95.85.243.43`), so it must be toggled off briefly. A route-only split-tunnel
     does NOT work — WireGuard's kill-switch (WFP) blocks untunneled traffic. To survive the
     Claude session dropping during the VPN-off window, run a **detached "armed" capture** that
     polls НСПД by DIRECT IP (`2.63.246.75`, DNS-free — DNS dies when the VPN drops) and extracts
     the moment the path opens; read the result file afterwards. (See the capture pattern used in
     this incident.)
- The public mirror `https://kadastrmapp.online/api.php?query=<num>&thematicSearchId=1` (headers
  `User-Agent: Mozilla/5.0`, `Referer/Origin: https://kadastrnomer.ru/`) works from the VPN
  egress but is **hard-capped at 81 objects/quarter and ignores limit/offset/page** — partial
  only. `test.fgishub.ru` (a spatial GetFeatureInfo proxy) is intermittently down.

## pynspd method (the complete one) — and the silent-300 gotcha

- Use `find_landplot(cn)` for the target, then enumerate the buffer with the layer searches:
  `Layer36048Feature` = land parcels, `Layer36049Feature` = buildings.
- **DO NOT trust a single `search_*_in_contour` call.** It POSTs the whole contour to
  `/api/geoportal/v1/intersects`, and НСПД **silently truncates at ~300** (no error → the
  library's own recursive splitter never fires). You MUST tile: recursively split the bbox into
  quadrants, re-querying any tile that returns ≥~250 features OR raises `TooBigContour`, dedupe by
  `cad_num`. `nspd_parcels_local.py:collect_complete()` implements this. (Real example: a single
  call returned 300; tiling found 339 land parcels in the bbox → 299 within the 100 m buffer.)
- `pynspd` returns lon/lat (EPSG:4326). Reproject to local UTM (Удмуртия = EPSG:32639) for metres.
  Construct `Nspd(client_dns_resolve=True, client_retry_on_blocked_ip=True)` to hit НСПД by IP
  (avoids DNS dependency) and ride out blocked-IP retries.

## Geometry / table rules (both engines)

- Geometry CRS: mirror = EPSG:3857, pynspd = EPSG:4326. **Never measure distance in raw 3857**
  (×1.8 error at 56°N → "100 m" ≈ 55 m). Reproject to UTM and measure there.
- Distance = **boundary-to-boundary** from the union of the target's contours (buffer the
  boundary, not the centre); touching/intersecting = 0 m.
- Compass side = bearing target-centroid → object-centroid, 8 sectors С/СВ/В/ЮВ/Ю/ЮЗ/З/СЗ.
- Columns the owner wants: `№`, `Номер земельного участка`, `Адрес...`, `Вид разрешенного
  использования участка`, `Расстояние от участка <cad>, м`, `Сторона света`, (+`Площадь, кв. м`,
  `Статус`; +`Тип объекта` in `--objects all`). Second sheet "Источник" with method + ЕГРН caveat.
- Write under `/root/.hermes/outbox/`, verify with `openpyxl` (reopen, row count) before sending.

## Caveats to state to the user

- Open public НСПД/Росреестр data — good for a working table. For legally significant use, confirm
  with an official ЕГРН extract.
- State that the radius was computed from available public geometries via spatial search.
