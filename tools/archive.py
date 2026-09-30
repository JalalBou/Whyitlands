#!/usr/bin/env python3
"""Snapshot the current edition before the weekly update.

python3 tools/archive.py            -> content/archive/<edition>.json (front page, briefings of the week)
python3 tools/archive.py briefing <slug>  -> content/archive/briefings/<slug>@<date>.json (keep a version before rewriting it)
"""
import glob, json, os, shutil, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "content")
A = os.path.join(C, "archive")

if len(sys.argv) > 2 and sys.argv[1] == "briefing":
    slug = sys.argv[2]
    src = next(f for f in glob.glob(os.path.join(C, "briefings", "*.json")) if json.load(open(f))["slug"] == slug)
    b = json.load(open(src))
    d = b.get("updated") or b["date"]
    os.makedirs(os.path.join(A, "briefings"), exist_ok=True)
    dst = os.path.join(A, "briefings", f"{slug}@{d}.json")
    shutil.copy(src, dst)
    print(os.path.relpath(dst, ROOT))
    sys.exit()

home = json.load(open(os.path.join(C, "home.json")))
ed = home.get("edition") or datetime.date.today().isoformat()
briefs = []
for f in sorted(glob.glob(os.path.join(C, "briefings", "*.json"))):
    b = json.load(open(f))
    briefs.append({"slug": b["slug"], "title": b["title"], "section": b["section"], "region": b.get("region"), "date": b["date"], "updated": b.get("updated")})
snap = {"edition": ed, "home": home, "briefings": briefs}
nl = os.path.join(C, "newsletter.json")
if os.path.exists(nl):
    snap["newsletter"] = json.load(open(nl))
os.makedirs(A, exist_ok=True)
json.dump(snap, open(os.path.join(A, f"{ed}.json"), "w"), ensure_ascii=False, indent=2)
print(f"content/archive/{ed}.json")
