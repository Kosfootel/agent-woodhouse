"""iCloud Calendar via CalDAV."""
import os, re
from datetime import datetime, timedelta

def _load_env(path="/Users/FOS_Erik/.openclaw/workspace/credentials/icloud-calendar.env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

ICLOUD_USER = os.environ.get("ICLOUD_CALDAV_USER", "erikdross@me.com")
ICLOUD_PASS = os.environ.get("ICLOUD_CALDAV_PASS", "")
ICLOUD_URL = os.environ.get("ICLOUD_CALDAV_URL", "https://p149-caldav.icloud.com/195531740/calendars/")

# Map family calendar IDs
FAMILY_CALENDAR_NAMES = {
    "1878bc23-cca1-45b3-a876-47d6b3cce509": "Reminders",
    "1ABCB27E-ED4E-4FD5-8C8F-62CA10D3609E": "Family",
    "1C05D81C-E6B4-4123-B17A-C6CA97C52DBA": "Family2",
    "1f8aa3b4b921985ff986b3163db9be99c0834dc0add017ff03c92dc6bf475e96": "Family3",
    "39D9F1EF-E285-4EC6-8228-F088206CF0A3": "Hockey Practice",
    "8f64e4fe62ba9082a54f2d71335089e41b1fa488aa47d24cf2086a6181a48111": "Hockey Shared",
    "e2d944087998e7180bcd9594497eba9a280433b036babea390de7ea3c21c7163": "Leah",
    "21ac487d688b5372dd1a7527f405b22d6b81c7e3146cce56f956dfab08d68017": "Felix",
    "fb231b93f6b320ab9f8dd16df0c15cdd480327ad0051c7f3be898467741a9b91": "Emma",
}

def get_calendar_events():
    """Fetch iCloud calendar events via CalDAV."""
    try:
        import caldav
    except ImportError:
        return {"error": "caldav library not installed (pip install caldav)"}
    try:
        client = caldav.DAVClient(ICLOUD_URL, username=ICLOUD_USER, password=ICLOUD_PASS)
        principal = client.principal()
        calendars = principal.calendars()
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = now + timedelta(days=2)
        all_events = []
        for cal in calendars:
            try:
                events = cal.date_search(now, end)
            except Exception:
                continue
            cal_name = cal.name or ""
            cal_id = cal.id or ""
            # Determine family calendar friendly name
            family_name = FAMILY_CALENDAR_NAMES.get(cal_id, cal_name)
            is_family = family_name in ("Leah", "Felix", "Emma") or "family" in family_name.lower()
            for ev in events:
                try:
                    vevent = ev.icalendar_instance.walk("VEVENT")
                    if not vevent:
                        continue
                    for component in vevent:
                        summary = str(component.get("summary", ""))
                        start_dt = component.get("dtstart")
                        end_dt = component.get("dtend")
                        start = start_dt.dt.isoformat() if start_dt else None
                        end = end_dt.dt.isoformat() if end_dt else None
                        if start:
                            all_events.append({
                                "subject": summary,
                                "start": start,
                                "end": end,
                                "location": str(component.get("location", "")),
                                "source": "iCloud",
                                "calendar": family_name,
                                "family": is_family,
                                "account": ICLOUD_USER,
                            })
                except Exception:
                    continue
        all_events.sort(key=lambda x: x.get("start", ""))
        return all_events
    except Exception as e:
        return {"error": str(e)}
