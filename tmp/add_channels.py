"""Add the owner's 49 public channels to the digest watchlist (via the real tg_agent logic)."""
import sys

sys.path.insert(0, "/var/www/albery")
import tg_agent  # noqa: E402

tg_agent._load_env_file()

RAW = """
https://t.me/vitaecom
@mkeeper
@redman
https://t.me/robo_wb
https://t.me/sellermp
https://t.me/wbsellerofficial
https://t.me/wbpopolochcam
https://t.me/ekspertmp
https://t.me/tigranwb
https://t.me/wbbillion
https://t.me/andrey_pro_business
https://t.me/postavleno
https://t.me/nashputwildberries
https://t.me/kudahiko
https://t.me/wbcon
https://t.me/marketplace_hogwarts
https://t.me/centWB
https://t.me/wbsharks
https://t.me/maxprowb
https://t.me/art_ecom
https://t.me/seotrener1
https://t.me/sonbokalchuk
https://t.me/finamp
https://t.me/novak_WB
https://t.me/vladlen_strokan
https://t.me/polagushin_clo
https://t.me/marpla_wildberries
https://t.me/tarbakristina
https://t.me/aliance_wb
https://t.me/steputenkov
https://t.me/alfedyaev
https://t.me/ivansergeevlife
https://t.me/marketpapa_channel
https://t.me/wbradarbidder
https://t.me/threeyearsonwb
https://t.me/olegnevorotov
https://t.me/vikenot
https://t.me/riazanov_top100
https://t.me/mpanalitik
https://t.me/WBusinesss24
https://t.me/iz_kioska_v_business
https://t.me/SEO_for_WB
https://t.me/fullstats
https://t.me/jvochannel
https://t.me/p_shevchenko
https://t.me/artem_grigoryev
https://t.me/marketpraktik
https://t.me/nasya_ok
https://t.me/wb_nisha
https://t.me/whoismaxbellini
"""

good, bad = [], []
for raw in RAW.split():
    name = tg_agent.normalize_channel(raw)
    (good.append(name) if name else bad.append(raw))

tg_agent.set_channels(tg_agent.channels() + good)
final = tg_agent.channels()
print(f"parsed_ok={len(good)} rejected={bad}")
print(f"watchlist now has {len(final)} channels")
print("sample:", final[:8])
