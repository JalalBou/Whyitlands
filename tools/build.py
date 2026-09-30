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
_dp = C / "doctrines.json"
doctrines = json.loads(_dp.read_text()) if _dp.exists() else None

REGION_ORDER = ["GLOBAL", "EMEA", "EU", "UK", "NA", "SA", "AS", "CN", "ME", "NAF"]
DESK_ORDER = ["EU", "UK", "NA", "SA", "AS", "CN", "ME", "NAF"]
RNAME = {"GLOBAL": "Global", "EMEA": "EMEA", "EU": "EU", "UK": "UK", "NA": "North America", "SA": "South America",
         "AS": "Asia", "CN": "China", "ME": "Middle East", "NAF": "North Africa"}
LANGS = [("en", "English"), ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("es", "Español"), ("pt", "Português")]

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
<a class="brand" href="/" aria-label="WhyItLands, home">WhyItLands{PARCEL}</a>
<span class="tagline">Where it lands, and why.</span>
<nav class="head-nav" aria-label="Main">
{nav('/regions', 'nav_regions', 'Regions', 'regions')}
{nav('/briefings/', 'nav_briefings', 'Briefings', 'briefings')}
{nav('/doctrines', 'nav_doctrines', 'Doctrines', 'doctrines')}
{nav('/#about', 'nav_about', 'About', 'about')}
<div class="lang"><button class="lang-btn" aria-haspopup="true" aria-expanded="false" aria-label="Language"><span class="lang-code">EN</span><svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></button>
<ul class="lang-menu" role="menu" hidden>{langs}</ul></div>
<a class="btn btn-coral head-sub" href="/#newsletter" data-i18n="subscribe">Subscribe</a>
</nav>
</div>
</header>
"""


def regionbar(keys, default):
    chips = "".join(f'<button class="chip" data-region="{k}" aria-pressed="{str(k==default).lower()}" data-region-label="{k}">{RNAME[k]}</button>' for k in keys)
    return f"""<div class="regionbar" id="regionbar"><div class="wrap">{i('your_region', 'Your region', 'span', 'kicker')}
<div class="chips" role="group" aria-label="Region">{chips}</div></div></div>
"""


def contact_dialog():
    topics = "".join(f'<button type="button" class="chip" data-topic-i="{n}" aria-pressed="{str(n==0).lower()}">{t}</button>' for n, t in enumerate(["Collaboration", "Speaking", "Press", "Tip or correction", "Other"]))
    return f"""<dialog class="modal" id="contact" aria-labelledby="ct-title">
<div class="modal-in">
<div class="modal-top"><div class="who"><img src="/assets/img/jalal.jpg" alt="" width="56" height="56">
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
<nav aria-label="Footer"><a href="/method" data-i18n="method">Method</a><a href="/glossary" data-i18n="glossary">Glossary</a><a href="/legal" data-i18n="legal">Legal & privacy</a>{f'<a href="{LINKEDIN}" rel="noopener">LinkedIn</a>' if LINKEDIN else ""}<a href="#" data-contact="footer" data-i18n="get_in_touch">Get in touch</a></nav></div>
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
    return f'<script type="application/json" id="coming-data">{data}</script>\n'


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


def page_home():
    h = home["hero"]; b = next(x for x in briefings if x["slug"] == h["briefing"])
    chain = "".join(f'<li><span class="n">{n}</span><div><b>{E(c["k"].upper())}</b><span>{E(c["t"])}</span></div></li>' for n, c in enumerate(home["chain"], 1))
    tiles = []
    for w in home["wire"]:
        inner = f'<span class="tag">{E(w["tag"])}</span>'
        if w.get("big"): inner += f'<span class="big">{E(w["big"])}</span>'
        if w.get("lede"): inner += f'<p class="lede">{E(w["lede"])}</p>'
        if w.get("text"): inner += f'<p>{E(w["text"])}</p>'
        inner += f'<span class="src">{src_link(w["src"], w.get("url"))}</span>'
        tiles.append(f'<article class="tile {w["style"]}" data-regions="{",".join(w.get("regions", []))}">{inner}</article>')
    whys = "".join(f"""<article class="why"><span class="kicker">{E(w['region'])}</span><h3>{E(w['title'])}</h3>
<dl><div><dt data-i18n="what_happened">What happened</dt><dd>{E(w['what'])}</dd></div><div><dt data-i18n="why">Why</dt><dd>{E(w['why'])}</dd></div><div><dt data-i18n="what_means">What it means</dt><dd>{E(w['means'])}</dd></div></dl></article>""" for w in home["why"])
    deals = "".join(f'<tr><td class="date">{E(d["date"])}</td><td class="co">{E(d["co"])}</td><td>{E(d["deal"])}</td><td><span class="pill">{E(d["region"])}</span></td><td>{src_link(d["src"], d.get("url"))}</td></tr>' for d in home["deals"])
    srcs = "".join(f'<div class="src-card"><div class="kicker">{E(s["k"])}</div><p>' + " · ".join(E(n) + (f'<span class="lng">{l}</span>' if l else "") for n, l in s["items"]) + "</p></div>" for s in home["sources"])
    mins = b.get("minutes") or 4
    out = head("WhyItLands · Where it lands, and why", "Geopolitics connected, factually and with sources, to e-commerce logistics, domestic and cross-border. A clear information grid for senior leaders: what is happening, what is coming, and why.", "/")
    out += header() + regionbar(REGION_ORDER, "GLOBAL")
    out += f"""<main id="main">
<section class="hero">{ARCS}
<div class="wrap hero-grid">
<div><span class="kicker">{E(h['kicker'])}</span>
<h1>{E(h['title'])}<br><em>{E(h['title_em'])}</em></h1>
<p class="dek">{E(h['dek'])}</p>
<div class="hero-cta"><a class="btn btn-coral" href="/briefings/{b['slug']}"><span data-i18n="read_briefing">Read the briefing</span></a>
{listen_btn(b)}<a class="btn btn-ghost-dark" href="/briefings/"><span data-i18n="all_briefings">All briefings</span></a></div></div>
<aside class="chain" aria-label="Why it lands here"><span class="kicker" data-i18n="why_lands_here">Why it lands here</span><ol>{chain}</ol></aside>
</div></section>

<section class="section"><div class="wrap">
<div class="section-head"><div>{i('briefings_kicker', 'Briefings', 'div', 'kicker')}{i('briefings_title', 'The analysis, region by region', 'h2')}</div><a class="more" href="/briefings/" data-i18n="all_briefings_arrow">All briefings →</a></div>
<div class="bgrid">{''.join(bcard(x, n == 0) for n, x in enumerate(briefings[:7]))}</div>
</div></section>

<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('wire_kicker', 'Industry wire', 'div', 'kicker')}{i('wire_title', 'What moved this week', 'h2')}</div></div>
<div class="bento">{''.join(tiles)}</div>
</div></section>

<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('why_kicker', 'The why', 'div', 'kicker')}{i('why_title', 'From geopolitics to the parcel', 'h2')}</div></div>
<div class="why-grid">{whys}</div>
</div></section>

<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('deals_kicker', 'Deals & investments', 'div', 'kicker')}{i('deals_title', 'The deal tracker', 'h2')}</div></div>
<div class="table-wrap"><table><thead><tr><th data-i18n="th_date">Date</th><th data-i18n="th_company">Company</th><th data-i18n="th_deal">Deal</th><th data-i18n="th_region">Region</th><th data-i18n="th_source">Source</th></tr></thead><tbody>{deals}</tbody></table></div>
</div></section>

<section class="section" style="padding-top:0" id="coming"><div class="wrap">
<div class="section-head"><div><div class="kicker"><span data-i18n="cal_kicker">Calendar</span> · <span data-current-region>GLOBAL</span></div>{i('coming_title', 'What’s coming', 'h2')}</div><a class="more" href="/regions" data-i18n="regional_link">Regional calendars and expos →</a></div>
{filters()}
<div class="timeline" data-timeline="home" data-limit="6" aria-live="polite"></div>
</div></section>

<section class="section" style="padding-top:0"><div class="wrap">
<div class="section-head"><div>{i('sources_kicker', 'Sources', 'div', 'kicker')}{i('sources_title', 'Close to the ground, in the local language', 'h2')}<p style="margin-top:14px;color:var(--muted-2);max-width:680px" data-i18n="sources_dek">Institutions, trade press and niche regional media, read in their original language. Every fact links to its source.</p></div></div>
<div class="src-grid">{srcs}</div>
</div></section>

<section class="section" style="padding-top:0" id="about"><div class="wrap">
<div class="about">
<div class="portrait"><img src="/assets/img/jalal.jpg" alt="Jalal Boucheikha" width="220" height="220" loading="lazy"></div>
<div>{i('about_kicker', 'About', 'div', 'kicker')}<h2>Jalal Boucheikha</h2>{i('role', 'Shipping Product Director at Asendia', 'div', 'role')}
<p data-i18n="about_1">Engineer by training, I work where operations, commercial, compliance and strategy meet: the product side of how cross-border parcels are processed, cleared, routed and tracked.</p>
<p data-i18n="about_2">My day-to-day is multicultural and multi-regional, with teams and partners across several continents, and a practice of agile at scale inside a large organisation.</p>
<p data-i18n="about_3">I started WhyItLands to explain the why behind the decisions reshaping e-commerce logistics, domestic and cross-border, in a form that is quick to read and easy to check.</p>
<blockquote>“Complexity should be invisible. What you expose to your merchants, your partners, your customers should be simple, reliable and programmable.”</blockquote>
<div class="cta">{f'<a class="btn btn-light" href="{LINKEDIN}" rel="noopener">LinkedIn</a>' if LINKEDIN else ""}<a class="btn btn-ghost-dark" href="#" data-contact="about" data-i18n="get_in_touch">Get in touch</a></div>
<p style="font-size:13px;margin-top:22px;color:#8C93A6" data-i18n="about_note">WhyItLands is a personal project. Views are my own and do not represent my employer.</p>
</div></div>
</div></section>

<section class="section" style="padding-top:0" id="newsletter"><div class="wrap nl">
<div class="nl-card"><h2><span data-i18n="nl_title1">Every week:</span><br><span data-i18n="nl_title2">where it lands, and why.</span></h2>
<p data-i18n="nl_dek">The week’s geopolitical shifts, deals and reforms for your region, in seven minutes. Free, one-click unsubscribe.</p>
<form id="nl-form" class="field-row" novalidate="false">
<label class="sr-only" for="nl-email" data-i18n="work_email">Work email</label>
<input class="input" id="nl-email" name="email" type="email" autocomplete="email" required data-i18n-ph="work_email" placeholder="Work email">
<select class="input" name="region" aria-label="Region">{''.join(f'<option value="{k}" data-region-label="{k}">{RNAME[k]}</option>' for k in REGION_ORDER)}</select>
<input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="btn btn-ink" type="submit" data-i18n="sign_up">Sign up</button>
</form>
<div class="status" id="nl-status" hidden role="status" style="margin-top:12px"></div>
<p class="fine" data-i18n="nl_fine">We send a confirmation email first. Region and language can be changed in every issue.</p></div>
{feedback_card()}
</div></section>
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
    out += '<main id="main">' + "".join(desks) + f"""
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
    return (f'<a class="bcard{" big" if big else ""}" href="/briefings/{b["slug"]}" data-regions="{regs}">'
            f'<span class="kicker">{E(b["section"])}</span><h3>{E(b["title"])}</h3><p>{E(plain(b["dek"]))}</p>'
            f'<span class="bmeta">{E(b["date_label"])} · {reading_minutes(b)} <span data-i18n="min_read">min read</span></span></a>')


def desk_briefings(k):
    mine = [b for b in briefings if b.get("region") == k] + [b for b in briefings if b.get("region") != k and k in b.get("regions", [])]
    if not mine:
        return ""
    return f"""<section class="section" style="padding-bottom:0"><div class="wrap">
<div class="section-head"><div>{i('briefings_kicker', 'Briefings', 'div', 'kicker')}{i('desk_analysis', 'The analysis for this region', 'h2')}</div></div>
<div class="bgrid">{''.join(bcard(b, n == 0 and b.get('region') == k) for n, b in enumerate(mine[:4]))}</div>
</div></section>"""


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
            toc.append(("csuite", "For the C-suite"))
            body.append(f'<section class="csuite" id="csuite"><div class="kicker" data-i18n="csuite_kicker">Decisions</div><h2 data-i18n="csuite">For the C-suite</h2><ol>{rows}</ol></section>')
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
<div class="art">
<div class="keypoints">{i('key_points', 'Key points', 'div', 'kicker')}<ul>{kp}</ul>
<div class="kp-links"><a class="btn btn-coral" href="#csuite" style="height:40px;font-size:14px" data-i18n="jump_csuite">Jump to the C-suite actions</a></div></div>
{lang_note()}
<nav class="toc" aria-label="In this briefing"><span class="kicker" data-i18n="in_this_briefing">In this briefing</span>{tocs}</nav>
<span id="listen"></span>{audio}
<div class="art-body" style="margin-top:28px">{''.join(body)}</div>
<section class="gloss" aria-labelledby="gl-h"><h2 id="gl-h" style="font-size:28px" data-i18n="acronyms">Acronyms in this article</h2><dl>{gl}</dl>
<p style="margin-top:16px;font-size:15px"><a href="#" data-back data-i18n="back_text">↩ Back to the text</a> · <a href="/glossary" data-i18n="full_glossary">Full glossary →</a></p></section>
<section class="sources-list"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section>
<p class="method-note" data-i18n="method_note">Facts are sourced; analysis, scenarios and recommendations are WhyItLands’ own reading. AI-assisted research, reviewed by Jalal Boucheikha.</p>
<div style="margin-top:40px">{feedback_card()}</div>
</div>
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
<section class="section"><div class="wrap"><div class="bgrid" data-filter-regions>{''.join(bcard(b) for b in briefings)}</div></div></section>
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
<section class="section"><div class="wrap"><div class="chips chips-light doc-toc">{toc}</div><div class="schools">{''.join(cards)}</div>
<section class="sources-list" style="max-width:760px"><h2 style="font-size:28px" data-i18n="sources_art">Sources</h2><ol>{srcs}</ol></section></div></section>
</main>
"""
    return out + footer()


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


def write(path, text):
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)


write("index.html", page_home())
write("regions.html", page_regions())
for b in briefings:
    write(f"briefings/{b['slug']}.html", page_briefing(b))
write("briefings/index.html", page_briefings_index())
if doctrines:
    write("doctrines.html", page_doctrines())
write("glossary.html", page_glossary())
write("method.html", page_method())
write("legal.html", page_legal())
write("404.html", page_404())
out = head("Subscribed · WhyItLands", "Your subscription is confirmed.", "/confirmed") + header()
out += '<main id="main" class="prose" style="text-align:center;padding-bottom:40px"><div class="kicker">Newsletter</div><h1>You are in. First issue lands this week.</h1><p>Thank you for confirming. You can change region and language from any issue.</p><p><a class="btn btn-ink" href="/">Back to the front page</a></p></main>'
write("confirmed.html", out + footer())
urls = ["/", "/briefings/", "/regions", "/doctrines", "/glossary", "/method", "/legal"] + [f"/briefings/{b['slug']}" for b in briefings]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{u}</loc></url>" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("built", len(urls), "pages")
