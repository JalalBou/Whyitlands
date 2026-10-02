#!/usr/bin/env python3
"""Build the static WhyItLands site from content/*.json into site/.

Usage: python3 tools/build.py
No dependencies beyond the Python standard library.
"""
import html, json, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "content"
OUT = ROOT / "site"
BASE = "https://www.whyitlands.com"
VER = datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
E = html.escape

home = json.loads((C / "home.json").read_text())
regions = json.loads((C / "regions.json").read_text())
gloss = json.loads((C / "glossary.json").read_text())
briefings = [json.loads(p.read_text()) for p in sorted((C / "briefings").glob("*.json"))]
briefings.sort(key=lambda b: (b["date"], b["slug"] == "global-small-parcel-door-closes"), reverse=True)
for _b in briefings:
    for _k, _v in (_b.get("glossary_add") or {}).items():
        gloss.setdefault(_k, _v)
    _b.setdefault("regions", [_b.get("region", "GLOBAL")])
_sp = C / "solutions.json"
SOL = json.loads(_sp.read_text()) if _sp.exists() else None
_dp = C / "doctrines.json"
doctrines = json.loads(_dp.read_text()) if _dp.exists() else None

REGION_ORDER = ["GLOBAL", "EMEA", "EU", "UK", "NA", "SA", "AS", "CN", "ME", "NAF"]
DESK_ORDER = ["EU", "UK", "NA", "SA", "AS", "CN", "ME", "NAF"]
RNAME = {"GLOBAL": "Global", "EMEA": "EMEA", "EU": "EU", "UK": "UK", "NA": "North America", "SA": "South America",
         "AS": "Asia", "CN": "China", "ME": "Middle East", "NAF": "North Africa"}
LANGS = [("en", "English")]  # English only

PARCEL = ('<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><polygon points="12,2.5 21.5,7.25 12,12 2.5,7.25" fill="#FF8A6A"/>'
          '<polygon points="2.5,7.25 12,12 12,21.75 2.5,17" fill="#FF5A36"/><polygon points="21.5,7.25 12,12 12,21.75 21.5,17" fill="#D9431F"/>'
          '<polyline points="16.75,4.875 7.25,9.625 7.25,19.375" fill="none" stroke="#FFE3D9" stroke-width="1.6" stroke-linejoin="round"/></svg>')
LINKEDIN = json.loads((C / "settings.json").read_text()).get("linkedin", "")  # set in content/settings.json


def i(key, text, tag="span", cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-i18n="{key}">{text}</{tag}>'


def exact(when):
    return bool(re.match(r"^\d{1,2}[\s–-]", when))


def all_coming():
    items = []
    for k, r in regions.items():
        for c in r["coming"]:
            items.append(dict(c, region=k, exact=exact(c["when"])))
    seen = {(x["date"], x["what"][:30]) for x in items}
    for c in home.get("global_coming", []):
        if (c["date"], c["what"][:30]) not in seen:
            items.append(dict(c, exact=exact(c["when"])))
    items.sort(key=lambda x: x["date"])
    return items


def head(title, desc, path, og_type="website", extra=""):
    url = BASE + path
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="WhyItLands">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/assets/img/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Jalal Boucheikha">
<meta name="theme-color" content="#0B0F1A">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/img/icon-180.png">
<link rel="preload" href="/assets/fonts/instrument-serif-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/instrument-sans-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={VER}">
{extra}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def header(active=""):
    langs = "".join(f'<li><button role="menuitemradio" aria-checked="{str(c=="en").lower()}" data-lang="{c}">{n}<small>{c.upper()}</small></button></li>' for c, n in LANGS)
    def nav(href, key, label, name):
        cur = ' aria-current="page"' if active == name else ""
        return f'<a class="navlink" href="{href}"{cur} data-i18n="{key}">{label}</a>'
    return f"""<header class="site-head">
<div class="wrap head-row">
<div class="brand-wrap"><a class="brand" href="/" aria-label="WhyItLands, home">WhyItLands{PARCEL}</a>
<span class="tagline">Where it lands, and why.</span></div>
<nav class="head-nav" aria-label="Main">
{nav('/storylines', 'nav_storylines', 'Storylines', 'storylines')}
{nav('/briefings/', 'nav_briefings', 'Briefings', 'briefings')}
{nav('/markets', 'nav_markets', 'Market Intelligence', 'markets')}
{nav('/radar', 'nav_radar', 'Regulatory Radar', 'radar')}
{nav('/doctrines', 'nav_doctrines', 'Doctrines', 'doctrines')}
{nav('/#about', 'nav_about', 'About', 'about')}
<a class="btn btn-coral head-sub" href="/#newsletter" data-i18n="subscribe">Subscribe</a>
{f'<a class="me-link" href="{LINKEDIN}" rel="noopener" target="_blank" aria-label="Jalal Boucheikha on LinkedIn"><img src="/assets/img/jalal.jpg?v=2" alt="" width="36" height="36"><span class="li-badge"><svg width="12" height="12" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.6 8.65 21 11.2 21 14.5V21h-4v-5.8c0-1.4-.03-3.2-1.95-3.2-1.95 0-2.25 1.52-2.25 3.1V21H9z"/></svg></span></a>' if LINKEDIN else ""}
</nav>
</div>
</header>
<nav class="tabbar" aria-label="Sections">
<a href="/" {'aria-current="page"' if active == 'home' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/></svg><span data-i18n="tab_home">Home</span></a>
<a href="/storylines" {'aria-current="page"' if active == 'storylines' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><path d="M7 6h10M6 8l5 8M18 8l-5 8"/></svg><span data-i18n="nav_storylines">Storylines</span></a>
<a href="/briefings/" {'aria-current="page"' if active == 'briefings' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4h11l3 3v13H5z"/><path d="M8 10h8M8 14h8M8 18h5"/></svg><span data-i18n="nav_briefings">Briefings</span></a>
<a href="/markets" {'aria-current="page"' if active == 'markets' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg><span data-i18n="tab_markets">Market Intel.</span></a>
<a href="/radar" {'aria-current="page"' if active == 'radar' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12l6-6"/></svg><span data-i18n="tab_radar">Radar</span></a>
<a href="/doctrines" {'aria-current="page"' if active == 'doctrines' else ''}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/></svg><span data-i18n="nav_doctrines">Doctrines</span></a>

</nav>
"""


def subnav(items, sticky=True, overview=True):
    """Page map (static, under the hero) plus the side rail (desktop) / contents bar (mobile).
    items: (anchor_id, i18n_key, label). One component for every long page."""
    items = [x for x in items if x[0]]
    if not items:
        return ""
    allit = ([("main", "rail_top", "Overview")] if overview else []) + items
    di = lambda k: f' data-i18n="{k}"' if k else ""
    pm = "".join(f'<a href="#{a}"{di(k)}>{E(l)}</a>' for a, k, l in items)
    rl = "".join(f'<li><a href="#{a}"><i></i><span{di(k)}>{E(l)}</span></a></li>' for a, k, l in allit)
    return (f'<nav class="pagemap" aria-label="On this page"><div class="wrap"><span class="pm-k" data-i18n="sec_jump">On this page</span><div class="pm-l">{pm}</div></div></nav>'
            f'<nav class="rail" aria-label="Sections of this page" data-n="{len(allit)}"><div class="rail-h"><span class="rail-c">1/{len(allit)}</span><span data-i18n="sec_jump">On this page</span><button type="button" class="rail-x" aria-label="Close">×</button></div><ol>{rl}</ol></nav>')


def auto_subnav(html, pairs):
    """Give the section heads whose kicker uses one of the i18n keys an id, and return (html, subnav)."""
    items = []
    for key, sid, label in pairs:
        pat = '<div class="section-head"'
        k = html.find(f'data-i18n="{key}"')
        if k == -1:
            continue
        h = html.rfind(pat, 0, k)
        if h == -1:
            continue
        html = html[:h] + f'<div id="{sid}" class="section-head"' + html[h + len(pat):]
        items.append((sid, key, label))
    return html, (subnav(items) if len(items) > 2 else "")


def regionbar(keys, default):
    chips = "".join(f'<button class="chip" data-region="{k}" aria-pressed="{str(k==default).lower()}" data-region-label="{k}">{RNAME[k]}</button>' for k in keys)
    return f"""<div class="regionbar" id="regionbar"><div class="wrap">{i('your_region', 'Your region', 'span', 'kicker')}
<div class="chips" role="group" aria-label="Region">{chips}</div></div></div>
"""


def contact_dialog():
    topics = "".join(f'<button type="button" class="chip" data-topic-i="{n}" aria-pressed="{str(n==0).lower()}">{t}</button>' for n, t in enumerate(["Collaboration", "Speaking", "Press", "Tip or correction", "Other"]))
    return f"""<dialog class="modal" id="contact" aria-labelledby="ct-title">
<div class="modal-in">
<div class="modal-top"><div class="who"><img src="/assets/img/jalal.jpg?v=2" alt="" width="56" height="56">
<div><h2 id="ct-title" style="font-size:34px;line-height:1" data-i18n="ct_title">Get in touch</h2><p style="font-size:14px;color:var(--muted);margin-top:4px" data-i18n="ct_sub">Messages go straight to Jalal.</p></div></div>
<button class="xbtn" data-close data-i18n-aria="close" aria-label="Close"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div>
<div class="status" id="ct-status" hidden role="status"></div>
<form id="ct-form" style="display:flex;flex-direction:column;gap:14px">
<div class="fld"><span style="font:600 14px var(--sans)" data-i18n="ct_about">What is it about?</span><div class="chips chips-light" style="flex-wrap:wrap" role="group">{topics}</div></div>
<div class="form-grid">
<div class="fld"><label for="ct-name" data-i18n="ct_name">Name</label><input class="input" id="ct-name" name="name" autocomplete="name" required maxlength="120"></div>
<div class="fld"><label for="ct-email" data-i18n="ct_email">Email</label><input class="input" id="ct-email" name="email" type="email" autocomplete="email" required maxlength="200"></div>
</div>
<div class="fld"><label for="ct-org"><span data-i18n="ct_org">Company and role</span> <span style="font-weight:400;color:var(--muted)" data-i18n="ct_optional">(optional)</span></label><input class="input" id="ct-org" name="org" autocomplete="organization" maxlength="160"></div>
<div class="fld"><label for="ct-msg" data-i18n="ct_msg">Message</label><textarea class="input" id="ct-msg" name="message" rows="4" required maxlength="5000"></textarea></div>
<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<label class="check"><input type="checkbox" name="consent" required><span data-i18n="ct_consent">I agree that my details are used only to answer this message. They are never shared or added to a mailing list.</span></label>
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap"><span style="font-size:13px;color:var(--muted)" data-i18n="ct_spam">Protected against spam. No email address is shown on the site.</span>
<button class="btn btn-ink" type="submit" data-i18n="send">Send</button></div>
</form>
</div>
</dialog>
"""


def footer():
    return f"""<footer class="site-foot">
<div class="wrap">
<div class="foot-row"><a class="brand" href="/">WhyItLands{PARCEL}</a>
<nav aria-label="Footer"><a href="/archive" data-i18n="ar_kicker">Archive</a><a href="/method" data-i18n="method">Method</a><a href="/glossary" data-i18n="glossary">Glossary</a><a href="/legal" data-i18n="legal">Legal & privacy</a>{f'<a href="{LINKEDIN}" rel="noopener">LinkedIn</a>' if LINKEDIN else ""}<a href="#" data-contact="footer" data-i18n="get_in_touch">Get in touch</a></nav></div>
<p class="disclose" data-i18n="disclose">AI-assisted monitoring, curated and reviewed by Jalal Boucheikha. Every fact is sourced.</p>
</div>
</footer>
{contact_dialog()}
<script src="/assets/js/config.js?v={VER}"></script>
<script src="/assets/js/i18n.js?v={VER}"></script>
<script src="/assets/js/site.js?v={VER}" defer></script>
</body>
</html>
"""


def coming_json():
    data = json.dumps(all_coming(), ensure_ascii=False).replace("</", "<\\/")
    smap = json.dumps({k: v["short"] for k, v in STORIES.items()}, ensure_ascii=False)
    return f'<script type="application/json" id="coming-data">{data}</script>\n<script type="application/json" id="story-map">{smap}</script>\n'


def filters():
    chips = "".join(f'<button class="chip" data-type="{t}" aria-pressed="{str(t=="All").lower()}" data-i18n="{k}">{lbl}</button>'
                    for t, k, lbl in [("All", "all", "All"), ("Geopolitics", "Geopolitics", "Geopolitics"), ("Regulation", "Regulation", "Regulation"), ("Expo", "Expo", "Expos")])
    return f'<div class="filters chips chips-light" role="group" aria-label="Type">{chips}</div>'


def src_link(label, url):
    return f'<a href="{E(url)}" rel="noopener">{E(label)}</a>' if url else E(label)


def lang_note():
    return '<p class="lang-note" data-i18n="lang_note" hidden>Briefings are published in English first. Translated editions are rolling out.</p>'


ARCS = """<svg class="hero-arcs" viewBox="0 0 1440 700" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<defs><linearGradient id="g1" x1="0" x2="1"><stop offset="0" stop-color="#FF5A36" stop-opacity="0"/><stop offset=".5" stop-color="#FF5A36"/><stop offset="1" stop-color="#FF5A36" stop-opacity="0"/></linearGradient>
<linearGradient id="g2" x1="0" x2="1"><stop offset="0" stop-color="#2B45E0" stop-opacity="0"/><stop offset=".5" stop-color="#6B80FF"/><stop offset="1" stop-color="#2B45E0" stop-opacity="0"/></linearGradient></defs>
<g fill="none" stroke-width="1.4"><path d="M-40 560 C 300 180, 700 120, 1480 300" stroke="url(#g1)"/><path d="M-40 640 C 420 330, 980 260, 1480 520" stroke="url(#g2)"/>
<path d="M200 700 C 480 360, 900 300, 1300 -20" stroke="url(#g1)" opacity=".5"/><path d="M-40 300 C 380 420, 900 520, 1480 140" stroke="url(#g2)" opacity=".45"/></g>
<g fill="#FF5A36"><circle cx="1120" cy="236" r="4"/><circle cx="410" cy="300" r="3"/><circle cx="880" cy="345" r="3" fill="#D7F75B"/><circle cx="1302" cy="380" r="3" fill="#6B80FF"/></g>
<g fill="#FFFFFF" opacity=".08">""" + "".join(f'<circle cx="{x}" cy="{y}" r="1.2"/>' for x in range(40, 1440, 48) for y in range(40, 700, 48)) + "</g></svg>"


def about_nl():
    return f"""<section class="section" style="padding-top:0" id="about"><div class="wrap">
<div class="about">
<div class="portrait"><img src="/assets/img/jalal.jpg?v=2" alt="Jalal Boucheikha" width="220" height="220" loading="lazy"></div>
<div>{i('about_kicker', 'About', 'div', 'kicker')}<h2>Jalal Boucheikha</h2>{i('role', 'Senior leader in e-commerce logistics', 'div', 'role')}<p class="role-2" data-i18n="role_2">Background in engineering, energy, strategy consulting and product leadership. Expertise in cross-border parcels, customs and compliance, carrier networks and product strategy.</p>
<p data-i18n="about_1">With an engineer’s grounding in how systems work, I lead product where operations, commercial, compliance and strategy meet: the side of cross-border parcels that decides how they are processed, cleared, routed and tracked.</p>
<p data-i18n="about_2">My day-to-day is multicultural and multi-regional, with teams and partners across several continents, and a practice of agile at scale inside a large organisation.</p>
<p data-i18n="about_3">I started WhyItLands to explain the why behind the decisions reshaping e-commerce logistics, domestic and cross-border, in a form that is quick to read and easy to check.</p>
<blockquote>“Complexity should be invisible. What you expose to your merchants, your partners, your customers should be simple, reliable and programmable.”</blockquote>
<div class="cta">{f'<a class="btn btn-light" href="{LINKEDIN}" rel="noopener" target="_blank"><svg width="16" height="16" viewBox="0 0 24 24" fill="#0A66C2" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05C20.6 8.65 21 11.2 21 14.5V21h-4v-5.8c0-1.4-.03-3.2-1.95-3.2-1.95 0-2.25 1.52-2.25 3.1V21H9z"/></svg><span data-i18n="li_btn">Connect on LinkedIn</span></a>' if LINKEDIN else ""}<a class="btn btn-ghost-dark" href="#" data-contact="about" data-i18n="get_in_touch">Get in touch</a></div>
<p style="font-size:13px;margin-top:22px;color:#8C93A6" data-i18n="about_note">WhyItLands is a personal project. Views are my own and do not represent my employer.</p>
</div></div>
</div></section>

<section class="section" style="padding-top:0" id="newsletter"><div class="wrap nl">
<div class="nl-card"><h2><span data-i18n="nl_title1">Every week:</span><br><span data-i18n="nl_title2">where it lands, and why.</span></h2>
<p data-i18n="nl_dek">The week’s geopolitical shifts, deals and reforms for your region, in seven minutes. Free, one-click unsubscribe.</p>
<form id="nl-form" class="field-row" novalidate="false">
<label class="sr-only" for="nl-email" data-i18n="work_email">Work email</label>
<input class="input" id="nl-email" name="email" type="email" autocomplete="email" required data-i18n-ph="work_email" placeholder="Work email">

<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="btn btn-ink" type="submit" data-i18n="sign_up">Sign up</button>
<fieldset class="nl-regions"><legend data-i18n="nl_regions">Your regions: pick one or more</legend><div class="nl-chips">
<label class="nl-chip"><input type="checkbox" name="regions" value="GLOBAL" checked><span data-i18n="nl_all">All regions</span></label>
{''.join(f'<label class="nl-chip"><input type="checkbox" name="regions" value="{k}"><span data-region-label="{k}">{RNAME[k]}</span></label>' for k in REGION_ORDER if k not in ("GLOBAL", "EMEA"))}
</div></fieldset>
</form>
<div class="status" id="nl-status" hidden role="status" style="margin-top:12px"></div>
<p class="fine" data-i18n="nl_fine">We send a confirmation email first. Your regions can be changed in every issue.</p></div>
{feedback_card()}
</div></section>
"""


EMEA_SET = ["EU", "UK", "ME", "NAF"]
RN_CODE = {"Middle East": "ME", "North America": "NA", "China": "CN", "EU": "EU", "UK": "UK", "Asia": "AS", "South America": "SA", "North Africa": "NAF", "Global": "GLOBAL"}


def show_for(*keys):
    ks = set(keys)
    if ks & set(EMEA_SET):
        ks.add("EMEA")
    return ",".join(sorted(ks))


def lead_for(k):
    if k == "GLOBAL":
        return next(x for x in briefings if x["slug"] == home["hero"]["briefing"])
    if k == "EMEA":
        return next(x for x in briefings if x.get("region") == "EU")
    return next((x for x in briefings if x.get("region") == k), briefings[0])


def hero_block(k):
    b = lead_for(k)
    if k == "GLOBAL":
        h = home["hero"]
        kicker, title, em, dek = h["kicker"], h["title"], h["title_em"], h["dek"]
        chain = [(c["k"], c["t"], c.get("story")) for c in home["chain"]]
    elif k == "EMEA":
        e = home["emea"]
        kicker, title, em, dek = e["kicker"], e["title"], e["title_em"], e["dek"]
        chain = [(c["k"], c["t"], c.get("story")) for c in e["chain"]]
    else:
        r = regions[k]
        kicker = RNAME[k] + " · " + b["date_label"]
        title, em, dek = r["headline"], "", plain(b["dek"])
        sk = (b.get("stories") or [None])[0]
        chain = [("", plain(x), sk) for x in b["keypoints"][:4]]
    ch = "".join((f'<li><a class="chain-a" href="/storylines/{st}">' if st in STORIES else '<li>') + f'<span class="n">{n}</span><div>{("<b>" + E(lbl.upper()) + "</b>") if lbl else ""}<span>{E(t)}</span>{"<em class=chain-go>" + E(STORIES[st]["short"]) + " →</em>" if st in STORIES else ""}</div>' + ('</a></li>' if st in STORIES else '</li>') for n, (lbl, t, st) in enumerate(chain, 1))
    return f"""<section class="hero" data-show="{k}"{'' if k == 'GLOBAL' else ' hidden'}>{ARCS}
<div class="wrap hero-grid">
<div><span class="kicker">{E(kicker)}</span>
<h1>{E(title)}{('<br><em>' + E(em) + '</em>') if em else ''}</h1>
<p class="dek">{E(dek)}</p>
<div class="hero-cta"><a class="btn btn-coral" href="/briefings/{b['slug']}"><span data-i18n="read_briefing">Read the briefing</span></a>
{listen_btn(b)}<a class="btn btn-ghost-dark" href="/markets#{k.lower()}"><span data-i18n="nav_markets">Market Intelligence</span></a></div></div>
<aside class="chain" aria-label="Why it lands here"><span class="kicker" data-i18n="why_lands_here">Why it lands here</span><ol>{ch}</ol></aside>
</div></section>"""


def home_market_block(k):
    keys = EMEA_SET if k == "EMEA" else [k]
    rows = []
    for kk in keys:
        for c in MARKETS.get(kk, {}).get("companies", []):
            if not c.get("revenue"):
                continue
            cid = re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-")
            rows.append(f'<tr><td class="co-n"><a href="/markets#{kk.lower()}">{E(c["name"])}</a></td><td class="date">{E(c.get("period", ""))}</td><td>{E(c.get("revenue") or "")} <span class="{chg_class(c.get("revenue_chg"))}">{E(c.get("revenue_chg") or "")}</span></td><td>{E(c.get("ebit") or "")} <span class="{chg_class(c.get("ebit_chg"))}">{E(c.get("ebit_chg") or "")}</span></td></tr>')
    if not rows:
        return ""
    take = " ".join(MARKETS[kk]["take"] for kk in keys if kk in MARKETS and MARKETS[kk].get("take"))
    return f"""<div data-show="{k}"{'' if k == 'GLOBAL' else ' hidden'}><p class="mk-home-take"><b data-i18n="mk_our_read">Our read</b> {E(take)}</p>
<div class="table-wrap mk-table"><table><thead><tr><th data-i18n="th_company">Company</th><th data-i18n="mk_period">Period</th><th data-i18n="mk_revenue">Revenue</th><th data-i18n="mk_profit">Operating profit</th></tr></thead><tbody>{''.join(rows[:8])}</tbody></table></div></div>"""


def home_expos(k):
    r = regions[k]
    expos = "".join(f"""<article class="expo"><span class="kicker">{E(RNAME[k])}</span><h3>{E(x['name'])}</h3><span class="when">{E(x['when'])}</span><ul>{''.join(f'<li>{E(p)}</li>' for p in x['points'])}</ul><span class="src"><span data-i18n="source">Source</span>: {E(x['src'])}</span></article>""" for x in r["expos"])
    return f'<div class="expo-grid" data-show="{show_for(k)}" hidden>{expos}</div>'


def why_cards():
    out = []
    for w in home["why"]:
        code = RN_CODE.get(w["region"], "GLOBAL")
        out.append((show_for("GLOBAL", code), w["region"], w["title"], w["what"], w["why"], w["means"], None, w.get("stories")))
    for b in briefings:
        k = b.get("region", "GLOBAL")
        if k == "GLOBAL":
            continue
        imp = next((x["impact"] for x in b["body"] if "impact" in x), "")
        out.append((show_for(k), RNAME.get(k, k), b["title"], plain(b["keypoints"][0]), plain(b["keypoints"][1]) if len(b["keypoints"]) > 1 else "", plain(imp), b["slug"], b.get("stories")))
    cards = []
    for sh, reg, title, what, why, means, slug, sts in out:
        link = f'<a class="more" href="/briefings/{slug}" data-i18n="read_briefing">Read the briefing</a>' if slug else ""
        cards.append(f"""<article class="why" data-show="{sh}"><span class="kicker">{E(reg)}</span><h3>{E(title)}</h3>
<dl><div><dt data-i18n="what_happened">What happened</dt><dd>{E(what)}</dd></div><div><dt data-i18n="why">Why</dt><dd>{E(why)}</dd></div><div><dt data-i18n="what_means">What it means</dt><dd>{E(means)}</dd></div></dl>{story_chips(sts)}{link}</article>""")
    return "".join(cards)


def page_home():
    WELCOME = """<section class="welcome" id="welcome"><div class="wrap wl-row">
<div class="wl-text"><p class="wl-h" data-i18n="wl_h">WhyItLands explains why world events land on the cost, speed and rules of a parcel.</p>
<p class="wl-sub" data-i18n="wl_sub">For executives and senior leaders in domestic and cross-border e-commerce logistics. Free, sourced, updated every week.</p>
<nav class="wl-links" aria-label="Sections"><a href="/storylines"><b data-i18n="nav_storylines">Storylines</b><span data-i18n="iv_s">Each crisis traced from geopolitics to law, market and parcel</span></a><a href="/briefings/"><b data-i18n="nav_briefings">Briefings</b><span data-i18n="iv_b">Long-form analyses confronting every point of view</span></a><a href="/markets"><b data-i18n="nav_markets">Market Intelligence</b><span data-i18n="iv_m">Signals, prices, moves and results of 40+ players</span></a><a href="/radar"><b data-i18n="nav_radar">Regulatory Radar</b><span data-i18n="iv_r">The rules coming, their dates and what to prepare</span></a></nav></div>
<div class="wl-act"><button type="button" class="wl-play" data-video><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg><span data-i18n="wl_watch">Watch in 100 seconds</span></button><button type="button" class="wl-more" data-i18n="wl_more">What is this site?</button></div>
</div></section>
<dialog class="vdlg" id="vdlg" aria-label="WhyItLands explained in 100 seconds"><button type="button" class="vdlg-x" aria-label="Close">×</button><video id="iv" src="/assets/video/whyitlands-explainer.mp4?v=20261001b" poster="/assets/video/poster.jpg" preload="none" playsinline controls controlslist="nodownload"></video></dialog>
""".format()
    tiles = []
    for w in home["wire"]:
        inner = f'<span class="tag">{E(w["tag"])}</span>'
        if w.get("big"): inner += f'<span class="big">{E(w["big"])}</span>'
        if w.get("lede"): inner += f'<p class="lede">{E(w["lede"])}</p>'
        if w.get("text"): inner += f'<p>{E(w["text"])}</p>'
        inner += story_chips(w.get("stories"), w.get("layer"))
        inner += f'<span class="src">{src_link(w["src"], w.get("url"))}</span>'
        tiles.append(f'<article class="tile {w["style"]}" data-regions="{",".join(w.get("regions", []))}">{inner}</article>')
    deals = "".join(f'<tr data-regions="{E(d["region"])}"><td class="date">{E(d["date"])}</td><td class="co">{E(d["co"])}</td><td>{E(d["deal"])}{story_chips(d.get("stories"), d.get("layer"))}</td><td><span class="pill">{E(d["region"])}</span></td><td>{src_link(d["src"], d.get("url"))}</td></tr>' for d in home["deals"])
    srcs = "".join(f'<div class="src-card"><div class="kicker">{E(s["k"])}</div><p>' + " · ".join(E(n) + (f'<span class="lng">{l}</span>' if l else "") for n, l in s["items"]) + "</p></div>" for s in home["sources"])
    heroes = "".join(hero_block(k) for k in REGION_ORDER)
    mk = "".join(home_market_block(k) for k in REGION_ORDER)
    expos = "".join(home_expos(k) for k in DESK_ORDER)
    out = head("WhyItLands · Where it lands, and why", "Geopolitics connected, factually and with sources, to e-commerce logistics, domestic and cross-border. A clear information grid for senior leaders: what is happening, what is coming, and why.", "/")
    HOME_RAIL = subnav([("barometer", "baro_kicker", "Parcel barometer"), ("briefings", "briefings_kicker", "Briefings"), ("coming", "ag_kicker", "Agenda"), ("storylines", "st_kicker_all", "Storylines"), ("wire", "wire_kicker", "Industry wire"), ("mk-home", "mk_kicker", "Market intelligence"), ("about", "about_kicker", "About"), ("newsletter", "subscribe", "Subscribe")])
    out += header("home") + WELCOME + regionbar(REGION_ORDER, "GLOBAL")
    out += f"""<main id="main" data-region-page>
{heroes}
{HOME_RAIL}
{home_barometer()}
<section class="section" id="briefings" style="padding-top:0"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="briefings_kicker">Briefings</span> · <span data-current-region>GLOBAL</span></div>{i('briefings_title', 'The analysis, region by region', 'h2')}</div><a class="more" href="/briefings/" data-i18n="all_briefings_arrow">All briefings →</a></div>
<div class="bgrid" data-filter-regions data-order-regions>{''.join(bcard(x) for x in briefings)}</div>
</div></section>
<section class="section" style="padding-top:0" id="coming"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="ag_kicker">Agenda</span> · <span data-current-region>GLOBAL</span></div><h2 data-i18n="ag_h">What’s coming, and when</h2></div><a class="more" href="/radar" data-i18n="rr_open">Open the radar →</a></div>
<div class="agenda">
<div class="ag-col"><h3 class="ag-h" data-i18n="rr_home_h">The next regulatory deadlines</h3>{home_radar_list()}</div>
<div class="ag-col"><h3 class="ag-h" data-i18n="ag_cal">Elections, summits and trade shows</h3>{filters()}<div class="timeline" data-timeline="home" data-limit="6" aria-live="polite"></div></div>
</div></div></section>

{home_storylines()}
<section class="section" id="wire" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('wire_kicker', 'Industry wire', 'div', 'kicker')}{i('wire_title', 'What moved this week', 'h2')}</div></div>
<div class="bento">{''.join(tiles)}</div>
</div></section>
<section class="section" id="mk-home" style="padding-top:0"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="mk_kicker">Market intelligence</span> · <span data-current-region>GLOBAL</span></div>{i('mk_h1', 'Who is winning, who is paying.', 'h2')}</div><a class="more" href="/markets" data-i18n="mk_all">All results →</a></div>
{mk}
</div></section>
<section class="section" style="padding-top:0" data-show="{show_for(*DESK_ORDER)}" hidden><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="shows_kicker">Trade shows</span> · <span data-current-region>GLOBAL</span></div>{i('shows_title', 'What the shows told us', 'h2')}</div></div>
{expos}
</div></section>
<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('sources_kicker', 'Sources', 'div', 'kicker')}{i('sources_title', 'Close to the ground, in the local language', 'h2')}<p style="margin-top:14px;color:var(--muted-2);max-width:680px" data-i18n="sources_dek">Institutions, trade press and niche regional media, read in their original language. Every fact links to its source.</p></div></div>
<div class="src-grid">{srcs}</div>
</div></section>
""" + about_nl() + f"""
</main>
{coming_json()}"""
    out += footer()
    return out


def feedback_card():
    return """<div class="fb-card"><h3 data-i18n="fb_title">Spotted an error, have a tip?</h3><p style="color:var(--muted-2)" data-i18n="fb_dek">Write anonymously or with your name. Every message is read.</p>
<form class="fb-form" style="display:flex;flex-direction:column;gap:10px">
<label class="sr-only" for="fb-msg" data-i18n="fb_msg">Your message</label><textarea class="input" id="fb-msg" name="message" required maxlength="5000" data-i18n-ph="fb_msg" placeholder="Your message"></textarea>
<label class="sr-only" for="fb-from" data-i18n="fb_name">Name or email (optional)</label><input class="input" id="fb-from" name="from" maxlength="200" data-i18n-ph="fb_name" placeholder="Name or email (optional)" style="border-radius:14px">
<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="btn btn-ink" type="submit" style="align-self:flex-start" data-i18n="send">Send</button>
<div class="status" hidden role="status"></div></form></div>"""


def page_regions():
    desks = []
    for k in DESK_ORDER:
        r = regions[k]
        expos = "".join(f"""<article class="expo"><h3>{E(x['name'])}</h3><span class="when">{E(x['when'])}</span><ul>{''.join(f'<li>{E(p)}</li>' for p in x['points'])}</ul><span class="src"><span data-i18n="source">Source</span>: {E(x['src'])}</span></article>""" for x in r["expos"])
        vids = r.get("videos") or []
        if vids:
            vhtml = '<div class="expo-grid">' + "".join(f"""<article class="expo"><div style="aspect-ratio:16/9;border-radius:16px;overflow:hidden;background:#000"><iframe src="https://www.youtube-nocookie.com/embed/{E(v['id'])}?start={int(v.get('start', 0))}" title="{E(v['title'])}" loading="lazy" allow="encrypted-media; picture-in-picture" allowfullscreen style="width:100%;height:100%;border:0"></iframe></div><h3 style="font-size:22px">{E(v['title'])}</h3><span class="src">{E(v.get('channel', ''))}</span></article>""" for v in vids) + "</div>"
        else:
            vhtml = '<p class="note" data-i18n="no_video">No verified video for this region yet. We only embed videos from identified channels, once their content has been checked.</p>'
        hidden = "" if k == "EU" else " hidden"
        desks.append(f"""<div class="desk" id="desk-{k}"{hidden}>
<section class="rhero"><div class="wrap"><div class="kicker"><span data-region-label="{k}">{RNAME[k]}</span> · <span data-i18n="regional_desk">Regional desk</span></div><h1>{E(r['headline'])}</h1><p>{E(r['dek'])}</p></div></section>
{desk_briefings(k)}
{desk_markets(k)}
<section class="section"><div class="wrap">
<div class="section-head"><div>{i('cal_kicker', 'Calendar', 'div', 'kicker')}{i('coming_title', 'What’s coming', 'h2')}</div></div>
{filters()}
<div class="timeline" data-timeline="{k}" aria-live="polite"></div>
</div></section>
<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('shows_kicker', 'Trade shows', 'div', 'kicker')}{i('shows_title', 'What the shows told us', 'h2')}</div></div>
<div class="expo-grid">{expos}</div>
</div></section>
<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('watch_kicker', 'Watch', 'div', 'kicker')}{i('watch_title', 'From the show floor', 'h2')}</div></div>
{vhtml}
</div></section>
</div>""")
    out = head("Regional desks · WhyItLands", "Regional calendars of regulation, geopolitics and logistics trade shows, with what each show told us: EU, UK, North America, South America, Asia, China, Middle East, North Africa.", "/regions")
    out += header("regions") + regionbar(DESK_ORDER, "EU")
    out += '<main id="main" data-region-page>' + "".join(desks) + f"""
<section class="section" style="padding-top:0"><div class="wrap nl" style="grid-template-columns:1fr">{feedback_card()}</div></section>
</main>
{coming_json()}"""
    return out + footer()


def inline(text, used):
    def rep(m):
        k = m.group(1)
        if k not in gloss:
            return E(k)
        if k in used:
            return E(k)
        used.append(k)
        return f'<span class="acr">{E(k)}<button class="ast" data-g="{E(k)}" aria-label="Definition of {E(k)}">*</button></span>'
    return re.sub(r"\[\[([A-Z0-9][A-Za-z0-9&-]{1,9})\]\]", rep, E(text))


def plain(text):
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)


def cites(idx, srcs):
    idx = [n for n in (idx or []) if isinstance(n, int) and 0 <= n < len(srcs)]
    if not idx:
        return ""
    return '<sup class="cite">' + "".join(f'<a href="#s-{n + 1}" title="{E(srcs[n].get("pub") or srcs[n]["t"])}">{n + 1}</a>' for n in idx) + "</sup>"


def reading_minutes(b):
    words = 0
    for blk in b["body"]:
        for k, v in blk.items():
            if k != "src":
                words += len(json.dumps(v, ensure_ascii=False).split())
    words += sum(len(k.split()) for k in b["keypoints"])
    return max(3, round(words / 230))


def has_audio(b):
    a = b.get("audio") or {}
    return bool(a.get("src") and (OUT / a["src"].lstrip("/")).exists())


def listen_btn(b):
    if not has_audio(b):
        return ""
    return (f'<a class="btn btn-ghost-dark" href="/briefings/{b["slug"]}#listen"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg>'
            f'<span data-i18n="listen">Listen</span></a>')


def bcard(b, big=False):
    regs = ",".join(b.get("regions", []))
    return (f'<a class="bcard{" big" if big else ""}" href="/briefings/{b["slug"]}" data-regions="{regs}" data-primary="{b.get("region", "GLOBAL")}" data-date="{b["date"]}" data-text="{E((b["title"] + " " + plain(b["dek"]) + " " + b["section"]).lower())}">'
            f'<span class="kicker">{E(b["section"])}</span><h3>{E(b["title"])}</h3><p>{E(plain(b["dek"]))}</p>'
            f'{story_chips((b.get("stories") or [])[:2], link=False)}<span class="bmeta">{E(b["date_label"])}{(" · updated " + E(date_label(b["updated"]))) if b.get("updated") else ""} · {reading_minutes(b)} <span data-i18n="min_read">min read</span></span></a>')


def desk_briefings(k):
    mine = [b for b in briefings if b.get("region") == k] + [b for b in briefings if b.get("region") != k and k in b.get("regions", [])]
    if not mine:
        return ""
    return f"""<section class="section" style="padding-bottom:0"><div class="wrap">
<div class="section-head"><div>{i('briefings_kicker', 'Briefings', 'div', 'kicker')}{i('desk_analysis', 'The analysis for this region', 'h2')}</div></div>
<div class="bgrid">{''.join(bcard(b, n == 0 and b.get('region') == k) for n, b in enumerate(mine[:4]))}</div>
</div></section>"""


def sol_cites(idx):
    S = SOL["sources"]
    return " ".join(f'<a href="{E(S[n]["u"])}" rel="noopener">{E(S[n].get("pub") or S[n]["t"])}</a>' for n in (idx or []) if isinstance(n, int) and 0 <= n < len(S))


def topic_html(tp, compact=False):
    players = "".join(f"""<article class="pl"><div class="pl-top"><h4>{E(x['name'])}</h4><span class="pl-type">{E(x.get('type', ''))}</span></div><p>{E(x.get('what', ''))}</p><p class="pl-pos">{E(x.get('position', ''))}</p><p class="pl-src">{sol_cites(x.get('src'))}</p></article>""" for x in sorted(tp["players"], key=lambda x: x["name"].lower()))
    head_ = "" if compact else f'<h3>{E(tp["title"])}</h3>'
    return f"""<div class="topic" id="sol-{E(tp['key'])}" data-regions="{','.join(tp.get('regions', []))}">{head_}{story_chips(tp.get('stories'), 'decision')}<p class="need"><b data-i18n="sol_need">What the rule requires</b> {E(tp.get('need', ''))}</p><div class="pls">{players}</div>{('<p class="sol-watch"><b data-i18n="sol_watch">Still moving</b> ' + E(tp['watch']) + '</p>') if tp.get('watch') else ''}</div>"""


def page_briefing(b):
    used = []
    S = b["sources"]
    body = []
    toc = []
    kp = ''.join(f'<li>{inline(k, used)}</li>' for k in b['keypoints'])
    for blk in b["body"]:
        c = cites(blk.get("src"), S)
        if "p" in blk:
            body.append(f"<p>{inline(blk['p'], used)}{c}</p>")
        elif "h" in blk:
            hid = re.sub(r"[^a-z0-9]+", "-", blk["h"].lower()).strip("-")[:50]
            toc.append((hid, blk["h"]))
            body.append(f'<h2 id="{hid}">{E(blk["h"])}</h2>')
        elif "views" in blk:
            cards = "".join(f'<article class="view"><div class="view-actor">{E(v["actor"])}</div><p class="view-stance">{inline(v["stance"], used)}</p><p>{inline(v["text"], used)}{cites(v.get("src"), S)}</p></article>' for v in blk["views"])
            body.append(f'<div class="views">{cards}</div>')
        elif "doctrines" in blk:
            cards = "".join(f'<article class="doc"><div class="doc-school">{E(d["school"])}</div><dl><dt data-i18n="doc_reading">How it reads the situation</dt><dd>{inline(d["reading"], used)}</dd><dt data-i18n="doc_parcel">What it means for the parcel</dt><dd>{inline(d["parcel"], used)}{cites(d.get("src"), S)}</dd></dl></article>' for d in blk["doctrines"])
            body.append(f'<div class="docs">{cards}</div><p class="more-docs"><a href="/doctrines" data-i18n="doc_all">All doctrines explained →</a></p>')
        elif "figures" in blk:
            cards = "".join(f'<div class="fig"><span class="big">{E(f["big"])}</span><span>{inline(f["label"], used)}</span></div>' for f in blk["figures"])
            toc.append(("figures", "Key figures"))
            body.append(f'<h2 id="figures" data-i18n="key_figures">Key figures</h2><div class="figs">{cards}</div>{("<p class=figsrc>" + c + "</p>") if c else ""}')
        elif "scenarios" in blk:
            cards = "".join(f'<article class="scen"><div class="scen-top"><h3>{E(x["name"])}</h3><span class="pill">{E(x.get("likelihood", ""))}</span></div><p>{inline(x["text"], used)}</p>{("<p class=signal><b data-i18n=signal>Signal to watch</b> " + inline(x["signal"], used) + "</p>") if x.get("signal") else ""}</article>' for x in blk["scenarios"])
            toc.append(("scenarios", "Scenarios"))
            body.append(f'<h2 id="scenarios" data-i18n="scenarios">Scenarios</h2><div class="scens">{cards}</div>')
        elif "watch" in blk:
            rows = "".join(f'<li><span class="tl-when">{E(w["when"])}</span><span>{inline(w["what"], used)}</span></li>' for w in blk["watch"])
            toc.append(("watchlist", "Watchlist"))
            body.append(f'<h2 id="watchlist" data-i18n="watchlist">Watchlist</h2><ul class="watch">{rows}</ul>')
        elif "csuite" in blk:
            rows = "".join(f"<li>{inline(x, used)}</li>" for x in blk["csuite"])
            toc.append(("csuite", "For executives and senior leaders"))
            body.append(f'<section class="csuite" id="csuite"><div class="kicker" data-i18n="csuite_kicker">Decisions</div><h2 data-i18n="csuite">For executives and senior leaders</h2><ol>{rows}</ol></section>')
        elif "landscape" in blk and SOL:
            tp = next((x for x in SOL["topics"] if x["key"] == blk["landscape"].get("topic")), None)
            if tp:
                body.append(f'<section class="landscape"><div class="kicker" data-i18n="sol_kicker">Solution landscape</div><h3>{E(tp["title"])}</h3><p>{inline(blk["landscape"].get("note", ""), used)}</p>{topic_html(tp, compact=True)}<p class="sol-neutral" data-i18n="sol_neutral">At least three providers per need, in alphabetical order. Information, not endorsement.</p><p><a href="/markets#solutions" data-i18n="sol_all">Full solution landscape →</a></p></section>')
        elif "impact" in blk:
            body.append(f'<div class="impact"><div class="kicker" style="color:var(--lime-ink)" data-i18n="bottom_line">Bottom line</div><p>{inline(blk["impact"], used)}</p></div>')
    mins = reading_minutes(b)
    keys = []
    for k in b.get("glossary", []) + used:
        if k not in keys and k in gloss:
            keys.append(k)
    gl = "".join(f'<div id="g-{E(k)}"><dt><span>{E(k)}</span>{E(gloss[k][0])}</dt><dd>{E(gloss[k][1])}</dd></div>' for k in keys)
    srcs = "".join(f'<li id="s-{n}"><a href="{E(s["u"])}" rel="noopener">{E(s["t"])}</a>{(" · " + E(s["pub"])) if s.get("pub") else ""}{(" · " + E(s["date"])) if s.get("date") else ""}{(" <span class=lng>" + E(s["lang"]) + "</span>") if s.get("lang") and s.get("lang") != "en" else ""}</li>' for n, s in enumerate(S, 1))
    audio = ""
    if has_audio(b):
        a = b["audio"]
        audio = f"""<div class="player" id="player" data-id="{E(b['slug'])}">
<button class="pbtn" aria-label="Play"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg></button>
<div><div class="ptitle">{E(b['title'])} · <span data-i18n="neural_voice">Neural voice</span></div><input type="range" min="0" max="100" step="1" value="0" aria-label="Seek"><div class="ptime"><span class="cur">0:00</span><span class="dur">{a.get('minutes', '')}:00</span></div></div>
<div class="pctl"><button data-skip="-15" aria-label="Back 15 seconds">−15</button><button data-skip="30" aria-label="Forward 30 seconds">+30</button><button data-rate aria-label="Playback speed">1×</button></div>
<audio preload="metadata" src="{E(a['src'])}"></audio></div>"""
    tocs = "".join(f'<a href="#{h}">{E(t)}</a>' for h, t in toc)
    related = [x for x in briefings if x["slug"] != b["slug"]][:3]
    rel = "".join(bcard(x) for x in related)
    ld = json.dumps({"@context": "https://schema.org", "@type": "NewsArticle", "headline": b["title"], "datePublished": b["date"], "author": dict({"@type": "Person", "name": "Jalal Boucheikha"}, **({"url": LINKEDIN} if LINKEDIN else {})), "publisher": {"@type": "Organization", "name": "WhyItLands"}, "image": BASE + "/assets/img/og.png", "description": plain(b["dek"])}, ensure_ascii=False)
    out = head(f"{b['title']} · WhyItLands", plain(b["dek"]), f"/briefings/{b['slug']}", "article", f'<script type="application/ld+json">{ld}</script>\n')
    out += header("briefings")
    out += f"""<main id="main">
<section class="art-head"><div class="wrap"><div class="kicker">{E(b['section'])}</div><h1>{E(b['title'])}</h1><p style="color:var(--on-ink-muted);font-size:clamp(17px,1.6vw,20px);max-width:760px;margin-bottom:18px">{inline(b['dek'], [])}</p><div class="meta">{E(b['date_label'])} · {mins} <span data-i18n="min_read">min read</span> · {len(S)} <span data-i18n="n_sources">sources</span> · Jalal Boucheikha</div></div></section>
<div class="art-shell">{subnav([("keypoints", "key_points", "Key points")] + [(h, "", t) for h, t in toc], overview=False).split("</nav>", 1)[1]}
<div class="art">
<div class="keypoints" id="keypoints">{i('key_points', 'Key points', 'div', 'kicker')}<ul>{kp}</ul>
<div class="kp-links"><a class="btn btn-coral" href="#csuite" style="height:40px;font-size:14px" data-i18n="jump_csuite">Jump to the actions for leaders</a></div></div>
<div class="art-ctx">{('<div class="part-of"><span data-i18n="st_part">Part of the storyline</span> ' + " · ".join(f'<a href="/storylines/{k}">{E(STORIES[k]["title"])}</a>' for k in (b.get("stories") or []) if k in STORIES) + '</div>') if b.get("stories") else ''}
{(lambda rr: ('<div class="part-of rr-of"><span data-i18n="rr_on">On the Regulatory Radar</span> ' + " · ".join(f'<a href="/radar#rr-{E(x["key"])}">{E(x["title"])}</a>' for x in rr) + '</div>') if rr else '')(radar_for_url(f"/briefings/{b['slug']}"))}
</div>
<nav class="toc" aria-label="In this briefing"><span class="kicker" data-i18n="in_this_briefing">In this briefing</span>{tocs}</nav>
<span id="listen"></span>{audio}
<div class="art-body" style="margin-top:28px">{''.join(body)}</div>
<section class="gloss" aria-labelledby="gl-h"><h2 id="gl-h" style="font-size:28px" data-i18n="acronyms">Acronyms in this article</h2><dl>{gl}</dl>
<p style="margin-top:16px;font-size:15px"><a href="#" data-back data-i18n="back_text">↩ Back to the text</a> · <a href="/glossary" data-i18n="full_glossary">Full glossary →</a></p></section>
<section class="sources-list"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section>
<p class="method-note" data-i18n="method_note">Facts are sourced; analysis, scenarios and recommendations are WhyItLands’ own reading. AI-assisted research, reviewed by Jalal Boucheikha.</p>
<div style="margin-top:40px">{feedback_card()}</div>
</div></div>
<section class="section"><div class="wrap"><div class="section-head"><div>{i('read_next', 'Read next', 'div', 'kicker')}</div></div><div class="bgrid">{rel}</div></div></section>
<button class="btn btn-ink backpill" id="backpill" hidden data-i18n="back_text">↩ Back to the text</button>
</main>
"""
    return out + footer()


def page_briefings_index():
    out = head("Briefings · WhyItLands", "Long-form analyses confronting governments, industry and schools of thought on how geopolitics lands on parcels and cross-border e-commerce logistics.", "/briefings/")
    out += header("briefings") + regionbar(REGION_ORDER, "GLOBAL")
    out += f"""<main id="main">
<section class="rhero"><div class="wrap"><div class="kicker" data-i18n="briefings_kicker">Briefings</div><h1 data-i18n="briefings_h1">Where it lands, region by region.</h1><p data-i18n="briefings_dek">Each briefing confronts the positions of governments, industry and schools of thought, then spells out what it means for parcel volumes, landed cost, networks and contracts.</p></div></section>
<section class="section"><div class="wrap">
<div class="bfilters"><input class="input" type="search" id="bq" data-i18n-ph="bf_search" placeholder="Search briefings (topic, country, company…)" aria-label="Search briefings">
<select class="input" id="bm" aria-label="Month"><option value="" data-i18n="bf_all_dates">All dates</option>{''.join(f'<option value="{m}">{datetime.date.fromisoformat(m + "-01").strftime("%B %Y")}</option>' for m in sorted({b["date"][:7] for b in briefings}, reverse=True))}</select>
<a class="more" href="/archive" data-i18n="bf_archive">Weekly editions archive →</a></div>
<div class="bgrid" data-filter-regions data-searchable>{''.join(bcard(b) for b in briefings)}</div>
<p class="empty" id="bnone" hidden data-i18n="bf_none">No briefing matches these filters.</p></div></section>
</main>
"""
    return out + footer()


def page_doctrines():
    d = doctrines
    S = d.get("sources", [])
    bysl = {b["slug"]: b for b in briefings}
    cards = []
    for sc in d["schools"]:
        links = "".join(f'<a href="/briefings/{s}">{E(bysl[s]["title"])}</a>' for s in sc.get("briefings", []) if s in bysl)
        cards.append(f"""<article class="school" id="{E(sc['key'])}"><h2>{E(sc['name'])}</h2><div class="thinkers">{E(sc['thinkers'])}</div>
<dl><dt data-i18n="doc_idea">Core idea</dt><dd>{E(plain(sc['idea']))}</dd><dt data-i18n="doc_trade">How it sees trade</dt><dd>{E(plain(sc['trade']))}</dd><dt data-i18n="doc_parcel">What it means for the parcel</dt><dd>{E(plain(sc['parcel']))}</dd><dt data-i18n="doc_seen">Where you see it in 2026</dt><dd>{E(plain(sc['seen_in']))}{cites(sc.get('src'), S)}</dd></dl>
{('<div class="doc-links"><span class="kicker" data-i18n="doc_read">Read it applied</span>' + links + '</div>') if links else ''}</article>""")
    toc = "".join(f'<a class="chip" href="#{E(sc["key"])}">{E(sc["name"])}</a>' for sc in d["schools"])
    srcs = "".join(f'<li id="s-{n}"><a href="{E(s["u"])}" rel="noopener">{E(s["t"])}</a>{(" · " + E(s["pub"])) if s.get("pub") else ""}</li>' for n, s in enumerate(S, 1))
    intro = "".join(f"<p>{E(plain(p))}</p>" for p in (d["intro"] if isinstance(d["intro"], list) else d["intro"].split("\n\n")))
    out = head("Doctrines · WhyItLands", "The schools of strategic and economic thought behind today's trade decisions, and what each one means for parcels and cross-border e-commerce.", "/doctrines")
    out += header("doctrines")
    out += f"""<main id="main">
<section class="rhero"><div class="wrap"><div class="kicker" data-i18n="nav_doctrines">Doctrines</div><h1>{E(d.get('title', 'Doctrines: the lenses behind the decisions'))}</h1><div class="doc-intro">{intro}</div></div></section>
{subnav([(sc["key"], "", re.split(r"[,(:]", sc["name"])[0].strip()) for sc in d["schools"]])}
<section class="section"><div class="wrap"><div class="chips chips-light doc-toc">{toc}</div><div class="schools">{''.join(cards)}</div>
<section class="sources-list" style="max-width:760px"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section></div></section>
</main>
"""
    return out + footer()


# ---------- Market intelligence ----------
MARKETS = {}
MARKET_ORDER = ["GLOBAL", "EU", "UK", "NA", "SA", "AS", "CN", "ME", "NAF"]
for _mf in sorted((C / "markets").glob("*.json")) if (C / "markets").exists() else []:
    _md = json.loads(_mf.read_text())
    _ms = _md.get("sources", [])
    for _rk, _rv in _md.get("regions", {}).items():
        _slot = MARKETS.setdefault(_rk, {"take": "", "companies": [], "watch": []})
        if _rv.get("take"):
            _slot["take"] = (_slot["take"] + " " + _rv["take"]).strip()
        for _c in _rv.get("companies", []):
            _c["_src"] = [_ms[n] for n in _c.get("src", []) if isinstance(n, int) and 0 <= n < len(_ms)]
            _slot["companies"].append(_c)
        _slot["watch"] += _rv.get("watch", [])


def chg_class(s):
    s = (s or "").strip()
    return "up" if s.startswith("+") else ("down" if s.startswith(("-", "−")) else "")


def company_card(c):
    def kpi(label, val, chg, extra=""):
        if not val:
            return ""
        return (f'<div class="kpi"><span class="kpi-l">{E(label)}</span><span class="kpi-v">{E(val)}</span>'
                f'{("<span class=" + chr(34) + "kpi-c " + chg_class(chg) + chr(34) + ">" + E(chg) + "</span>") if chg else ""}{extra}</div>')
    margin = f'<span class="kpi-m">margin {E(c["margin"])}</span>' if c.get("margin") and c["margin"] != "not disclosed" else ""
    segs = ""
    if c.get("segments"):
        segs = '<table class="segs"><thead><tr><th data-i18n="mk_segment">Segment</th><th data-i18n="mk_revenue">Revenue</th><th data-i18n="mk_profit">Profit</th><th></th></tr></thead><tbody>' + "".join(
            f'<tr><td>{E(s.get("name", ""))}</td><td>{E(s.get("revenue", ""))}</td><td>{E(s.get("ebit", ""))}</td><td class="snote">{E(s.get("note", ""))}</td></tr>' for s in c["segments"]) + "</tbody></table>"
    lst = lambda xs: "".join(f"<li>{E(x)}</li>" for x in (xs or []))
    srcs = " ".join(f'<a href="{E(s["u"])}" rel="noopener">{E(s.get("pub") or s["t"])}</a>' for s in c.get("_src", []))
    cid = re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-")
    return f"""<article class="co" id="{cid}">
<div class="co-head"><div><h3>{E(c['name'])}</h3><div class="co-seg">{E(c.get('segment', ''))}</div></div><div class="co-per">{E(c.get('period', ''))}{(' · ' + E(c['reported'])) if c.get('reported') else ''}</div></div>
<div class="kpis">{kpi('Revenue', c.get('revenue'), c.get('revenue_chg'))}{kpi(c.get('ebit_label') or 'Operating profit', c.get('ebit'), c.get('ebit_chg'), margin)}</div>
{('<p class="co-vol"><b data-i18n="mk_volumes">Volumes</b> ' + E(c['volume']) + '</p>') if c.get('volume') else ''}
{('<p class="co-prev"><b data-i18n="mk_trend">Trend</b> ' + E(c['vs_prev']) + '</p>') if c.get('vs_prev') else ''}
{('<p class="co-why"><b data-i18n="mk_why">Why</b> ' + E(c['exposure']) + '</p>') if c.get('exposure') else ''}{story_chips(c.get('stories'))}
<div class="co-cols"><div><div class="kicker" data-i18n="mk_drivers">What drove it</div><ul>{lst(c.get('highlights'))}</ul></div><div><div class="kicker" style="color:var(--coral)" data-i18n="mk_challenges">Main challenges</div><ul>{lst(c.get('challenges'))}</ul></div></div>
{segs}
{('<p class="co-out"><b data-i18n="mk_outlook">Outlook</b> ' + E(c['outlook']) + '</p>') if c.get('outlook') else ''}
{('<p class="co-src"><span data-i18n="sources_art">Sources</span>: ' + srcs + '</p>') if srcs else ''}
</article>"""


def market_summary_table(k):
    rows = "".join(f'<tr><td class="co-n"><a href="#{re.sub(r"[^a-z0-9]+", "-", c["name"].lower()).strip("-")}">{E(c["name"])}</a></td><td class="date">{E(c.get("period", ""))}</td><td>{E(c.get("revenue") or "")} <span class="{chg_class(c.get("revenue_chg"))}">{E(c.get("revenue_chg") or "")}</span></td><td>{E(c.get("ebit") or "")} <span class="{chg_class(c.get("ebit_chg"))}">{E(c.get("ebit_chg") or "")}</span></td></tr>' for c in MARKETS[k]["companies"] if c.get("revenue"))
    if not rows:
        return ""
    return f'<div class="table-wrap mk-table"><table><thead><tr><th data-i18n="th_company">Company</th><th data-i18n="mk_period">Period</th><th data-i18n="mk_revenue">Revenue</th><th data-i18n="mk_profit">Operating profit</th></tr></thead><tbody>{rows}</tbody></table></div>'


def page_markets():
    desks = []
    for k in MARKET_ORDER:
        if k not in MARKETS:
            continue
        m = MARKETS[k]
        watch = "".join(f'<li><span class="tl-when">{E(w.get("date", ""))}</span><span>{E(w.get("what", ""))}</span></li>' for w in m["watch"])
        hidden = "" if k == "GLOBAL" else " hidden"
        desks.append(f"""<div data-show="{show_for(k)}" id="desk-{k}"{hidden}>
<section class="rhero"><div class="wrap"><div class="kicker"><span data-region-label="{k}">{RNAME[k]}</span> · <span data-i18n="mk_kicker">Market intelligence</span></div>
<h1 data-i18n="mk_h1">Who is winning, who is paying.</h1><p class="mk-take"><b data-i18n="mk_our_read">Our read</b> {E(m['take'])}</p></div></section>
{subnav([("sig-" + k if signals_block(k) else None, "si_k", "Signals"), ("dd-" + k if comp_teasers(k) else None, "cp_k", "Competition deep dive"), ("pw-" + k if watch_block(k) else None, "pw_k", "Price and service watch"), ("mv-" + k if moves_block(k) else None, "mv_k", "Moves"), ("sh-" + k if shoppers_block(k) else None, "sh_k", "Shopper pulse"), ("res-" + k, "mk_res_k", "Results"), ("solutions" if SOL else None, "sol_kicker", "Solution landscape")])}
{signals_block(k, sid="sig-" + k)}<div id="dd-{k}">{comp_teasers(k)}</div>{watch_block(k, sid="pw-" + k)}{moves_block(k, sid="mv-" + k)}{shoppers_block(k, sid="sh-" + k)}
<section class="section" id="res-{k}"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="mk_res_k">Results</div><h2 data-i18n="mk_res_h">Latest quarterly results</h2></div></div>{market_summary_table(k)}
<div class="cos">{''.join(company_card(c) for c in m['companies'])}</div>
{('<h2 style="margin:40px 0 14px" data-i18n="mk_next">Next results and dates</h2><ul class="watch">' + watch + '</ul>') if watch else ''}
</div></section></div>""")
    out = head("Market Intelligence · WhyItLands", "Latest quarterly results of the main postal, parcel, express and e-commerce players by region: revenue, operating profit, trend, drivers and challenges.", "/markets")
    out += header("markets") + regionbar(REGION_ORDER, "GLOBAL")
    sol = ""
    if SOL:
        sol = f"""<section class="section" id="solutions" style="padding-top:0"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="sol_kicker">Solution landscape</div><h2 data-i18n="sol_h">Who helps comply with the new rules</h2><p style="margin-top:14px;color:var(--muted-2);max-width:820px">{E(SOL['intro'])}</p></div></div>
<div class="topics" data-filter-topics>{''.join(topic_html(tp) for tp in SOL['topics'])}</div></div></section>"""
    out += '<main id="main" data-region-page>' + "".join(desks) + sol + '<section class="section" style="padding-top:0"><div class="wrap"><p class="method-note" data-i18n="mk_note">Figures come from company results releases or quality financial press, as published; periods differ by company. Our read is WhyItLands’ analysis.</p></div></section></main>\n'
    return out + footer()


def home_markets():
    if not MARKETS:
        return ""
    names = [c["name"] for k in MARKET_ORDER if k in MARKETS for c in MARKETS[k]["companies"][:2]]
    return f"""<section class="section" style="padding-top:0"><div class="wrap"><a class="mk-teaser" href="/markets"><div><div class="kicker" data-i18n="mk_kicker">Market intelligence</div><h3 data-i18n="mk_h1">Who is winning, who is paying.</h3><p>{E(", ".join(names))} …</p></div><span class="more" data-i18n="mk_open">Open →</span></a></div></section>"""


def desk_markets(k):
    if k not in MARKETS:
        return ""
    names = ", ".join(c["name"] for c in MARKETS[k]["companies"][:6])
    return f"""<section class="section" style="padding-bottom:0"><div class="wrap"><a class="mk-teaser" href="/markets#{k.lower()}"><div><div class="kicker" data-i18n="mk_kicker">Market intelligence</div><h3 data-i18n="mk_teaser">Latest results of the region's players</h3><p>{E(names)}</p></div><span class="more" data-i18n="mk_open">Open →</span></a></div></section>"""


# ---------- Archive ----------
ARCH = []
for _af in sorted((C / "archive").glob("*.json"), reverse=True) if (C / "archive").exists() else []:
    ARCH.append(json.loads(_af.read_text()))
ARCH_BRIEFS = []
for _af in sorted((C / "archive" / "briefings").glob("*.json")) if (C / "archive" / "briefings").exists() else []:
    _b = json.loads(_af.read_text()); _b["_ver"] = _af.stem.split("@")[1]; ARCH_BRIEFS.append(_b)


def date_label(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def page_archive():
    eds = []
    for a in ARCH:
        h = a["home"]["hero"]
        nl = (ROOT / "newsletter" / f"{a.get('newsletter', {}).get('send_date', '')}.html")
        nl_link = f'<a href="/archive/newsletter/{a["newsletter"]["send_date"]}">Newsletter of {date_label(a["newsletter"]["send_date"])}</a>' if a.get("newsletter") and nl.exists() and a["newsletter"]["send_date"] <= datetime.date.today().isoformat() else ""
        eds.append(f"""<article class="ed" data-date="{a['edition']}"><div class="ed-date">{E(date_label(a['edition']))}</div><div><a class="ed-t" href="/archive/{a['edition']}">{E(h['title'])} <em>{E(h.get('title_em', ''))}</em></a>
<p>{E(h['dek'])}</p><div class="ed-links"><a href="/archive/{a['edition']}" data-i18n="ar_open">Open this edition →</a>{nl_link}</div></div></article>""")
    vers = "".join(f'<li><a href="/archive/briefings/{E(b["slug"])}-{E(b["_ver"])}">{E(b["title"])}</a> <span class="tl-when">version of {E(date_label(b["_ver"]))}</span></li>' for b in sorted(ARCH_BRIEFS, key=lambda x: x["_ver"], reverse=True))
    out = head("Archive · WhyItLands", "Every weekly edition of WhyItLands, with its front page, briefings and newsletter.", "/archive")
    out += header("archive")
    out += f"""<main id="main"><section class="rhero"><div class="wrap"><div class="kicker" data-i18n="ar_kicker">Archive</div><h1 data-i18n="ar_h1">Every edition, kept.</h1><p data-i18n="ar_dek">Each week’s front page, briefings and newsletter stay available, so you can see what we said and when.</p></div></section>
<section class="section"><div class="wrap"><div class="eds">{''.join(eds)}</div>
{('<h2 style="margin:40px 0 14px" data-i18n="ar_versions">Earlier versions of briefings</h2><ul class="watch">' + vers + '</ul>') if vers else ''}
<p style="margin-top:30px"><a class="btn btn-ink" href="/briefings/" data-i18n="ar_all_briefings">All briefings, by date and region →</a></p></div></section></main>
"""
    return out + footer()


def page_edition(a):
    h = a["home"]; hero = h["hero"]
    chain = "".join(f'<li><span class="n">{n}</span><div><b>{E(c["k"].upper())}</b><span>{E(c["t"])}</span></div></li>' for n, c in enumerate(h["chain"], 1))
    tiles = "".join(f'<article class="tile {w.get("style", "")}"><span class="tag">{E(w["tag"])}</span>{("<span class=big>" + E(w["big"]) + "</span>") if w.get("big") else ""}{("<p class=lede>" + E(w["lede"]) + "</p>") if w.get("lede") else ""}{("<p>" + E(w["text"]) + "</p>") if w.get("text") else ""}<span class="src">{src_link(w["src"], w.get("url"))}</span></article>' for w in h.get("wire", []))
    deals = "".join(f'<tr><td class="date">{E(d["date"])}</td><td class="co">{E(d["co"])}</td><td>{E(d["deal"])}</td><td><span class="pill">{E(d["region"])}</span></td><td>{src_link(d["src"], d.get("url"))}</td></tr>' for d in h.get("deals", []))
    live = {b["slug"] for b in briefings}
    bl = "".join(f'<li><a href="/briefings/{E(b["slug"])}">{E(b["title"])}</a> <span class="tl-when">{E(b["section"])}</span></li>' if b["slug"] in live else f'<li>{E(b["title"])}</li>' for b in a["briefings"])
    out = head(f"Edition of {date_label(a['edition'])} · WhyItLands", hero["dek"], f"/archive/{a['edition']}")
    out += header("archive")
    out += f"""<main id="main"><div class="ar-banner"><div class="wrap"><span data-i18n="ar_banner">Archived edition</span> · {E(date_label(a['edition']))} · <a href="/archive" data-i18n="ar_back">All editions</a> · <a href="/" data-i18n="ar_current">Current edition</a></div></div>
<section class="hero"><div class="wrap hero-grid"><div><span class="kicker">{E(hero['kicker'])}</span><h1>{E(hero['title'])}<br><em>{E(hero.get('title_em', ''))}</em></h1><p class="dek">{E(hero['dek'])}</p></div>
<aside class="chain"><span class="kicker" data-i18n="why_lands_here">Why it lands here</span><ol>{chain}</ol></aside></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div>{i('briefings_kicker', 'Briefings', 'div', 'kicker')}<h2>Briefings of the week</h2></div></div><ul class="watch">{bl}</ul></div></section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="section-head"><div>{i('wire_kicker', 'Industry wire', 'div', 'kicker')}{i('wire_title', 'What moved this week', 'h2')}</div></div><div class="bento">{tiles}</div></div></section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="section-head"><div>{i('deals_kicker', 'Deals & investments', 'div', 'kicker')}{i('deals_title', 'The deal tracker', 'h2')}</div></div><div class="table-wrap"><table><tbody>{deals}</tbody></table></div></div></section>
</main>
"""
    return out + footer()


def page_briefing_version(b):
    html_ = page_briefing(b)
    return html_.replace('<main id="main">', f'<main id="main"><div class="ar-banner"><div class="wrap"><span data-i18n="ar_banner_b">Archived version</span> · {E(date_label(b["_ver"]))} · <a href="/briefings/{E(b["slug"])}" data-i18n="ar_latest">Read the latest version</a></div></div>', 1).replace(f'<link rel="canonical" href="{BASE}/briefings/{b["slug"]}">', f'<link rel="canonical" href="{BASE}/briefings/{b["slug"]}"><meta name="robots" content="noindex">')


# ---------- Storylines (golden thread) ----------
_stp = C / "storylines.json"
STORYDATA = json.loads(_stp.read_text()) if _stp.exists() else {"storylines": [], "sources": []}
STORIES = {s["key"]: s for s in STORYDATA["storylines"]}
_bp = C / "barometer.json"
BARO = json.loads(_bp.read_text()) if _bp.exists() else None
LAYERS = [("geopolitics", "Geopolitics"), ("decision", "Decision & law"), ("market", "Market"), ("parcel", "Parcel impact")]
LAYER_NAME = dict(LAYERS)
DIMS = [("cost", "Cost"), ("speed", "Speed"), ("volume", "Volume"), ("compliance", "Compliance"), ("network", "Network")]
DIM_NAME = dict(DIMS)


def story_chips(keys, layer=None, link=True):
    keys = [k for k in (keys or []) if k in STORIES]
    if not keys and not layer:
        return ""
    lay = f'<span class="lay lay-{layer}" data-i18n="lay_{layer}">{E(LAYER_NAME.get(layer, layer))}</span>' if layer in LAYER_NAME else ""
    ch = "".join((f'<a class="schip" href="/storylines/{k}">' if link else '<span class="schip">') + E(STORIES[k]["short"]) + ('</a>' if link else '</span>') for k in keys)
    return f'<span class="chips-s">{lay}{ch}</span>'


def st_cites(idx):
    S = STORYDATA["sources"]
    idx = [n for n in (idx or []) if isinstance(n, int) and 0 <= n < len(S)]
    return ('<sup class="cite">' + "".join(f'<a href="#s-{n + 1}" title="{E(S[n].get("pub") or S[n]["t"])}">{n + 1}</a>' for n in idx) + "</sup>") if idx else ""


ARROW = {"up": "↑", "down": "↓", "mixed": "↕", "flat": "→"}


def mini_chain(s):
    c = s["chain"]
    first = lambda L: plain(c.get(L, [{}])[0].get("text", "")) if c.get(L) else ""
    return "".join(f'<li class="mc-{L}"><b data-i18n="lay_{L}">{E(n)}</b><span>{E(first(L))}</span></li>' for L, n in LAYERS)


def story_card(s):
    return f"""<a class="scard" href="/storylines/{s['key']}" data-regions="{','.join(s.get('regions', []))}"><span class="kicker">{E(' · '.join(RNAME.get(r, r) for r in s.get('regions', [])))}</span><h3>{E(s['title'])}</h3><p>{E(plain(s['why']))}</p><ol class="minichain">{mini_chain(s)}</ol></a>"""


def company_region(name):
    for k, m in MARKETS.items():
        for c in m["companies"]:
            if c["name"] == name:
                return k
    return None


def page_story(s):
    c = s["chain"]
    cols = []
    for L, n in LAYERS:
        items = []
        for it in c.get(L, []):
            if L == "parcel":
                items.append(f'<li><span class="pdim">{ARROW.get(it.get("dir"), "")} <span data-i18n="dim_{it.get("dim")}">{E(DIM_NAME.get(it.get("dim"), it.get("dim", "")))}</span></span><p>{E(plain(it["text"]))}{st_cites(it.get("src"))}</p></li>')
            else:
                stt = f'<span class="pill st-{E(it.get("status", "").replace(" ", "-"))}">{E(it.get("status", ""))}</span>' if it.get("status") else ""
                items.append(f'<li><span class="tl-when">{E(it.get("date", ""))}</span>{stt}<p>{E(plain(it["text"]))}{st_cites(it.get("src"))}</p></li>')
        cols.append(f'<div class="layer layer-{L}"><div class="layer-h"><span class="ln">{LAYERS.index((L, n)) + 1}</span><span data-i18n="lay_{L}">{E(n)}</span></div><ul>{"".join(items)}</ul></div>')
    docs = "".join(f'<a class="schip" href="/doctrines#{E(k)}">{E(next((x["name"] for x in (doctrines or {}).get("schools", []) if x["key"] == k), k))}</a>' for k in s.get("doctrines", []))
    bys = {b["slug"]: b for b in briefings}
    brs = "".join(bcard(bys[x]) for x in s.get("briefings", []) if x in bys)
    cos = "".join(f'<a class="schip" href="/markets#{(company_region(n) or "global").lower()}">{E(n)}</a>' for n in s.get("companies", []))
    sols = "".join(f'<a class="schip" href="/markets#solutions">{E(next((t["title"] for t in (SOL or {}).get("topics", []) if t["key"] == k), k))}</a>' for k in s.get("solutions", []))
    nxt = "".join(f'<li><span class="tl-when">{E(x["date"])}</span><span>{E(x["text"])}</span></li>' for x in s.get("next", []))
    used = sorted({n for L, _ in LAYERS for it in c.get(L, []) for n in (it.get("src") or [])})
    S = STORYDATA["sources"]
    srcs = "".join(f'<li id="s-{n + 1}" value="{n + 1}"><a href="{E(S[n]["u"])}" rel="noopener">{E(S[n]["t"])}</a>{(" · " + E(S[n]["pub"])) if S[n].get("pub") else ""}</li>' for n in used if n < len(S))
    others = "".join(story_card(x) for x in STORYDATA["storylines"] if x["key"] != s["key"] and set(x.get("regions", [])) & set(s.get("regions", [])))[:0] or ""
    out = head(f"{s['title']} · WhyItLands", plain(s["why"]), f"/storylines/{s['key']}")
    out += header("storylines")
    out += f"""<main id="main">
<section class="rhero"><div class="wrap"><div class="kicker"><span data-i18n="st_kicker">Storyline</span> · {E(' · '.join(RNAME.get(r, r) for r in s.get('regions', [])))}</div><h1>{E(s['title'])}</h1><p>{E(plain(s['why']))}</p></div></section>
<section class="section"><div class="wrap">
<div class="section-head" id="chain"><div><div class="kicker" data-i18n="st_chain_k">The chain</div><h2 data-i18n="st_chain_h">From geopolitics to the parcel</h2></div></div>
<div class="chain4">{''.join(cols)}</div>
<div class="st-read"><div class="kicker" data-i18n="mk_our_read">Our read</div><p>{E(plain(s.get('our_read', '')))}</p></div>
{('<h3 class="st-sub" id="next" data-i18n="st_next">What comes next</h3><ul class="watch">' + nxt + '</ul>') if nxt else ''}
{story_signals(s['key'])}
{story_radar(s['key'])}
{story_shoppers(s['key'])}
{('<h3 class="st-sub" data-i18n="st_lens">The lens behind the decisions</h3><div class="chips-row">' + docs + '</div>') if docs else ''}
{('<h3 class="st-sub" data-i18n="st_cos">Companies visibly affected</h3><div class="chips-row">' + cos + '</div>') if cos else ''}
{('<h3 class="st-sub" data-i18n="st_sols">Solution landscape</h3><div class="chips-row">' + sols + '</div>') if sols else ''}
{('<h3 class="st-sub" id="analysis" data-i18n="st_brs">Read the full analysis</h3><div class="bgrid">' + brs + '</div>') if brs else ''}
<section class="sources-list" id="sources" style="max-width:860px"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section>
<p style="margin-top:24px"><a class="btn btn-ink" href="/storylines" data-i18n="st_all">All storylines →</a></p>
</div></section></main>
"""
    _items = [(a, k, l) for a, k, l in [("chain", "st_chain_k", "The chain"), ("next", "st_next", "What comes next"), ("signals", "st_signals", "Signals"), ("rules", "st_rules", "Rules"), ("shoppers", "st_shop", "Shoppers"), ("analysis", "st_brs", "Read the full analysis"), ("sources", "sources_art", "Sources")] if f'id="{a}"' in out]
    _i = out.index("</section>", out.index('<main id="main">')) + len("</section>")
    out = out[:_i] + subnav(_items) + out[_i:]
    return out + footer()


def page_storylines():
    cards = "".join(story_card(s) for s in STORYDATA["storylines"])
    out = head("Storylines · WhyItLands", "Each storyline follows one chain, from geopolitics to decisions and laws, to market reactions, to the impact on parcels.", "/storylines")
    out += header("storylines") + regionbar(REGION_ORDER, "GLOBAL")
    out += f"""<main id="main" data-region-page><section class="rhero"><div class="wrap"><div class="kicker" data-i18n="st_kicker_all">Storylines</div><h1 data-i18n="st_h1">The why behind the whats.</h1><p>{E(plain(STORYDATA.get('intro', '')))}</p>
<ol class="legend4">{''.join(f'<li class="mc-{L}"><b data-i18n="lay_{L}">{E(n)}</b></li>' for L, n in LAYERS)}</ol></div></section>
<section class="section"><div class="wrap"><div class="sgrid" data-filter-stories data-limit-vis="6">{cards}</div></div></section></main>
"""
    return out + footer()


def barometer_block(k):
    if not BARO or k not in BARO.get("regions", {}):
        return ""
    gs = []
    for g in BARO["regions"][k]["gauges"]:
        lv = int(g.get("level", 0))
        segs = "".join(f'<i class="{"on" if n < lv else ""}"></i>' for n in range(5))
        st = "".join(f'<a href="/storylines/{x}">{E(STORIES[x]["short"])}</a>' for x in g.get("stories", []) if x in STORIES)
        gs.append(f'<div class="gauge lv{lv}"><div class="g-top"><span data-i18n="dim_{g["dim"]}">{E(DIM_NAME.get(g["dim"], g["dim"]))}</span><span class="g-tr tr-{g.get("trend")}">{ARROW.get(g.get("trend"), "")}</span></div><div class="g-bar">{segs}</div><p>{E(g.get("note", ""))}</p><div class="g-st">{st}</div></div>')
    return f'<div class="baro" data-show="{k}"{"" if k == "GLOBAL" else " hidden"}>{"".join(gs)}</div>'


def home_barometer():
    if not BARO:
        return ""
    return f"""<section class="section baro-sec" id="barometer"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="baro_kicker">Parcel barometer</span> · <span data-current-region>GLOBAL</span></div><h2 data-i18n="baro_h">Pressure on the parcel, and why.</h2></div><a class="more" href="/storylines" data-i18n="st_all">All storylines →</a></div>
{''.join(barometer_block(k) for k in REGION_ORDER)}
<p class="method-note">{E(BARO.get('note', ''))} · <span data-i18n="baro_asof">As of</span> {E(date_label(BARO.get('as_of', home.get('edition', ''))))}</p>
</div></section>"""


def home_storylines():
    if not STORYDATA["storylines"]:
        return ""
    return f"""<section class="section" id="storylines" style="padding-top:0"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="st_kicker_all">Storylines</span> · <span data-current-region>GLOBAL</span></div><h2 data-i18n="st_home_h">Follow the thread</h2></div><a class="more" href="/storylines" data-i18n="st_all">All storylines →</a></div>
<div class="sgrid" data-filter-stories data-limit-vis="6">{''.join(story_card(s) for s in STORYDATA['storylines'])}</div></div></section>"""


def page_glossary():
    rows = "".join(f'<div id="g-{E(k)}" style="padding:14px 0;border-top:1px solid var(--line)"><dt style="font-weight:600"><span style="font:500 14px var(--mono);color:var(--blue-ink);margin-right:10px">{E(k)}</span>{E(v[0])}</dt><dd style="margin:4px 0 0;color:var(--muted-2)">{E(v[1])}</dd></div>' for k, v in sorted(gloss.items()))
    out = head("Glossary · WhyItLands", "Acronyms used across WhyItLands briefings, from customs and trade to logistics and institutions.", "/glossary")
    out += header() + f'<main id="main" class="prose"><div class="kicker" data-i18n="glossary">Glossary</div><h1>Acronyms, spelled out</h1><dl>{rows}</dl></main>'
    return out + footer()


def page_method():
    out = head("Method · WhyItLands", "How WhyItLands selects, checks and explains the news: primary sources, local-language media, and an explicit what / why / what it means structure.", "/method")
    out += header() + """<main id="main" class="prose"><div class="kicker" data-i18n="method">Method</div><h1>How WhyItLands works</h1>
<p>WhyItLands connects geopolitical and regulatory events to their effects on e-commerce logistics, domestic and cross-border. Each item answers three questions: what happened, why, and what it means for the parcel.</p>
<h2>Sources first</h2>
<p>Facts come from primary sources where they exist: official texts, institutions (UPU, IPC, WTO, European Commission, U.S. CBP, WCO), company filings and results. Trade press and regional media are read in their original language to catch what international coverage misses. Every fact links to its source.</p>
<h2>AI-assisted, human-reviewed</h2>
<p>Monitoring and first drafts are assisted by AI. Selection, framing and final review are done by Jalal Boucheikha. Quotes are never invented; if a statement cannot be traced to a source, it is not published.</p>
<h2>Videos</h2>
<p>Videos are only embedded from identified channels (official bodies, organisers, companies or established media), after their content has been checked.</p>
<h2>Corrections</h2>
<p>Spotted an error? Use the feedback form on any page. Confirmed corrections are flagged in the article.</p>
<h2>Independence</h2>
<p>WhyItLands is a personal project. It has no sponsors and does not use confidential information from any employer. Views are the author’s own.</p>
</main>"""
    return out + footer()


def page_legal():
    out = head("Legal & privacy · WhyItLands", "Publisher, hosting and privacy information for whyitlands.com.", "/legal")
    out += header() + """<main id="main" class="prose"><div class="kicker" data-i18n="legal">Legal & privacy</div><h1>Legal notice and privacy</h1>
<h2>Publisher</h2>
<p>whyitlands.com is a personal, non-commercial publication by Jalal Boucheikha, who is responsible for its content. Contact: use the “Get in touch” form.</p>
<h2>Hosting</h2>
<p>Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, United States.</p>
<h2>Privacy</h2>
<p><strong>No advertising, no tracking cookies.</strong> Audience measurement uses PostHog, hosted in the EU, configured without cookies or persistent identifiers. It records anonymous interactions (pages viewed, language and region chosen, audio played) to improve the site.</p>
<p><strong>Newsletter.</strong> If you subscribe, your email, region and language are stored by Brevo (Sendinblue SAS, France) only to send the newsletter. Subscription requires email confirmation; every issue contains a one-click unsubscribe link.</p>
<p><strong>Contact and feedback.</strong> Messages are forwarded by email to the publisher and used only to reply. They are never shared or added to a mailing list. Feedback can be sent anonymously.</p>
<p><strong>Your rights.</strong> Under the GDPR you can access, correct or delete your data at any time via the contact form. You may also lodge a complaint with the CNIL (cnil.fr).</p>
<p><strong>Preferences.</strong> Your language and region choices are stored only in your browser.</p>
<h2>Content</h2>
<p>Texts © Jalal Boucheikha. Trademarks and quoted material belong to their owners. Embedded videos remain the property of their publishers.</p>
</main>"""
    return out + footer()


def page_404():
    out = head("Not found · WhyItLands", "This page has not landed.", "/404")
    out += header() + '<main id="main" class="prose" style="text-align:center;padding-bottom:40px"><div class="kicker">404</div><h1>This parcel went astray.</h1><p>The page you are looking for does not exist or has moved.</p><p><a class="btn btn-ink" href="/">Back to the front page</a></p></main>'
    return out + footer()


# ---------- Intelligence layer: signals, price and service watch, moves, competition ----------
_ip = C / "intel"
_ld = lambda p, d: json.loads(p.read_text()) if p.exists() else d
SIGNALS = _ld(_ip / "signals.json", {"signals": []})["signals"]
MOVES = _ld(_ip / "moves.json", {"moves": []})["moves"]
PWATCH = _ld(_ip / "watch.json", {"items": []})["items"]
COMPS = [json.loads(p.read_text()) for p in sorted((_ip / "competition").glob("*.json"))] if (_ip / "competition").exists() else []
CONF = {"low": 1, "medium": 2, "high": 3}
MOVE_T = {"capacity": "Capacity", "acquisition": "M&A", "network": "Network", "partnership": "Partnership", "closure": "Closure", "pricing": "Pricing", "product": "Product"}


def noread(t):
    t = re.sub(r"^\s*Our (reading|read)( is that)?\s*:?\s*", "", t or "", flags=re.I)
    return t[:1].upper() + t[1:]


def in_region(item, k):
    rs = item.get("regions") or []
    return k == "GLOBAL" or k in rs


def fdate(iso):
    try:
        d = datetime.date.fromisoformat(iso)
        return f"{d.day} {d.strftime('%b %Y')}"
    except Exception:
        return iso or ""


def signal_card(s, open_=False, anchor=False):
    lv = CONF.get(s.get("confidence"), 1)
    dots = "".join(f'<i class="{"on" if i < lv else ""}"></i>' for i in range(3))
    ev = "".join(f'<li><span class="tl-when">{E(fdate(e.get("date")))}</span><p><b>{E(e.get("co", ""))}</b> {E(e["text"])} <a class="src-a" href="{E(e["url"])}" rel="noopener">{E(e.get("src", "source"))}</a></p></li>' for e in s.get("evidence", []))
    mon = "".join(f"<li>{E(m)}</li>" for m in s.get("monitor", []))
    rg = " · ".join(RNAME.get(r, r) for r in s.get("regions", []))
    st = s.get("status", "emerging")
    return f"""<article class="sig"{(' id="sig-' + E(s['key']) + '"') if anchor else ''} data-regions="{','.join(s.get('regions', []))}">
<div class="sig-top"><span class="pill sig-st sig-{E(st)}" data-i18n="si_{E(st)}">{E(st.capitalize())}</span><span class="sig-conf" title="Confidence: {E(s.get('confidence', ''))}"><span data-i18n="si_conf">Confidence</span> <span class="dots">{dots}</span> <span data-i18n="si_c_{E(s.get('confidence', 'low'))}">{E(s.get('confidence', ''))}</span></span><span class="sig-rg">{E(rg)}</span></div>
<h3>{E(s['title'])}</h3><p class="sig-claim">{E(s['claim'])}</p>
<div class="sig-read"><b data-i18n="si_read">Our reading</b> {E(noread(s.get('inference', '')))}</div>
<details{' open' if open_ else ''}><summary><span data-i18n="si_evidence">The evidence</span> ({len(s.get('evidence', []))}) <span data-i18n="si_and">and what would change our mind</span></summary>
<ul class="sig-ev">{ev}</ul>
<div class="sig-cr"><div><div class="kicker" data-i18n="si_confirm">Would confirm it</div><p>{E(s.get('confirm', ''))}</p></div><div><div class="kicker" style="color:var(--coral)" data-i18n="si_refute">Would prove it wrong</div><p>{E(s.get('refute', ''))}</p></div></div>
{('<div class="kicker" data-i18n="si_monitor">What we monitor</div><ul class="sig-mon">' + mon + '</ul>') if mon else ''}
</details>{story_chips(s.get('stories'))}
</article>"""


def signals_block(k, items=None, sid=None):
    sig = items if items is not None else [s for s in SIGNALS if in_region(s, k) and k != "GLOBAL"] if k != "GLOBAL" else SIGNALS
    if not sig:
        return ""
    sig = sorted(sig, key=lambda s: (-CONF.get(s.get("confidence"), 0), s["title"]))
    return f"""<section class="section intel"{(' id="' + sid + '"') if sid else ''}><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="si_k">Signals</div><h2 data-i18n="si_h">What the facts add up to</h2><p class="intel-dek" data-i18n="si_dek">No single fact below is news. Put side by side, at least three dated, sourced facts from different players point to a shift nobody has announced. Each signal says how confident we are, and what would prove it wrong.</p></div></div>
<div class="sigs" data-limit-vis="6">{''.join(signal_card(s, anchor=(k == 'GLOBAL' and items is None)) for s in sig)}</div></div></section>"""


def watch_block(k, sid=None):
    items = [w for w in PWATCH if (k in (w.get("regions") or [])) or (k == "GLOBAL" and "GLOBAL" in (w.get("regions") or []))]
    if not items:
        return ""
    rows = "".join(f'<tr><td class="co-n">{E(w["carrier"])}</td><td>{E(w["item"])}{("<div class=snote>" + E(w["note"]) + "</div>") if w.get("note") else ""}</td><td class="pw-v">{E(w["value"])}{("<div class=snote>" + E(w["change"]) + "</div>") if w.get("change") else ""}</td><td class="date">{E(w.get("effective", ""))}</td><td><a class="src-a" href="{E(w["url"])}" rel="noopener">{E(w.get("src", "source"))}</a></td></tr>' for w in items)
    return f"""<section class="section intel"{(' id="' + sid + '"') if sid else ''} style="padding-top:0"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="pw_k">Price and service watch</div><h2 data-i18n="pw_h">What shipping costs right now</h2><p class="intel-dek" data-i18n="pw_dek">Published fuel surcharges, peak fees, 2027 rate increases, regulated tariffs and service changes, as the carriers and authorities state them. Fuel surcharges move weekly: check the date.</p></div></div>
<div class="table-wrap pw-table"><table><thead><tr><th data-i18n="pw_who">Carrier or authority</th><th data-i18n="pw_what">What</th><th data-i18n="pw_val">Value</th><th data-i18n="pw_when">Effective</th><th data-i18n="sources_art">Source</th></tr></thead><tbody>{rows}</tbody></table></div></div></section>"""


def moves_block(k, limit=14, sid=None):
    items = [m for m in MOVES if in_region(m, k)][:limit]
    if not items:
        return ""
    li = "".join(f'<li data-regions="{",".join(m.get("regions", []))}"><span class="tl-when">{E(fdate(m["date"]))}</span><div><span class="pill mv-t mv-{E(m.get("type", ""))}">{E(MOVE_T.get(m.get("type"), m.get("type", "")))}</span> <b>{E(m["co"])}</b><p>{E(m["text"])} <a class="src-a" href="{E(m["url"])}" rel="noopener">{E(m.get("src", "source"))}</a></p>{story_chips(m.get("stories"))}</div></li>' for m in items)
    return f"""<section class="section intel"{(' id="' + sid + '"') if sid else ''} style="padding-top:0"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="mv_k">Moves</div><h2 data-i18n="mv_h">Who is building, buying or pulling out</h2><p class="intel-dek" data-i18n="mv_dek">Capacity, network, M&amp;A, partnerships, closures and pricing moves, dated and sourced. Patterns across these lines are where the signals come from.</p></div></div>
<ul class="moves">{li}</ul></div></section>"""


SHOP = _ld(_ip / "shoppers.json", {"trends": []})
SH_THEME = {"speed": "Speed", "price": "Price", "duties": "Duties at checkout", "ooh": "Lockers and pick-up", "returns": "Returns", "platforms": "Platforms", "sustainability": "Sustainability", "trust": "Trust", "tracking": "Tracking"}
SH_DIR = {"up": "↑ rising", "down": "↓ falling", "flat": "→ stable", "new": "new reading"}


def shoppers_block(k, sid=None):
    ts = [t for t in SHOP.get("trends", []) if k == "GLOBAL" or k in t.get("regions", []) or (k == "EMEA" and set(t.get("regions", [])) & set(EMEA_SET))]
    if not ts:
        return ""
    def card(t):
        s_ = t.get("source", {})
        prev = f'<span class="sh-prev">{E(t["previous"])}</span>' if t.get("previous") else ""
        spon = f'<p class="sh-spon">{E(t["sponsor_note"])}</p>' if t.get("sponsor_note") else ""
        return f"""<article class="sh" data-regions="{','.join(t.get('regions', []))}">
<div class="sh-top"><span class="pill sh-th" data-i18n="sh_t_{E(t.get('theme', ''))}">{E(SH_THEME.get(t.get('theme'), t.get('theme', '')))}</span><span class="sh-rg">{E(' · '.join(RNAME.get(r, r) for r in t.get('regions', [])))}</span></div>
<h3>{E(t['title'])}</h3>
<div class="sh-num"><b>{E(t.get('big', ''))}</b><span>{E(t.get('label', ''))}</span></div>
<div class="sh-dir sh-{E(t.get('direction', ''))}">{E(SH_DIR.get(t.get('direction'), ''))} {prev}</div>
<div class="sig-read"><b data-i18n="sh_why">Why</b> {E(noread(t.get('why', '')))}</div>
<p class="sh-means"><b data-i18n="sh_means">What it means</b> {E(t.get('means', ''))}</p>
<p class="sh-src"><a class="src-a" href="{E(s_.get('u', '#'))}" rel="noopener">{E(s_.get('pub', 'source'))}{(', ' + E(s_['t'])) if s_.get('t') else ''}</a>{(' · ' + E(s_['method'])) if s_.get('method') else ''}</p>{spon}
{story_chips(t.get('stories'))}</article>"""
    return f"""<section class="section intel"{(' id="' + sid + '"') if sid else ''} style="padding-top:0"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="sh_k">Shopper pulse</div><h2 data-i18n="sh_h">What shoppers do with parcels, and why</h2><p class="intel-dek">{E(SHOP.get('intro', ''))}</p></div></div>
<div class="shs" data-limit-vis="6">{''.join(card(t) for t in ts)}</div></div></section>"""


def comp_teasers(k):
    cs = [c for c in COMPS if k == "GLOBAL" or c["region"] == k]
    if not cs:
        return ""
    cards = "".join(f'<a class="cp-teaser" href="/markets/{E(c["key"])}"><div class="kicker"><span data-i18n="cp_k">Competition deep dive</span> · {E(RNAME.get(c["region"], c["region"]))}</div><h3>{E(c["title"])}</h3><p>{E(c["dek"])}</p><span class="more" data-i18n="cp_open">Read the deep dive →</span></a>' for c in cs)
    return f'<section class="section" style="padding-top:0"><div class="wrap"><div class="cp-teasers">{cards}</div></div></section>'


def cp_cites(idx):
    idx = [n for n in (idx or []) if isinstance(n, int)]
    return ('<sup class="cite">' + "".join(f'<a href="#c-{n + 1}">{n + 1}</a>' for n in idx) + "</sup>") if idx else ""


CP_ARROW = {"up": ("▲", "up"), "down": ("▼", "down"), "flat": ("▬", "flat")}
POS_I18N = {"gaining": "cp_gaining", "holding": "cp_holding", "losing": "cp_losing"}


def cp_deep(c):
    """Scorecard, segment or country breakdown, price stack and scenarios for a deep dive."""
    out = {}
    sc = c.get("scorecard") or []
    if sc:
        def ar(v, kind):
            a, cls = CP_ARROW.get(v, ("", ""))
            lab = {"v": ("cp_volume", "Volume"), "y": ("cp_yield", "Yield")}[kind]
            return f'<span class="ar-l" data-i18n="{lab[0]}">{lab[1]}</span><span class="ar ar-{cls}" title="{E(v)}">{a} <span data-i18n="cp_{E(v)}">{E(v)}</span></span>'
        rows = "".join(f'<tr><td class="co-n">{E(x["name"])}</td><td>{ar(x.get("volume"), "v")}</td><td>{ar(x.get("yield"), "y")}</td><td><span class="pos pos-{E(x.get("position", ""))}" data-i18n="{POS_I18N.get(x.get("position"), "")}">{E(x.get("position", ""))}</span></td><td class="sc-why">{E(x.get("why", ""))}{cp_cites(x.get("src"))}</td></tr>' for x in sc)
        out["score"] = f"""<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_sc_k">Scorecard</div><h2 data-i18n="cp_sc_h">Who is gaining, who is losing</h2><p class="intel-dek" data-i18n="cp_sc_dek">Volume and yield (revenue per parcel) direction over the latest reported periods. The position column is our reading.</p></div></div>
<div class="table-wrap sc-table"><table><thead><tr><th data-i18n="cp_player">Player</th><th data-i18n="cp_volume">Volume</th><th data-i18n="cp_yield">Yield</th><th data-i18n="cp_position">Position</th><th data-i18n="cp_why">Why</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    seg = c.get("countries") or c.get("segments") or []
    if seg:
        isc = bool(c.get("countries"))
        cards = "".join(f"""<details class="cp-seg"{' open' if i == 0 else ''}><summary><h3>{E(x['name'])}</h3><span class="cp-seg-read"><b data-i18n="si_read">Our reading</b> {E(noread(x.get('read', '')))}</span></summary>
<dl><dt data-i18n="cp_size">Size</dt><dd>{E(x.get('size', ''))}</dd><dt data-i18n="cp_leaders">Leaders</dt><dd>{E(x.get('leaders', ''))}</dd><dt data-i18n="cp_dynamics">Dynamics</dt><dd>{E(x.get('dynamics', ''))}</dd><dt data-i18n="cp_rules">Rules that bite</dt><dd>{E(x.get('rules', ''))}{cp_cites(x.get('src'))}</dd></dl></details>""" for i, x in enumerate(seg))
        k, h = ("cp_ct_k", "cp_ct_h") if isc else ("cp_sg_k", "cp_sg_h")
        out["seg"] = f"""<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="{k}">{'Country by country' if isc else 'Segment by segment'}</div><h2 data-i18n="{h}">{'Six markets, six rulebooks' if isc else 'Five markets inside one market'}</h2><p class="intel-dek" data-i18n="cp_sg_dek">The first line of each card is our reading; open it for the sourced facts.</p></div></div><div class="cp-segs">{cards}</div>"""
    ps = c.get("price_stack") or []
    if ps:
        rows = "".join(f'<tr><td class="co-n">{E(x["carrier"])}</td><td>{E(x["item"])}</td><td class="pw-v">{E(x["value"])}</td><td class="date">{E(x.get("effective", ""))}</td><td>{cp_cites(x.get("src"))}</td></tr>' for x in ps)
        out["price"] = f"""<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_ps_k">The price stack</div><h2 data-i18n="cp_ps_h">What a shipper pays on top of the base rate</h2><p class="intel-dek" data-i18n="cp_ps_dek">Rate increases, fuel and peak surcharges as published by the carriers. Fuel moves weekly: check the date.</p></div></div>
<div class="table-wrap pw-table"><table><thead><tr><th data-i18n="pw_who">Carrier or authority</th><th data-i18n="pw_what">What</th><th data-i18n="pw_val">Value</th><th data-i18n="pw_when">Effective</th><th data-i18n="sources_art">Source</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    scn = c.get("scenarios") or []
    if scn:
        cards = "".join(f'<div class="cp-scn cp-scn-{i}"><div class="kicker" data-i18n="cp_l_{E(x.get("likelihood", "").replace(" ", "_"))}">{E(x.get("likelihood", ""))}</div><h3>{E(x["name"])}</h3><p>{E(noread(x.get("text", "")))}</p><p class="cp-trig"><b data-i18n="cp_triggers">Watch for</b> {E(x.get("triggers", ""))}</p></div>' for i, x in enumerate(scn))
        out["scn"] = f"""<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_scn_k">Next 12 months</div><h2 data-i18n="cp_scn_h">Three scenarios</h2><p class="intel-dek" data-i18n="cp_scn_dek">Our reading, grounded in the facts above. The likelihood labels are judgements, not probabilities.</p></div></div><div class="cp-scns">{cards}</div>"""
    return out


def page_competition(c):
    S = c.get("sources", [])
    stats = "".join(f'<div class="cp-stat"><b>{E(x["big"])}</b><span>{E(x["label"])}{cp_cites([x.get("src")])}</span></div>' for x in c.get("stats", []))
    players = "".join(f"""<article class="cp-pl"><div class="cp-pl-h"><h3>{E(p['name'])}</h3><span class="co-seg">{E(p.get('type', ''))}</span></div>
<p class="cp-scale">{E(p.get('scale', ''))}</p><p><b data-i18n="cp_strategy">Strategy</b> {E(p.get('strategy', ''))}</p><p><b data-i18n="cp_moves">Latest moves</b> {E(p.get('moves', ''))}</p><p class="cp-press"><b data-i18n="cp_pressure">Under pressure from</b> {E(p.get('pressure', ''))}{cp_cites(p.get('src'))}</p></article>""" for p in c.get("players", []))
    bgs = "".join(f'<div class="cp-bg"><h3>{E(b["h"])}</h3><p>{E(b["text"])}{cp_cites(b.get("src"))}</p></div>' for b in c.get("battlegrounds", []))
    imps = "".join(f'<div class="cp-imp"><div class="kicker">{E(i["who"])}</div><p>{E(i["text"])}</p></div>' for i in c.get("implications", []))
    wt = "".join(f'<li><span class="tl-when">{E(fdate(w["date"]))}</span><span>{E(w["what"])}</span></li>' for w in c.get("watch", []))
    sig = [s for s in SIGNALS if c["region"] in s.get("regions", [])]
    srcs = "".join(f'<li id="c-{n + 1}" value="{n + 1}"><a href="{E(s["u"])}" rel="noopener">{E(s["t"])}</a>{(" · " + E(s["pub"])) if s.get("pub") else ""}{(" · " + E(s["date"])) if s.get("date") else ""}</li>' for n, s in enumerate(S))
    D = cp_deep(c)
    out = head(f"{c['title']} · WhyItLands", c["dek"], f"/markets/{c['key']}")
    out += header("markets")
    out += "<!--CPMAIN-->"
    out += f"""<main id="main">
<section class="rhero"><div class="wrap"><div class="kicker"><a href="/markets#{c['region'].lower()}" style="color:inherit" data-i18n="nav_markets">Market Intelligence</a> · <span data-i18n="cp_k">Competition deep dive</span> · {E(RNAME.get(c['region'], c['region']))} · <span data-i18n="baro_asof">As of</span> {E(fdate(c.get('as_of', '')))}</div><h1>{E(c['title'])}</h1><p>{E(c['dek'])}</p></div></section>
<section class="section"><div class="wrap">
<div class="kicker" data-i18n="cp_structure">Market structure</div><div class="cp-stats">{stats}</div>
<div class="st-read"><div class="kicker" data-i18n="mk_our_read">Our read</div><p>{E(noread(c.get('our_read', '')))}</p></div>
{D.get('score', '')}
<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_bg_k">Battlegrounds</div><h2 data-i18n="cp_bg_h">Where the competition is fought</h2></div></div>
<div class="cp-bgs">{bgs}</div>
{D.get('seg', '')}{D.get('price', '')}
<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_pl_k">Players</div><h2 data-i18n="cp_pl_h">Who does what, and what squeezes them</h2><p class="intel-dek" data-i18n="cp_pl_dek">Scale and moves are sourced facts; strategy and pressure combine company statements with our reading, marked as such.</p></div></div>
<div class="cp-pls">{players}</div>
{D.get('scn', '')}
<div class="section-head" style="margin-top:44px"><div><div class="kicker" data-i18n="cp_imp_k">So what</div><h2 data-i18n="cp_imp_h">What it means for you</h2></div></div>
<div class="cp-imps">{imps}</div>
</div></section>
{signals_block(c['region'], sig) if sig else ''}
<section class="section" style="padding-top:0"><div class="wrap">
{('<h2 style="margin:0 0 14px" data-i18n="st_next">What comes next</h2><ul class="watch">' + wt + '</ul>') if wt else ''}
<section class="sources-list" style="max-width:900px"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section>
<p style="margin-top:24px"><a class="btn btn-ink" href="/markets#{c['region'].lower()}" data-i18n="cp_back">Back to Market Intelligence →</a></p>
</div></section></main>
"""
    pre, main = out.split("<!--CPMAIN-->")
    main, nav = auto_subnav(main, [("cp_sc_k", "scorecard", "Scorecard"), ("cp_bg_k", "battlegrounds", "Battlegrounds"), ("cp_ct_k", "countries", "Country by country"), ("cp_sg_k", "segments", "Segment by segment"), ("cp_ps_k", "prices", "The price stack"), ("cp_pl_k", "players", "Players"), ("cp_scn_k", "scenarios", "Next 12 months"), ("cp_imp_k", "so-what", "So what")])
    i_ = main.index("</section>") + len("</section>")
    return pre + main[:i_] + nav + main[i_:] + footer()


def story_shoppers(key):
    ts = [t for t in SHOP.get("trends", []) if key in (t.get("stories") or [])]
    if not ts:
        return ""
    return '<h3 class="st-sub" id="shoppers" data-i18n="st_shop">How shoppers are reacting</h3><div class="chips-row">' + "".join(f'<a class="schip" href="/markets#sh-{E((t.get("regions") or ["GLOBAL"])[0])}">{E(t.get("big", ""))} · {E(t["title"])}</a>' for t in ts) + "</div>"


def story_signals(key):
    sig = [s for s in SIGNALS if key in (s.get("stories") or [])]
    if not sig:
        return ""
    return '<h3 class="st-sub" id="signals" data-i18n="st_signals">Signals on this storyline</h3><div class="chips-row">' + "".join(f'<a class="schip" href="/markets#sig-{E(s["key"])}">{E(s["title"])}</a>' for s in sig) + "</div>"



# ---------- Regulatory Radar ----------
RADAR = []
for _f in sorted((C / "radar").glob("*.json")) if (C / "radar").exists() else []:
    RADAR += json.loads(_f.read_text()).get("items", [])
import sys as _sys
_sys.path.insert(0, str(ROOT / "tools"))
import thread as _thread
RLINKS = _thread.link_radar(RADAR, _thread.index_mentions(C)) if RADAR else {}
KIND_LABEL = {"briefing": "Briefing", "storyline": "Storyline", "signal": "Signal", "calendar": "Calendar", "competition": "Deep dive", "results": "Results", "move": "Move"}


def rr_mentions(key, date):
    ms = RLINKS.get(key, {}).get(date, [])
    if not ms:
        return ""
    order = list(KIND_LABEL)
    ms = sorted(ms, key=lambda m: order.index(m["kind"]) if m["kind"] in order else 99)
    a = lambda m: f'<a class="rr-m" href="{E(m["url"])}" title="{E(m["snippet"])}"><span class="rr-mk" data-i18n="rk_{m["kind"]}">{KIND_LABEL.get(m["kind"], m["kind"])}</span>{E(m["title"])}</a>'
    li = "".join(a(m) for m in ms[:5])
    more = f'<details class="rr-more"><summary>+{len(ms) - 5}</summary>{"".join(a(m) for m in ms[5:])}</details>' if len(ms) > 5 else ""
    return f'<div class="rr-ms"><span class="rr-ml" data-i18n="rr_also">Also on the site</span>{li}{more}</div>'


def radar_for_url(path):
    """Radar rules whose dates are mentioned on the page at this path."""
    out = []
    for it in RADAR:
        for d, ms in RLINKS.get(it["key"], {}).items():
            if any(m["url"].split("#")[0] == path for m in ms):
                out.append(it); break
    return out


RR_STATUS = {"consultation": "Consultation", "proposed": "Proposed", "adopted": "Adopted", "in-force": "In force", "suspended": "Suspended"}
RR_DOMAIN = {"customs": "Customs", "tax": "Tax", "trade": "Trade and tariffs", "postal": "Postal", "platforms": "Platforms", "product-safety": "Product safety", "data": "Data", "sustainability": "Sustainability", "labour": "Labour"}
RR_ORDER = {"in-force": 0, "adopted": 1, "proposed": 2, "consultation": 3, "suspended": 4}


def rr_next(it, today):
    ds = sorted(d["date"] for d in it.get("dates", []) if d.get("date", "") >= today)
    return ds[0] if ds else "9999"


def rr_card(it, today):
    S = it.get("sources", [])
    def cite(n):
        return f'<a class="src-a" href="{E(S[n]["u"])}" rel="noopener">{E(S[n].get("pub") or "source")}</a>' if isinstance(n, int) and 0 <= n < len(S) else ""
    dates = "".join(f'<li class="{"past" if d["date"] < today else ""}"><span class="tl-when" data-cd="{E(d["date"])}">{E(fdate(d["date"]))}</span><span>{E(d["what"])} {cite(d.get("src"))}{rr_mentions(it["key"], d["date"])}</span></li>' for d in sorted(it.get("dates", []), key=lambda d: d["date"]))
    hits = "".join(f"<span>{E(h)}</span>" for h in it.get("hits", []))
    prep = "".join(f"<li>{E(x)}</li>" for x in it.get("prepare", []))
    srcs = "".join(f'<li><a href="{E(x["u"])}" rel="noopener">{E(x["t"])}</a>{(" · " + E(x["pub"])) if x.get("pub") else ""}{(" · " + E(x["date"])) if x.get("date") else ""}</li>' for x in S)
    st = it.get("status", "")
    return f"""<article class="rr" id="rr-{E(it['key'])}" data-status="{E(it.get('status', ''))}" data-regions="{','.join(it.get('regions', []))}" data-domain="{E(it.get('domain', ''))}" data-next="{rr_next(it, today)}">
<div class="rr-top"><span class="pill rr-st rr-{E(st)}" data-i18n="rr_s_{E(st)}">{E(RR_STATUS.get(st, st))}</span><span class="rr-dom" data-i18n="rr_d_{E(it.get('domain', ''))}">{E(RR_DOMAIN.get(it.get('domain'), it.get('domain', '')))}</span><span class="rr-jur">{E(it.get('jurisdiction', ''))}</span></div>
<h3>{E(it['title'])}</h3><p>{E(it.get('summary', ''))}</p>
<div class="rr-parcel"><b data-i18n="rr_parcel">For a parcel</b> {E(it.get('parcel', ''))}</div>
{('<ul class="rr-dates">' + dates + '</ul>') if dates else ''}
<details><summary data-i18n="rr_more">Who it hits, what to prepare, our reading</summary>
{('<div class="kicker" data-i18n="rr_hits">Directly affected</div><div class="rr-hits">' + hits + '</div>') if hits else ''}
{('<div class="kicker" data-i18n="rr_prepare">What to prepare</div><ul class="rr-prep">' + prep + '</ul>') if prep else ''}
<div class="sig-read"><b data-i18n="si_read">Our reading</b> {E(noread(it.get('read', '')))}</div>
<div class="kicker" data-i18n="sources_art">Sources</div><ol class="rr-src">{srcs}</ol>
</details>{story_chips(it.get('stories'))}
</article>"""


def page_radar():
    today = datetime.date.today().isoformat()
    horizon = (datetime.date.today() + datetime.timedelta(days=550)).isoformat()
    ev = sorted(((d["date"], d["what"], it) for it in RADAR for d in it.get("dates", []) if today <= d["date"] <= horizon), key=lambda x: x[0])
    months, tl = {}, ""
    for d, w, it in ev:
        months.setdefault(d[:7], []).append((d, w, it))
    for m, rows in months.items():
        mlabel = datetime.date.fromisoformat(m + "-01").strftime("%B %Y")
        li = "".join(f'<li data-regions="{",".join(it.get("regions", []))}" data-domain="{E(it.get("domain", ""))}" data-date="{d}"><span class="cd" data-cd="{d}"></span><span class="tl-when">{E(fdate(d))}</span><div><a href="#rr-{E(it["key"])}">{E(it["title"])}</a><p>{E(w)}</p><span class="rr-jur">{E(it.get("jurisdiction", ""))}</span>{rr_mentions(it["key"], d)}</div></li>' for d, w, it in rows)
        tl += f'<div class="rr-month"><h3>{E(mlabel)}</h3><ul class="rr-tl">{li}</ul></div>'
    items = sorted(RADAR, key=lambda it: (rr_next(it, today), RR_ORDER.get(it.get("status"), 9)))
    doms = sorted({it.get("domain") for it in RADAR if it.get("domain")}, key=lambda d: list(RR_DOMAIN).index(d) if d in RR_DOMAIN else 99)
    dchips = '<button class="chip" data-domain-f="" aria-pressed="true" data-i18n="rr_all">All topics</button>' + "".join(f'<button class="chip" data-domain-f="{E(d)}" aria-pressed="false" data-i18n="rr_d_{E(d)}">{E(RR_DOMAIN.get(d, d))}</button>' for d in doms)
    n_force = sum(1 for it in RADAR if it.get("status") == "in-force")
    n_pipe = sum(1 for it in RADAR if it.get("status") in ("adopted", "proposed", "consultation"))
    out = head("Regulatory Radar · WhyItLands", "The rules reshaping e-commerce logistics, region by region: customs, tax, trade, postal, platform and product-safety measures, with their dates, who they hit and what to prepare.", "/radar")
    out += header("radar") + regionbar(REGION_ORDER, "GLOBAL")
    out += f"""<main id="main" data-region-page data-radar>
<section class="rhero"><div class="wrap"><div class="kicker"><span data-current-region>GLOBAL</span> · <span data-i18n="nav_radar">Regulatory Radar</span></div>
<h1 data-i18n="rr_h1">What the rules will change, and when.</h1>
<p data-i18n="rr_dek">Customs, tax, trade, postal, platform and product-safety rules that reshape the cost, data and liability of a parcel. Each one with its dates, who it hits, what to prepare and our reading. Sourced from the official texts first.</p>
<div class="rr-stats"><div><b id="rr-n">{len(RADAR)}</b><span data-i18n="rr_tracked">rules tracked</span></div><div><b id="rr-nf">{n_force}</b><span data-i18n="rr_inforce">already in force</span></div><div><b id="rr-np">{n_pipe}</b><span data-i18n="rr_pipe">in the pipeline</span></div><div class="rr-next"><b id="rr-next-cd">·</b><span><span data-i18n="rr_nextdl">Next deadline</span>: <a id="rr-next-a" href="#"></a></span></div></div>
</div></section>
{subnav([("agenda", "rr_tl_h", "The next 18 months"), ("register", "rr_reg_k", "The register")])}
<section class="section"><div class="wrap">
<div class="chips chips-light rr-domains" role="group" aria-label="Topic">{dchips}</div>
<div class="section-head" id="agenda" style="margin-top:28px"><div><div class="kicker" data-i18n="rr_tl_k">Agenda</div><h2 data-i18n="rr_tl_h">The next 18 months, date by date</h2></div></div>
<div class="rr-months">{tl}</div>
<div class="section-head" id="register" style="margin-top:56px"><div><div class="kicker" data-i18n="rr_reg_k">The register</div><h2 data-i18n="rr_reg_h">Every rule, what it does, what to prepare</h2><p class="intel-dek" data-i18n="rr_reg_dek">Ordered by the next deadline. Status reflects the legal state today: consultation, proposed, adopted (not yet applying), in force, or suspended.</p></div></div>
<div class="rrs">{''.join(rr_card(it, today) for it in items)}</div>
<p class="method-note" style="margin-top:32px" data-i18n="rr_note">Information, not legal advice. Dates come from official texts or quality legal and trade press, and slip often: always check the current text before acting.</p>
</div></section></main>
"""
    return out + footer()


def home_radar_list(n=6):
    today = datetime.date.today().isoformat()
    ev = sorted(((d["date"], d["what"], it) for it in RADAR for d in it.get("dates", []) if d["date"] >= today), key=lambda x: x[0])
    li = "".join(f'<li data-regions="{",".join(it.get("regions", []))}"><span class="cd" data-cd="{d}"></span><span class="tl-when">{E(fdate(d))}</span><div><a href="/radar#rr-{E(it["key"])}">{E(it["title"])}</a><p>{E(w)}</p></div></li>' for d, w, it in ev[:40])
    return f'<ul class="rr-tl rr-home" data-radar-home data-n="{n}">{li}</ul>'


def home_radar():
    today = datetime.date.today().isoformat()
    ev = sorted(((d["date"], d["what"], it) for it in RADAR for d in it.get("dates", []) if d["date"] >= today), key=lambda x: x[0])
    if not ev:
        return ""
    li = "".join(f'<li data-regions="{",".join(it.get("regions", []))}"><span class="cd" data-cd="{d}"></span><span class="tl-when">{E(fdate(d))}</span><div><a href="/radar#rr-{E(it["key"])}">{E(it["title"])}</a><p>{E(w)}</p></div></li>' for d, w, it in ev[:40])
    return f"""<section class="section" style="padding-top:0" id="radar-teaser"><div class="wrap"><div class="section-head"><div><div class="kicker" data-i18n="nav_radar">Regulatory Radar</div><h2 data-i18n="rr_home_h">The next regulatory deadlines</h2></div><a class="btn btn-ink" href="/radar" data-i18n="rr_open">Open the radar →</a></div>
<ul class="rr-tl rr-home" data-radar-home>{li}</ul></div></section>"""


def story_radar(key):
    its = [it for it in RADAR if key in (it.get("stories") or [])]
    if not its:
        return ""
    return '<h3 class="st-sub" id="rules" data-i18n="st_rules">Rules on this storyline</h3><div class="chips-row">' + "".join(f'<a class="schip" href="/radar#rr-{E(it["key"])}">{E(it["title"])}</a>' for it in its) + "</div>"


def write(path, text):
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)


write("index.html", page_home())
write("regions.html", '<!doctype html><meta charset="utf-8"><title>WhyItLands</title><link rel="canonical" href="' + BASE + '/"><script>location.replace("/" + location.hash)</script><meta http-equiv="refresh" content="0; url=/">')
for b in briefings:
    write(f"briefings/{b['slug']}.html", page_briefing(b))
write("briefings/index.html", page_briefings_index())
if doctrines:
    write("doctrines.html", page_doctrines())
if RADAR:
    write("radar.html", page_radar())
if MARKETS:
    write("markets.html", page_markets())
for _c in COMPS:
    write(f"markets/{_c['key']}.html", page_competition(_c))
write("storylines.html", page_storylines())
for _s in STORYDATA["storylines"]:
    write(f"storylines/{_s['key']}.html", page_story(_s))
write("archive.html", page_archive())
for _a in ARCH:
    write(f"archive/{_a['edition']}.html", page_edition(_a))
for _b in ARCH_BRIEFS:
    write(f"archive/briefings/{_b['slug']}-{_b['_ver']}.html", page_briefing_version(_b))
for _nf in (ROOT / "newsletter").glob("20*.html"):
    if _nf.stem > datetime.date.today().isoformat():
        continue
    _t = _nf.read_text().replace("{{ update_profile }}", "/#newsletter").replace("{{ unsubscribe }}", "/#newsletter")
    _t = re.sub(r"\{%[^%]*%\}", "", _t)  # web archive shows every region
    write(f"archive/newsletter/{_nf.stem}.html", _t)
write("glossary.html", page_glossary())
write("method.html", page_method())
write("legal.html", page_legal())
write("404.html", page_404())
out = head("Subscribed · WhyItLands", "Your subscription is confirmed.", "/confirmed") + header()
out += """<main id="main" class="prose" style="text-align:center;padding-bottom:40px"><div class="kicker">Newsletter</div>
<h1 id="cf-h">You are in.</h1>
<p id="cf-p">Your first issue lands on <b id="cf-date">Monday</b> at 07:30, Paris time.</p>
<div class="countdown" id="cf-cd" aria-live="off"><div><b id="cd-d">0</b><span>days</span></div><div><b id="cd-h">0</b><span>hours</span></div><div><b id="cd-m">0</b><span>minutes</span></div><div><b id="cd-s">0</b><span>seconds</span></div></div>
<p style="font-size:15px;color:var(--muted)">One issue a week, every Monday morning. Region and language can be changed from any issue.</p>
<p><a class="btn btn-ink" href="/">Back to the front page</a></p></main>
<script>
(function(){
  if(/error=/.test(location.search)){document.getElementById("cf-h").textContent="This link did not work.";document.getElementById("cf-p").textContent="It may have expired or been used already. Please sign up again from the front page.";document.getElementById("cf-cd").hidden=true;return;}
  function parisOffsetMin(d){var p=new Date(d.toLocaleString("en-US",{timeZone:"Europe/Paris"}));var u=new Date(d.toLocaleString("en-US",{timeZone:"UTC"}));return Math.round((p-u)/60000);}
  function nextIssue(){var now=new Date();for(var i=0;i<8;i++){var d=new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()+i,7,30));var off=parisOffsetMin(d);var t=new Date(d.getTime()-off*60000);var wd=new Date(t.getTime()+off*60000).getUTCDay();if(wd===1&&t>now)return t;}return null;}
  var target=nextIssue();if(!target)return;
  document.getElementById("cf-date").textContent=target.toLocaleDateString(document.documentElement.lang||"en",{weekday:"long",day:"numeric",month:"long",year:"numeric",timeZone:"Europe/Paris"});
  function tick(){var s=Math.max(0,Math.floor((target-new Date())/1000));document.getElementById("cd-d").textContent=Math.floor(s/86400);document.getElementById("cd-h").textContent=Math.floor(s%86400/3600);document.getElementById("cd-m").textContent=Math.floor(s%3600/60);document.getElementById("cd-s").textContent=s%60;}
  tick();setInterval(tick,1000);
})();
</script>"""
write("confirmed.html", out + footer())
urls = ["/", "/storylines", "/briefings/", "/archive", "/markets", "/radar", "/doctrines", "/glossary", "/method", "/legal"] + [f"/briefings/{b['slug']}" for b in briefings] + [f"/storylines/{x['key']}" for x in STORYDATA["storylines"]] + [f"/markets/{c['key']}" for c in COMPS]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{u}</loc></url>" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("built", len(urls), "pages")
