# Magnit address-scoped delivery availability checks

Use this when the Magnit web UI is blocked or shows the generic “Выключите VPN” page, but the user needs a factual answer about whether a product can be delivered to a specific Russian address.

## Proven workflow

1. Load `https://magnit.ru/` and inspect Nuxt assets if needed:
   - Main bundle is usually under `/_nuxt/<hash>.js`.
   - Runtime config includes `omniWebApi` and the frontend calls `/webgate/...` endpoints.
2. Geocode the target address:
   - If Magnit/Yandex geocoder key fails server-side, use another source such as OSM Nominatim.
   - Keep latitude/longitude explicit in notes.
3. Find address-scoped delivery shops:
   - Endpoint: `GET https://magnit.ru/webgate/shops/v1/shop_by_point?x=<lat>&y=<lon>`
   - Magnit uses `x=latitude`, `y=longitude` for this endpoint.
   - Response returns `shops[]` with `delivery`, `delivery_type`, `formatted_address`, `xml_id`, and a partner `webview` URL.
   - For grocery delivery, prefer `delivery_type: "express"` / product shop, not cosmetic-only shops.
4. Search the store-scoped catalog:
   - Endpoint: `POST https://magnit.ru/webgate/v2/goods/search`
   - Minimal body that worked for grocery delivery:
     ```json
     {
       "term": "пельмени цезарь",
       "pagination": {"limit": 20, "offset": 0},
       "includeAdultGoods": true,
       "sort": {"order": "DESC", "type": "RELEVANCE"},
       "storeCode": "160454",
       "storeType": "1",
       "catalogType": "1"
     }
     ```
   - `storeCode` comes from `shop_by_point` (`xml_id`) or store facade `externalId.storeCode`.
   - `storeType: "1"` can be required even when `shop_by_point.delivery_type` says `express`; strings like `express` may return `invalid_service_pair`.
5. Interpret results:
   - `items[].quantity` is the observed stock for that selected store.
   - `pickupOnly: false` means it is not restricted to pickup.
   - Answer in plain language: delivery eligibility at the address, matching product names, price, stock, and whether the requested quantity fits.

## Headers

Use browser-like JSON headers to reduce false blocks:

```python
headers = {
  "User-Agent": "Mozilla/5.0 ...",
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Device-Platform": "Web",
  "X-New-Magnit": "true",
  "X-Platform-Version": "loyalty-web",
  "X-Device-Tag": "disabled",
  "X-Device-ID": str(uuid.uuid4()),
  "X-App-Version": "<version from window.__NUXT__.config.public.version>",
  "X-Client-Name": "magnit",
  "Origin": "https://magnit.ru",
  "Referer": "https://magnit.ru/"
}
```

Avoid raw Cyrillic in HTTP header values (`Referer` with an unescaped Russian query can raise `UnicodeEncodeError` in Python `requests`). URL-encode it or use a plain origin/path referer.

## Example evidence from 2026-06-07

For `Казань, Деревня Универсиады, 4`:
- OSM coordinates: `55.7438905, 49.1830744`.
- `shop_by_point` returned a grocery delivery shop: `Казань, Победы пр-кт, дом № 43`, `xml_id: 160454`, `delivery_type: express`.
- `v2/goods/search` with `storeCode=160454`, `storeType=1`, `catalogType=1`, term `пельмени цезарь` returned:
  - `Пельмени Цезарь Гордость Сибири 800г`, price `356.99`, quantity `6`, `pickupOnly=false`.
  - `Пельмени Цезарь Отборные 700г`, price `329.99`, quantity `6`, `pickupOnly=false`.

Treat these example values as historical evidence only; always rerun live checks for current availability.
