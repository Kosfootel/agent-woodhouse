#!/usr/bin/env python3
"""
Woodhouse iCloud CalDAV helper (Calendar + Reminders).
Credentials stored in macOS Keychain under account 'woodhouse'.
"""
import subprocess
import caldav
from datetime import datetime, timezone, timedelta

# Calendars to exclude from briefings (noisy / not Mr. Ross's own)
EXCLUDE_CALENDARS = {"Reminders ⚠️", "Family List ⚠️", "Hockey Practice (Full) ⚠️"}

# Calendars that are Mr. Ross's own (prioritise these)
PRIMARY_CALENDARS = {"Erik", "Erik added by Leah"}

def _kc(service: str) -> str:
    r = subprocess.run(
        ['security', 'find-generic-password', '-a', 'woodhouse', '-s', service, '-w'],
        capture_output=True, text=True
    )
    return r.stdout.strip()

def get_client() -> caldav.DAVClient:
    return caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=_kc("icloud_username"),
        password=_kc("icloud_app_password"),
    )

def get_calendars():
    client = get_client()
    principal = client.principal()
    return principal.calendars()

def get_events(days_ahead: int = 2, include_family: bool = True) -> list:
    """Fetch upcoming events across iCloud calendars."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)
    events_out = []

    for cal in get_calendars():
        try:
            name = cal.get_display_name() or ""
            if name in EXCLUDE_CALENDARS:
                continue
            if not include_family and name not in PRIMARY_CALENDARS:
                continue

            results = cal.search(
                start=now, end=end,
                event=True, expand=True
            )
            for e in results:
                try:
                    vevent   = e.vobject_instance.vevent
                    summary  = str(getattr(vevent, 'summary',  type('', (), {'value': '(no title)'})()).value)
                    dtstart  = getattr(vevent, 'dtstart', None)
                    location = str(getattr(vevent, 'location', type('', (), {'value': ''})()).value)
                    start_val = dtstart.value if dtstart else None
                    # Normalise to string
                    if hasattr(start_val, 'isoformat'):
                        start_str = start_val.isoformat()[:16]
                        all_day   = len(str(dtstart.value)) == 10
                    else:
                        start_str = str(start_val)[:16] if start_val else '?'
                        all_day   = True

                    events_out.append({
                        "summary":  summary,
                        "start":    start_str,
                        "all_day":  all_day,
                        "location": location,
                        "calendar": name,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    # Sort by start time
    events_out.sort(key=lambda x: x["start"])
    return events_out


def icloud_briefing():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    events = get_events(days_ahead=2)

    print(f"\n{'='*60}")
    print(f"  iCLOUD CALENDAR BRIEFING")
    print(f"  {now.strftime('%A, %d %B %Y')}")
    print(f"{'='*60}")

    if events:
        print(f"\n📅 Upcoming events (next 48h) — {len(events)} items:")
        for e in events:
            loc = f" @ {e['location']}" if e['location'] else ""
            cal = f" [{e['calendar']}]" if e['calendar'] not in PRIMARY_CALENDARS else ""
            print(f"  • {e['start']}{loc} — {e['summary']}{cal}")
    else:
        print("  Nothing on the calendar, sir.")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    icloud_briefing()
