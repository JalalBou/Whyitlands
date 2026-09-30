# WhyItLands

Where it lands, and why. Geopolitics connected, factually and with sources, to e-commerce logistics, domestic and cross-border.

https://www.whyitlands.com

## How the repo is organised

| Path | What it is |
|---|---|
| `content/` | All editorial content as JSON: home page, regional desks, briefings, glossary, settings. **Edit here.** |
| `tools/build.py` | Turns `content/` into static pages in `site/`. Standard-library Python only. |
| `site/` | The published website (what Cloudflare Pages serves). Generated pages are committed. |
| `site/assets/js/i18n.js` | Interface text in EN (default), FR, DE, IT, ES, PT. |
| `site/assets/js/config.js` | Public settings, including the PostHog key for analytics. |
| `src/` | Cloudflare Worker: serves `site/` and handles the contact, feedback and newsletter APIs (`src/api/`). |
| `wrangler.jsonc` | Worker configuration (name `whyitlands`, static assets from `site/`). |

After any content change: `python3 tools/build.py`, then commit.

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

## Editorial rules

- Solution providers (compliance, landed cost, customs data, brokerage): whenever one is named, name at least three for the same need, in alphabetical order, neutrally, with sources. Landscape lives in `content/solutions.json`. Never mention Asendia.

- Every fact has a source. No invented quotes.
- Videos are embedded only from identified channels, after checking (`content/regions.json` → `videos`: `{id, title, channel, start}`).
- Nothing confidential from any employer. AI assistance is disclosed on every page.
