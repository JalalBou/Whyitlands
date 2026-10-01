# WhyItLands

Where it lands, and why. Geopolitics connected, factually and with sources, to e-commerce logistics, domestic and cross-border.

https://www.whyitlands.com

## How the repo is organised

| Path | What it is |
|---|---|
| `content/` | All editorial content as JSON: home page, regional desks, briefings, glossary, settings. **Edit here.** |
| `tools/build.py` | Turns `content/` into static pages in `site/`. Standard-library Python only. |
| `site/` | The published website (what Cloudflare Pages serves). Generated pages are committed. |
| `site/assets/js/i18n.js` | Interface text. The site is English only (no language switch); other languages in this file are unused. |
| `site/assets/js/config.js` | Public settings, including the PostHog key for analytics. |
| `src/` | Cloudflare Worker: serves `site/` and handles the contact, feedback and newsletter APIs (`src/api/`). |
| `wrangler.jsonc` | Worker configuration (name `whyitlands`, static assets from `site/`). |

After any content change: `python3 tools/build.py`, then commit.

Archive: before each weekly update run `python3 tools/archive.py` (snapshots the edition to `content/archive/<date>.json`, shown at /archive). Before materially rewriting a briefing run `python3 tools/archive.py briefing <slug>` and set `"updated"` in the briefing; new topics get a new briefing file rather than overwriting an old one.

Audio: `.github/workflows/audio.yml` regenerates the neural-voice audio of any new or changed briefing on GitHub Actions (`tools/tts.py`).

## Cloudflare settings (Worker `whyitlands`)

- Deploy command: `npx wrangler deploy` (reads `wrangler.jsonc`)
- No build command: pages in `site/` are committed after `python3 tools/build.py`
- Custom domain: whyitlands.com

## Environment variables (Worker → Settings → Variables and secrets)

| Name | Used for |
|---|---|
| `BREVO_API_KEY` (secret) | Sending contact/feedback emails and newsletter double opt-in |
| `CONTACT_TO` | Inbox that receives contact and feedback messages |
| `SENDER_EMAIL` | Sender verified in Brevo (for example hello@whyitlands.com) |
| `BREVO_LIST_ID` | Newsletter list ID in Brevo |

Until these are set, the forms answer with a polite error and nothing is sent.

## Analytics

PostHog (EU region), cookieless (`persistence: memory`), no session recording. Paste the project key in `site/assets/js/config.js`.
Tracked events: `region_selected`, `language_selected`, `calendar_filtered`, `audio_played`, `audio_completed`, `acronym_opened`, `source_opened`, `scroll_depth`, `newsletter_signup`, `contact_opened`, `contact_sent`, `feedback_sent`.

## The golden thread

Every item is linked to a storyline (`content/storylines.json`, 11 storylines) and to a layer of the causal model: geopolitics → decision & law → market → parcel impact. Tag new items with `"stories": [...]` and `"layer"` (wire, deals, calendar, companies, solution topics, briefings). The parcel barometer (`content/barometer.json`) is our weekly reading of pressure on cost, speed, volume, compliance and network per region.

## Intelligence layer (Market Intelligence)

Lives in `content/intel/`:
- `signals.json`: syntheses. Each signal needs at least three dated, sourced facts from different players (`evidence`), an `inference` (our reading), `confidence` (low/medium/high), `status` (emerging/confirmed/faded), `confirm`, `refute`, `monitor`, `regions`, `stories`. A signal goes live only with three independent facts. Faded signals stay in the file: they are the track record.
- `watch.json`: price and service watch (fuel surcharges, peak fees, rate increases, regulated tariffs, service changes) as published, with effective date and source.
- `moves.json`: dated capacity, network, M&A, partnership, closure, pricing and product moves, newest first.
- `competition/<key>.json`: competition deep dives (US, ASEAN) rendered at `/markets/<key>`: stats, scorecard, battlegrounds, segments or countries, price stack, players, scenarios, implications, watch, sources (cited by index; append only).

Signals about competitors rest on public sources only, cover players evenly, and never use anything known from the author's employment.

## Regulatory Radar (/radar)

`content/radar/*.json` (europe, americas, asia-mena-global), one `{"items": [...]}` per file, schema in `content/radar/SCHEMA.md`. Each rule has a status (consultation, proposed, adopted, in-force, suspended), dated milestones with a source each, who it hits, the parcel impact, what to prepare, our reading and storylines. The page shows an 18-month agenda with countdowns and the full register, filtered by region and topic; the home page shows the next deadlines; storyline pages link the rules on that storyline. Information, not legal advice. Each rule date links automatically to every briefing, storyline, signal, calendar item or deep dive that mentions the same date about the same rule (tools/thread.py: same date, same jurisdiction, shared rule keywords); briefings show the rules they mention. Nothing to tag by hand: keep dates in ISO form in content and in plain words ("1 November 2026") in text.

## Newsletter regions

Subscribers pick one or more regions. Brevo stores REGIONS as ",EU,UK," (plus REGION = first pick). tools/newsletter.py wraps each region block in Brevo conditions, so each subscriber sees their regions; contacts with no REGIONS or GLOBAL see everything. Set "personalise": false in content/newsletter.json to send identical content.

## Editorial rules

- Solution providers (compliance, landed cost, customs data, brokerage): whenever one is named, name at least three for the same need, in alphabetical order, neutrally, with sources. Landscape lives in `content/solutions.json`. Never mention Asendia.

- Every fact has a source. No invented quotes.
- Videos are embedded only from identified channels, after checking (`content/regions.json` → `videos`: `{id, title, channel, start}`).
- Nothing confidential from any employer. AI assistance is disclosed on every page.
