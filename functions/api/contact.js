// POST /api/contact — contact form and anonymous feedback, forwarded by email to the publisher.
// Needs env: BREVO_API_KEY, CONTACT_TO, SENDER_EMAIL (a sender verified in Brevo).
import { json, clean, isEmail, esc, readBody, sameOrigin, brevo } from './_lib.js';

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request, env)) return json({ ok: false, error: 'forbidden' }, 403);
  let b; try { b = await readBody(request); } catch (e) { return json({ ok: false, error: 'bad_request' }, 400); }
  if (clean(b.hp)) return json({ ok: true }); // honeypot: pretend success
  const kind = b.kind === 'feedback' ? 'feedback' : 'contact';
  const message = clean(b.message, 5000);
  if (message.length < 3) return json({ ok: false, error: 'empty' }, 400);
  const email = clean(b.email, 200);
  if (kind === 'contact') {
    if (!isEmail(email) || !clean(b.name) || b.consent !== true) return json({ ok: false, error: 'invalid' }, 400);
  }
  if (!env.BREVO_API_KEY || !env.CONTACT_TO || !env.SENDER_EMAIL) return json({ ok: false, error: 'not_configured' }, 503);

  const rows = kind === 'contact'
    ? [['Topic', clean(b.topic, 60)], ['Name', clean(b.name, 120)], ['Email', email], ['Company and role', clean(b.org, 160)], ['Language', clean(b.lang, 5)]]
    : [['From', clean(b.from, 200) || 'Anonymous'], ['Page', clean(b.page, 200)], ['Language', clean(b.lang, 5)]];
  const table = rows.map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#5A6072">${k}</td><td>${esc(v || '—')}</td></tr>`).join('');
  const subject = kind === 'contact' ? `[WhyItLands] ${clean(b.topic, 60) || 'Contact'} from ${clean(b.name, 80)}` : '[WhyItLands] Reader feedback';
  const payload = {
    sender: { name: 'WhyItLands', email: env.SENDER_EMAIL },
    to: [{ email: env.CONTACT_TO }],
    subject,
    htmlContent: `<div style="font-family:system-ui,sans-serif;font-size:15px"><table>${table}</table><p style="white-space:pre-wrap;border-top:1px solid #ddd;padding-top:12px">${esc(message)}</p></div>`
  };
  if (kind === 'contact') payload.replyTo = { email, name: clean(b.name, 120) };
  const fromMail = clean(b.from, 200);
  if (kind === 'feedback' && isEmail(fromMail)) payload.replyTo = { email: fromMail };
  try { await brevo(env, '/smtp/email', payload); } catch (e) { return json({ ok: false, error: 'send_failed' }, 502); }
  return json({ ok: true });
}

export const onRequest = () => json({ ok: false, error: 'method_not_allowed' }, 405);
