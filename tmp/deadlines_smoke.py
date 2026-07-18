"""Live read-only smoke of the new deadline rules on prod (no writes)."""
import sys
from datetime import date, datetime

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402  (must come first: zoom imports back from app at module load)
import business_hours as bh  # noqa: E402
import zoom  # noqa: E402

now = bh.msk_now()
print("now MSK:", now.strftime("%A %d.%m.%Y %H:%M"))

iso, text = zoom.zoom_dispatch_deadline({})
print("zoom lead deadline if dispatched now:", text, "| iso:", iso)

for label, probe in [
    ("morning 10:00", now.replace(hour=10, minute=0)),
    ("15:01", now.replace(hour=15, minute=1)),
    ("evening 19:30", now.replace(hour=19, minute=30)),
]:
    d = bh.zoom_lead_deadline_at(probe)
    print(f"zoom rule @{label}: -> {bh.format_deadline_msk(d)}")

for anchor in [date(2026, 7, 9), date(2026, 7, 10), date(2026, 7, 11)]:
    iso, text = app.owner_recommendations_task_deadline({"report_date": anchor.isoformat()}, "daily")
    print(f"recommendations for report {anchor} ({anchor.strftime('%A')}): {text}")
