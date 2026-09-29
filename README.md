# WhyItLands

Where it lands, and why. Geopolitics connected, factually and with sources, to e-commerce logistics, domestic and cross-border.

https://whyitlands.com

## How the repo is organised

| Path | What it is |
|---|---|
| `content/` | All editorial content as JSON: home page, regional desks, briefings, glossary, settings. **Edit here.** |
| `tools/build.py` | Turns `content/` into static pages in `site/`. Standard-library Python only. |
| `site/` | The published website (what Cloudflare Pages serves). Generated pages are committed. |
| `site/assets/js/i18n.js` | Interface text in EN (default), FR, DE, IT, ES, PT. |
| `site/assets/js/config.js` | Public settings, including the PostHog key for analytics. |
| `functions/api/` | Cloudflare Pages Functions: contact form, reader feedback, newsletter signup. |

After any content change: `python3 tools/build.py`, then commit.

## Cloudflare Pages settings

- Framework preset: **None**
- Build command: *(leave empty)*
- Build output directory: **site**
- Custom domain: whyitlands.com

## Environment variables (Cloudflare Pages → Settings → Variables and secrets)

| Name | Used for |
|---|---|
| `BREVO_API_KEY` (secret) | Sending contact/feedback emails and newsletter double opt-in |
| `CONTACT_TO` | Inbox that receives contact and feedback messages |
| `SENDER_EMAIL` | Sender verified in Brevo (for example hello@whyitlands.com) |
| `BREVO_LIST_ID` | Newsletter list ID in Brevo |
| `BREVO_DOI_TEMPLATE_ID` | Brevo double opt-in confirmation template ID |

Until these are set, the forms answer with a polite error and nothing is sent.

## Analytics

PostHog (EU region), cookieless (`persistence: memory`), no session recording. Paste the project key in `site/assets/js/config.js`.
Tracked events: `region_selected`, `language_selected`, `calendar_filtered`, `audio_played`, `audio_completed`, `acronym_opened`, `source_opened`, `scroll_depth`, `newsletter_signup`, `contact_opened`, `contact_sent`, `feedback_sent`.

## Editorial rules

- Every fact has a source. No invented quotes.
- Videos are embedded only from identified channels, after checking (`content/regions.json` → `videos`: `{id, title, channel, start}`).
- Nothing confidential from any employer. AI assistance is disclosed on every page.
