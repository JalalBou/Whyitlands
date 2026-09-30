#!/usr/bin/env python3
"""Create a scheduled Brevo campaign for each newsletter file passed as argument.

The file's <title> is the subject, <meta name="wil-preview"> the preview text and
<meta name="wil-send"> the send date (sent at 07:30 Europe/Paris that day).
Needs env BREVO_API_KEY; optional BREVO_LIST_ID (default 2), SENDER_EMAIL.
"""
import datetime, json, os, re, sys, urllib.request, zoneinfo, html

KEY = os.environ.get("BREVO_API_KEY", "")
if not KEY:
    print("::error::BREVO_API_KEY secret is missing in GitHub (Settings > Secrets and variables > Actions)")
    sys.exit(1)
LIST = int(os.environ.get("BREVO_LIST_ID") or 2)
SENDER = os.environ.get("SENDER_EMAIL") or "hello@whyitlands.com"


def call(method, path, body=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"api-key": KEY, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read().decode()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        msg = f"Brevo {e.code} on {path}: {e.read().decode()[:400]}"
        print("::error::" + msg.replace("\n", " "))
        sys.exit(1)


def pick_sender():
    """Use the configured sender if Brevo lists it as active, else the first active whyitlands.com sender."""
    try:
        req = urllib.request.Request("https://api.brevo.com/v3/senders", headers={"api-key": KEY, "Accept": "application/json"})
        with urllib.request.urlopen(req) as r:
            senders = json.loads(r.read().decode()).get("senders", [])
    except Exception as e:
        print(f"::warning::could not list Brevo senders: {e}")
        return {"name": "WhyItLands", "email": SENDER}
    print("::notice::Brevo senders: " + "; ".join(f"{x.get('id')} {x.get('email')} active={x.get('active')}" for x in senders))
    for x in senders:
        if x.get("email", "").lower() == SENDER.lower() and x.get("active"):
            return {"id": x["id"]}
    for x in senders:
        if x.get("email", "").lower().endswith("@whyitlands.com") and x.get("active"):
            return {"id": x["id"]}
    return {"name": "WhyItLands", "email": SENDER}


SENDER_OBJ = pick_sender()

for path in sys.argv[1:]:
    src = open(path).read()
    subject = html.unescape(re.search(r"<title>(.*?)</title>", src, re.S).group(1)).strip()
    preview = html.unescape((re.search(r'name="wil-preview" content="([^"]*)"', src) or [None, ""])[1])
    send = datetime.date.fromisoformat(re.search(r'name="wil-send" content="([^"]+)"', src).group(1))
    when = datetime.datetime.combine(send, datetime.time(7, 30), zoneinfo.ZoneInfo("Europe/Paris"))
    now = datetime.datetime.now(datetime.timezone.utc)
    body = {"name": f"WhyItLands {send.isoformat()}", "subject": subject, "previewText": preview[:140],
            "sender": SENDER_OBJ, "replyTo": SENDER,
            "htmlContent": src, "recipients": {"listIds": [LIST]}}
    if when > now + datetime.timedelta(minutes=15):
        body["scheduledAt"] = when.isoformat()
    existing = None
    for status in ("queued", "draft"):
        lst = call("GET", f"/emailCampaigns?status={status}&limit=50") or {}
        existing = next((c for c in lst.get("campaigns", []) if c.get("name") == body["name"]), None)
        if existing:
            break
    if existing:
        call("PUT", f"/emailCampaigns/{existing['id']}", body)
        print(f"Campaign {existing['id']} updated for {path}: '{subject}'")
    else:
        res = call("POST", "/emailCampaigns", body)
        print(f"Campaign {res.get('id')} created for {path}: '{subject}'" + (f", scheduled {when.isoformat()}" if "scheduledAt" in body else ", saved as draft (send date passed)"))
