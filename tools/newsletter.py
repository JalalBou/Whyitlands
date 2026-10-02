#!/usr/bin/env python3
"""Build the weekly WhyItLands newsletter email from content/.

Usage: python3 tools/newsletter.py [YYYY-MM-DD]   (send date, a Monday; default: next Monday)
Reads content/newsletter.json for the editorial choices of the week:
  {"send_date": "2026-10-05", "subject": "...", "preview": "...", "minute": ["...", "...", "..."],
   "lead": "briefing-slug", "number": {"big": "$104.46", "label": "..."}, "doctrine": "doctrine-key"}
Writes newsletter/<send_date>.html. A GitHub Action turns each new file into a scheduled Brevo campaign.
"""
import datetime, glob, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "content"
E = html.escape
SITE = "https://www.whyitlands.com"
LI = json.loads((C / "settings.json").read_text()).get("linkedin", "") or SITE
plain = lambda s: re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)

cfg = json.loads((C / "newsletter.json").read_text()) if (C / "newsletter.json").exists() else {}
if len(sys.argv) > 1:
    send = datetime.date.fromisoformat(sys.argv[1])
elif cfg.get("send_date"):
    send = datetime.date.fromisoformat(cfg["send_date"])
else:
    t = datetime.date.today()
    send = t + datetime.timedelta(days=(7 - t.weekday()) % 7 or 7)
week = send.isocalendar()[1]

B = {}
for f in glob.glob(str(C / "briefings" / "*.json")):
    b = json.loads(open(f).read())
    B[b["slug"]] = b
imp = lambda s: next((x["impact"] for x in B[s]["body"] if "impact" in x), "")
lead = B.get(cfg.get("lead")) or sorted(B.values(), key=lambda b: b["date"], reverse=True)[0]
RN = [("EU", "EU"), ("UK", "UK"), ("ME", "Middle East"), ("NAF", "North Africa"), ("NA", "North America"), ("SA", "South America"), ("CN", "China"), ("NEA", "North Asia"), ("SEA", "Southeast Asia"), ("SAS", "South Asia"), ("OCE", "Oceania")]
by_region = {}
for b in sorted(B.values(), key=lambda b: b["date"], reverse=True):
    by_region.setdefault(b.get("region"), b)

regions = json.loads((C / "regions.json").read_text())
home = json.loads((C / "home.json").read_text())
PERS = cfg.get("personalise", True)
coming = []
for k, r in regions.items():
    for c in r["coming"]:
        if re.match(r"^\d{1,2}[\s–-]", c["when"]) and c["date"] >= send.isoformat():
            coming.append(c)
for c in home.get("global_coming", []):
    if c["date"] >= send.isoformat() and all(c["what"][:25] != x["what"][:25] for x in coming):
        coming.append(c)
for _rf in sorted((C / "radar").glob("*.json")) if (C / "radar").exists() else []:
    for _it in json.loads(_rf.read_text()).get("items", []):
        for _d in _it.get("dates", []):
            if send.isoformat() <= _d["date"] <= (send + datetime.timedelta(days=120)).isoformat():
                coming.append({"date": _d["date"], "when": datetime.date.fromisoformat(_d["date"]).strftime("%-d %b %Y"), "what": _it["title"], "regions": _it.get("regions", []), "radar": _it["key"]})
_seen, _c2 = set(), []
for c in sorted(coming, key=lambda c: c["date"]):
    k_ = (c["date"], c["what"][:30])
    if k_ not in _seen:
        _seen.add(k_); _c2.append(c)
coming = _c2[:14] if PERS else _c2[:6]
def c_regs(c):
    return c.get("regions") or ([c["region"]] if c.get("region") else [])

doc = None
if (C / "doctrines.json").exists():
    d = json.loads((C / "doctrines.json").read_text())
    doc = next((s for s in d["schools"] if s["key"] == cfg.get("doctrine")), d["schools"][week % len(d["schools"])])

minute = cfg.get("minute") or [plain(k) for k in lead["keypoints"][:3]]
number = cfg.get("number")
subject = cfg.get("subject") or f"WhyItLands · Week {week}: {lead['title']}"
preview = cfg.get("preview") or plain(lead["dek"])[:140]

# (personalisation flags defined near the top)
# Personalisation: Brevo template conditions on the contact's REGIONS attribute (",EU,UK,").
# Contacts without REGIONS (older sign-ups) or with GLOBAL see everything. Set "personalise": false
# in content/newsletter.json to send the same content to everyone.
PERS = cfg.get("personalise", True)
EMEA_R = ["EU", "UK", "ME", "NAF"]
APAC_R = ["CN", "NEA", "SEA", "SAS", "OCE"]


def gate(regs, html_):
    if not PERS:
        return html_
    rs = set()
    for r in regs or []:
        rs.update(EMEA_R if r == "EMEA" else APAC_R if r == "APAC" else [r])
    if rs & {"NEA", "SEA", "SAS", "OCE"}:
        rs.add("AS")  # subscribers who signed up before the Asia split
    if not rs or "GLOBAL" in rs:
        return html_
    tests = " or ".join(f'",{r}," in contact.REGIONS' for r in sorted(rs))
    return '{% if contact.REGIONS == "" or ",GLOBAL," in contact.REGIONS or ' + tests + ' %}' + html_ + '{% endif %}'


F = "font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
S = "font-family:Georgia,'Times New Roman',serif"
M = "font-family:Menlo,Consolas,monospace"
U = SITE + "/briefings/"
icon = f'<img src="{SITE}/assets/img/icon-180.png" width="28" height="28" alt="" style="vertical-align:middle;border-radius:6px">'
rows = "".join(gate([k], f'''<tr><td style="padding:14px 0;border-top:1px solid #E6E3DA"><div style="{M};font-size:11px;letter-spacing:1px;color:#FF5A36;text-transform:uppercase">{E(name)}</div>
<a href="{U}{by_region[k]['slug']}" style="{S};font-size:19px;line-height:1.25;color:#0B0F1A;text-decoration:none">{E(by_region[k]["title"])}</a>
<div style="{F};font-size:14px;line-height:1.5;color:#3B4152;margin-top:4px">{E(plain(imp(by_region[k]['slug'])))}</div></td></tr>''') for k, name in RN if k in by_region and by_region[k]["slug"] != lead["slug"])
today = send
cal = "".join(gate(c_regs(c), f'<tr><td style="{M};font-size:13px;color:#FF5A36;padding:8px 12px 8px 0;white-space:nowrap">D−{(datetime.date.fromisoformat(c["date"]) - today).days}</td><td style="{M};font-size:12px;color:#5A6072;padding:8px 12px 8px 0;white-space:nowrap">{E(c["when"])}</td><td style="{F};font-size:14px;color:#0B0F1A;padding:8px 0">' + (f'<a href="{SITE}/radar#rr-{c["radar"]}" style="color:#0B0F1A">{E(c["what"])}</a>' if c.get("radar") else E(c["what"])) + '</td></tr>') for c in coming)
kp = "".join(f'<li style="margin:0 0 8px">{E(x)}</li>' for x in minute)
num = ""
if number:
    num = f'''<tr><td style="background:#FF5A36;padding:26px 30px;border-top:8px solid #F4F2EC"><div style="{M};font-size:11px;letter-spacing:1px;color:#FFD5C8">NUMBER OF THE WEEK</div>
<div style="{S};font-size:56px;line-height:1;color:#FFFFFF;margin:8px 0">{E(number["big"])}</div><div style="{F};font-size:14px;line-height:1.5;color:#FFE9E2">{E(number["label"])}</div></td></tr>'''
sthtml = ""
_stp = C / "storylines.json"
if cfg.get("storyline") and _stp.exists():
    _st = next((x for x in json.loads(_stp.read_text())["storylines"] if x["key"] == cfg["storyline"]), None)
    if _st:
        _steps = "".join(f'<tr><td style="{M};font-size:11px;letter-spacing:1px;color:#5A6072;padding:6px 12px 6px 0;white-space:nowrap;vertical-align:top">{L.upper()}</td><td style="{F};font-size:14px;line-height:1.45;color:#0B0F1A;padding:6px 0">{E(plain(_st["chain"][L][-1]["text"]))}</td></tr>' for L in ("geopolitics", "decision", "market", "parcel") if _st["chain"].get(L))
        sthtml = f'''<tr><td style="background:#FFFFFF;padding:26px 30px;border-top:8px solid #F4F2EC"><div style="{M};font-size:11px;letter-spacing:1px;color:#2B45E0">STORYLINE OF THE WEEK</div>
<a href="{SITE}/storylines/{_st['key']}" style="{S};font-size:24px;line-height:1.15;color:#0B0F1A;text-decoration:none;display:block;margin:8px 0 10px">{E(_st['title'])}</a>
<table cellpadding="0" cellspacing="0">{_steps}</table><a href="{SITE}/storylines/{_st['key']}" style="{F};font-size:14px;color:#2B45E0;display:inline-block;margin-top:10px">Follow the full chain →</a></td></tr>'''
dhtml = ""
if doc:
    dhtml = f'''<tr><td style="background:#0B0F1A;padding:26px 30px;border-top:8px solid #F4F2EC"><div style="{M};font-size:11px;letter-spacing:1px;color:#D7F75B">DOCTRINE OF THE WEEK</div>
<div style="{S};font-size:22px;color:#FFFFFF;margin:8px 0 6px">{E(doc["name"])}</div><div style="{F};font-size:14px;line-height:1.55;color:#C8CCD6">{E(plain(doc["parcel"]))}</div>
<a href="{SITE}/doctrines#{E(doc["key"])}" style="{F};font-size:14px;color:#D7F75B;display:inline-block;margin-top:10px">All doctrines explained →</a></td></tr>'''

out = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{E(subject)}</title><meta name="wil-preview" content="{E(preview)}"><meta name="wil-send" content="{send.isoformat()}"></head>
<body style="margin:0;background:#F4F2EC">
<div style="display:none;max-height:0;overflow:hidden">{E(preview)}</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F2EC"><tr><td align="center" style="padding:24px 12px">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">
<tr><td style="background:#0B0F1A;border-radius:20px 20px 0 0;padding:26px 30px"><table width="100%"><tr><td style="{F};font-size:22px;font-weight:700;color:#F4F2EC">WhyItLands {icon}</td><td align="right" style="{M};font-size:11px;letter-spacing:1px;color:#8C93A6">WEEK {week} · {send.strftime("%d %b %Y").upper()}</td></tr></table>
<div style="{S};font-style:italic;font-size:17px;color:#C8CCD6;margin-top:6px">Where it lands, and why.</div></td></tr>
<tr><td style="background:#0B0F1A;padding:6px 30px 30px"><div style="{M};font-size:11px;letter-spacing:1px;color:#D7F75B">THE WEEK IN ONE MINUTE</div><ul style="{F};font-size:15px;line-height:1.5;color:#F4F2EC;padding-left:18px;margin:12px 0 0">{kp}</ul></td></tr>
<tr><td style="background:#FFFFFF;padding:30px"><div style="{M};font-size:11px;letter-spacing:1px;color:#FF5A36">THE LEAD · {E(lead["section"].upper())}</div>
<a href="{U}{lead['slug']}" style="{S};font-size:28px;line-height:1.15;color:#0B0F1A;text-decoration:none;display:block;margin:10px 0 12px">{E(lead['title'])}</a>
<div style="{F};font-size:15px;line-height:1.6;color:#3B4152">{E(plain(lead['dek']))}</div>
<div style="background:#D7F75B;border-radius:12px;padding:14px 16px;margin:18px 0"><div style="{M};font-size:11px;letter-spacing:1px;color:#4A5A0B">WHAT IT MEANS FOR YOU</div><div style="{F};font-size:15px;line-height:1.5;color:#0B0F1A;margin-top:4px">{E(plain(imp(lead['slug'])))}</div></div>
<a href="{U}{lead['slug']}" style="{F};display:inline-block;background:#FF5A36;color:#FFFFFF;font-weight:700;font-size:15px;text-decoration:none;padding:12px 22px;border-radius:999px">Read the analysis</a></td></tr>
<tr><td style="background:#FFFFFF;padding:0 30px 10px;border-top:8px solid #F4F2EC"><div style="{M};font-size:11px;letter-spacing:1px;color:#5A6072;padding-top:24px">{'YOUR REGIONS' if PERS else 'BY REGION'}</div><table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px">{rows}</table></td></tr>
{sthtml}
{num}
<tr><td style="background:#FFFFFF;padding:26px 30px;border-top:8px solid #F4F2EC"><div style="{M};font-size:11px;letter-spacing:1px;color:#5A6072">WHAT’S COMING</div><table cellpadding="0" cellspacing="0" style="margin-top:8px">{cal}</table>
<a href="{SITE}/radar" style="{F};font-size:14px;color:#2B45E0;display:inline-block;margin-top:14px">Every rule and deadline: Regulatory Radar →</a><br><a href="{SITE}/markets" style="{F};font-size:14px;color:#2B45E0;display:inline-block;margin-top:6px">Signals, prices and results: Market Intelligence →</a></td></tr>
{dhtml}
<tr><td style="padding:24px 30px;{F};font-size:12px;line-height:1.6;color:#5A6072;text-align:center">Spotted an error or have a tip? <a href="{LI}" style="color:#5A6072">Message Jalal Boucheikha on LinkedIn</a>.<br>Researched and written with AI under Jalal Boucheikha’s editorial rules. Every fact is sourced on the site.<br>
You receive this because you subscribed at whyitlands.com. <a href="{{{{ update_profile }}}}" style="color:#2B45E0">Update your preferences</a> · <a href="{{{{ unsubscribe }}}}" style="color:#2B45E0">Unsubscribe</a></td></tr>
</table></td></tr></table></body></html>'''
dst = ROOT / "newsletter" / f"{send.isoformat()}.html"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out + f"\n<!-- generated {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC -->\n")
print(dst.relative_to(ROOT), "|", subject)
