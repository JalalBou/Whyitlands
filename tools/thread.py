"""Date thread: finds where a Regulatory Radar date is mentioned elsewhere on the site.

index_mentions(content_dir) returns a list of mentions:
  {"date": "YYYY-MM-DD", "kind": "briefing|storyline|signal|calendar|competition|results|move",
   "title": str, "url": str, "snippet": str, "stories": [...], "regions": [...], "text": str}
link_radar(items, mentions) returns {radar_key: {date: [mention, ...]}} keeping only mentions that
share the date AND a storyline, or a region plus a topic word, so a generic "1 January" never links
two unrelated things.
"""
import datetime, glob, json, pathlib, re, urllib.parse

MONTHS = {m.lower(): i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
MON3 = {k[:3]: v for k, v in MONTHS.items()}
DATE_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?(?:,?\s+(\d{4}))?", re.I)
STOP = set("""about above after again against also among and another any are around because been before being below between both but
by can could does down during each even every from further have having here into its itself just like made make many more most
much must near never next now only other over same should since some such than that their them then there these they this
those through under until upon very want were what when where which while will with within would year years your from rules rule
parcel parcels goods import imports from new set sets moves move first last under plus each state states""".split())
EMEA = {"EU", "UK", "ME", "NAF"}
APAC = {"CN", "NEA", "SEA", "SAS", "OCE"}
plain = lambda s: re.sub(r"\[\[([^\]]+)\]\]", r"\1", s or "")


ALIAS = {"european union": "eu", "united kingdom": "uk", "united states": "us", "universal postal union": "upu", "world trade organization": "wto"}


def words(t):
    t = plain(t)
    low = t.lower()
    w = {x for x in re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9'’-]{3,}", low) if x not in STOP}
    w |= {x.lower() for x in re.findall(r"\b[A-Z][A-Z0-9]{1,5}\b", t)}
    w |= {re.sub(r"[^\d.]", "", x) for x in re.findall(r"[€$£¥]\s?\d[\d.,]*|\d[\d.,]*\s?%", t)}
    for k, v in ALIAS.items():
        if k in low: w.add(v)
    w.discard("")
    return w


def sentence(text, pos):
    t = plain(text)
    a = max(t.rfind(". ", 0, pos), t.rfind("; ", 0, pos))
    b_ = [i for i in (t.find(". ", pos), t.find("; ", pos)) if i > -1]
    return t[a + 2 if a > -1 else 0: (min(b_) + 1) if b_ else len(t)].strip()


def dates_in(text, ctx_iso):
    """All (iso, matched string) date mentions in text; a missing year is taken from the context date (or the year after if that would be >2 months earlier)."""
    out = []
    try:
        ctx = datetime.date.fromisoformat(ctx_iso)
    except Exception:
        ctx = datetime.date.today()
    for m in DATE_RE.finditer(plain(text)):
        d, mon, y = int(m.group(1)), MON3[m.group(2)[:3].lower()], m.group(3)
        years = [int(y)] if y else [ctx.year, ctx.year + 1]
        for yy in years:
            try:
                dt = datetime.date(yy, mon, d)
            except ValueError:
                continue
            if not y and yy == ctx.year and dt < ctx - datetime.timedelta(days=60):
                continue
            out.append((dt.isoformat(), m.group(0), sentence(text, m.start())))
            if not y:
                break
    return out


def frag(s):
    return "#:~:text=" + urllib.parse.quote(s, safe="")


def index_mentions(C):
    C = pathlib.Path(C)
    M = []
    def add(iso, kind, title, url, text, stories, regions, snippet=None):
        M.append({"date": iso, "kind": kind, "title": title, "url": url, "text": plain(text), "snippet": plain(snippet or text)[:180], "stories": stories or [], "regions": regions or []})
    # Briefings: every paragraph, view, scenario, watch item.
    for f in sorted(glob.glob(str(C / "briefings" / "*.json"))):
        b = json.load(open(f))
        url = f"/briefings/{b['slug']}"
        st, rg, ctx = b.get("stories", []), b.get("regions", [b.get("region")]), b.get("date", "")
        texts = list(b.get("keypoints", []))
        for x in b.get("body", []):
            if "p" in x: texts.append(x["p"])
            for v in x.get("views", []): texts.append(v.get("text", ""))
            for v in x.get("scenarios", []): texts.append(v.get("text", "") + " " + v.get("signal", ""))
            for v in x.get("csuite", []): texts.append(v)
            for w in x.get("watch", []):
                add(w["date"], "briefing", b["title"], url + frag(w.get("what", "")[:60]), w.get("what", ""), st, rg)
        for t in texts:
            for iso, s, sen in dates_in(t, ctx):
                add(iso, "briefing", b["title"], url + frag(s), sen, st, rg, sen)
    # Storylines: chain facts and next dates.
    sl = json.load(open(C / "storylines.json"))["storylines"]
    for s in sl:
        url = f"/storylines/{s['key']}"
        for layer, facts in s.get("chain", {}).items():
            for x in facts:
                if x.get("date"): add(x["date"], "storyline", s["title"], url, x["text"], [s["key"]], s.get("regions", []))
                for iso, m, sen in dates_in(x["text"], x.get("date") or ""):
                    if iso != x.get("date"): add(iso, "storyline", s["title"], url + frag(m), sen, [s["key"]], s.get("regions", []))
        for x in s.get("next", []):
            add(x["date"], "storyline", s["title"], url, x["text"], [s["key"]], s.get("regions", []))
    # Calendars.
    for k, r in json.load(open(C / "regions.json")).items():
        for c in r.get("coming", []):
            if re.match(r"^\d{4}-\d{2}-\d{2}$", c.get("date", "")):
                add(c["date"], "calendar", "Calendar", f"/#{k.lower()}", c["what"], c.get("stories", []), [k])
    for c in json.load(open(C / "home.json")).get("global_coming", []):
        add(c["date"], "calendar", "Calendar", "/#coming", c["what"], c.get("stories", []), [c.get("region", "GLOBAL")])
    # Market intelligence: results calendar, signals, moves, deep dives.
    for f in sorted(glob.glob(str(C / "markets" / "*.json"))):
        for k, r in json.load(open(f)).get("regions", {}).items():
            for w in r.get("watch", []):
                if re.match(r"^\d{4}-\d{2}-\d{2}$", w.get("date", "")):
                    add(w["date"], "results", "Market Intelligence", f"/markets#{k.lower()}", w["what"], [], [k])
    ip = C / "intel"
    if (ip / "signals.json").exists():
        for s in json.load(open(ip / "signals.json"))["signals"]:
            for e in s.get("evidence", []):
                t = f"{e.get('co', '')} {e['text']}"
                if e.get("date"): add(e["date"], "signal", s["title"], f"/markets#sig-{s['key']}", t, s.get("stories", []), s.get("regions", []))
                for iso, m, sen in dates_in(e["text"], e.get("date", "")):
                    if iso != e.get("date"): add(iso, "signal", s["title"], f"/markets#sig-{s['key']}", sen, s.get("stories", []), s.get("regions", []))
            for t in (s.get("claim", ""), s.get("confirm", ""), s.get("refute", "")):
                for iso, m, sen in dates_in(t, "2026-10-01"):
                    add(iso, "signal", s["title"], f"/markets#sig-{s['key']}", sen, s.get("stories", []), s.get("regions", []))
    if (ip / "moves.json").exists():
        for m in json.load(open(ip / "moves.json"))["moves"]:
            rg = m.get("regions", [])
            for iso, s_, sen in dates_in(m["text"], m.get("date", "")):
                add(iso, "move", m["co"], f"/markets#{(rg[0] if rg else 'global').lower()}", sen, m.get("stories", []), rg)
    for f in sorted(glob.glob(str(ip / "competition" / "*.json"))):
        c = json.load(open(f))
        url = f"/markets/{c['key']}"
        for w in c.get("watch", []):
            if w.get("date"): add(w["date"], "competition", c["title"], url + frag(w["what"][:60]), w["what"], [], [c["region"]])
        blobs = [b_.get("text", "") for b_ in c.get("battlegrounds", [])] + [x.get(k_, "") for x in c.get("segments", []) + c.get("countries", []) for k_ in ("dynamics", "rules", "size")]
        for t in blobs:
            for iso, m, sen in dates_in(t, c.get("as_of", "")):
                add(iso, "competition", c["title"], url + frag(m), sen, [], [c["region"]])
    return M


def _rgn(rs):
    s = set(rs or [])
    if "EMEA" in s: s |= EMEA
    if "APAC" in s: s |= APAC
    return s


def link_radar(items, mentions):
    by_date = {}
    for m in mentions:
        by_date.setdefault(m["date"], []).append(m)
    out = {}
    GENERIC = {"united", "states", "state", "kingdom", "republic", "union", "customs", "ministry", "finance", "national", "government",
               "authority", "council", "parliament", "commission", "federal", "tax", "trade", "postal", "member", "office"}
    for it in items:
        jur = words(it.get("jurisdiction", "")) - GENERIC
        kw_t = words(it.get("title", "")) - jur
        st = set(it.get("stories", []))
        res = {}
        for d in it.get("dates", []):
            kw_d = kw_t | words(d.get("what", "")) | jur
            seen, keep = set(), []
            for m in sorted(by_date.get(d["date"], []), key=lambda m: -len(kw_d & words(m["text"]))):
                mw = words(m["text"])
                if jur and not (jur & mw):
                    continue  # the sentence must be about the same jurisdiction
                if not (kw_t & mw):
                    continue  # and share at least one word specific to this rule
                overlap = len(kw_d & mw)
                if not (overlap >= 3 or (st & set(m["stories"]) and overlap >= 2)):
                    continue
                key = (m["kind"], m["url"].split("#")[0])
                if key in seen:
                    continue
                seen.add(key)
                keep.append(m)
            if keep:
                res[d["date"]] = keep
        if res:
            out[it["key"]] = res
    return out
