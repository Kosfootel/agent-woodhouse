"""Microsoft Graph API client for M365 mail and calendar."""
import os, requests, json, urllib.parse
from datetime import datetime, timedelta

# Load credentials from env file if not already in environment
def _load_env(path="/Users/FOS_Erik/.openclaw/workspace/credentials/m365.env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line=line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k,v=line.split("=",1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

CLIENT_ID = os.environ.get("M365_CLIENT_ID")
CLIENT_SECRET = os.environ.get("M365_CLIENT_SECRET")
TENANT_ID = os.environ.get("M365_TENANT_ID")
AUTHORITY = os.environ.get("M365_AUTHORITY", f"https://login.microsoftonline.com/{TENANT_ID}")
ENDPOINT = os.environ.get("M365_GRAPH_ENDPOINT", "https://graph.microsoft.com/v1.0")

def get_access_token():
    url = f"{AUTHORITY}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    r = requests.post(url, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def _headers():
    return {"Authorization": f"Bearer {get_access_token()}", "Content-Type": "application/json"}

def get_mail_unread(mailbox: str, max_items: int = 30):
    """Fetch unread mail from a shared/delegate mailbox."""
    # Use /users/{mailbox}/messages with $filter
    url = f"{ENDPOINT}/users/{urllib.parse.quote(mailbox)}/messages"
    params = {
        "$filter": "isRead eq false",
        "$select": "subject,receivedDateTime,from,isRead,importance",
        "$top": max_items,
        "$orderby": "receivedDateTime desc",
    }
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    if r.status_code == 200:
        data = r.json().get("value", [])
        return [{"subject": m.get("subject"),"from":m.get("from",{}).get("emailAddress",{}).get("name",""),"received":m.get("receivedDateTime"),"importance":m.get("importance","normal")} for m in data]
    else:
        return {"error": r.status_code, "text": r.text[:500]}

def get_calendar_events(mailbox: str, days: int = 2):
    """Fetch calendar events for today + next days."""
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = now.isoformat() + "Z"
    end = (now + timedelta(days=days)).isoformat() + "Z"
    url = f"{ENDPOINT}/users/{urllib.parse.quote(mailbox)}/calendarView"
    params = {
        "startDateTime": start,
        "endDateTime": end,
        "$select": "subject,start,end,location,showAs",
        "$orderby": "start/dateTime asc",
        "$top": 50,
    }
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    if r.status_code == 200:
        data = r.json().get("value", [])
        return [{"subject":e.get("subject"),"start":e.get("start",{}).get("dateTime"),"end":e.get("end",{}).get("dateTime"),"location":e.get("location",{}).get("displayName",""),"showAs":e.get("showAs",""),"source":"M365","account":mailbox} for e in data]
    else:
        return {"error": r.status_code, "text": r.text[:500]}

def get_mailboxes_unread():
    """Fetch unread mail for both hockeyops mailboxes."""
    results = {}
    for mb in ["erik_ross@hockeyops.ai", "admin@hockeyops.ai"]:
        results[mb] = get_mail_unread(mb)
    return results

def get_calendar_events_both():
    """Fetch calendar events for both hockeyops mailboxes."""
    all_events = []
    for mb in ["erik_ross@hockeyops.ai", "admin@hockeyops.ai"]:
        ev = get_calendar_events(mb)
        if isinstance(ev, list):
            all_events.extend(ev)
        else:
            all_events.append({"error": True, "account": mb, "details": ev})
    return sorted(all_events, key=lambda x: x.get("start",""))
