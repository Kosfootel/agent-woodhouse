"""Google services: Gmail via IMAP and Google Calendar via API."""
import os, imaplib, email, re
from datetime import datetime, timedelta

def _load_env(path="/Users/FOS_Erik/.openclaw/workspace/credentials/gmail.env"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line=line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k,v=line.split("=",1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

GMAIL_USER = os.environ.get("GMAIL_USER", "kosfootel@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")

def get_unread_mail(max_items=30):
    """Fetch unread Gmail via IMAP."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        # Search for UNSEEN since today - 7 days
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        status, data = mail.search(None, f'(UNSEEN SINCE {date_since})')
        if status != "OK":
            return {"error": f"IMAP search failed: {status}"}
        ids = data[0].split()
        results = []
        for eid in ids[-max_items:][::-1]:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", "")
            from_ = msg.get("From", "")
            date = msg.get("Date", "")
            results.append({"subject": subject, "from": from_, "date": date})
        mail.close()
        mail.logout()
        return results
    except Exception as e:
        return {"error": str(e)}

def get_calendar_events():
    """Fetch Google Calendar events for today+tomorrow via Google Calendar API."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return {"error": "google-auth and google-api-python-client not installed"}
    # Check for token.json or credentials.json
    creds_path = "/Users/FOS_Erik/.openclaw/workspace/credentials/gmail-oauth.json"
    token_path = "/Users/FOS_Erik/.openclaw/workspace/credentials/gmail-token.json"
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)
    elif os.path.exists(creds_path):
        from google_auth_oauthlib.flow import InstalledAppFlow
        SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    if not creds:
        return {"error": "No Gmail OAuth credentials found (gmail-oauth.json or gmail-token.json missing)"}
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = (now + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime",
        maxResults=50,
    ).execute()
    items = events_result.get("items", [])
    return [{"subject": e.get("summary",""),"start":e.get("start",{}).get("dateTime",e.get("start",{}).get("date","")),"end":e.get("end",{}).get("dateTime",e.get("end",{}).get("date","")),"location":e.get("location",""),"source":"Google","account":GMAIL_USER} for e in items]
