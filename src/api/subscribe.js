// Newsletter signup with double opt-in, handled here (no Brevo template needed).
// POST /api/subscribe: sends a confirmation email with a signed link.
// GET  /api/confirm?t=...: verifies the link and adds the contact to the Brevo list.
// Needs env: BREVO_API_KEY (secret), BREVO_LIST_ID, SENDER_EMAIL.
import { json, clean, isEmail, esc, readBody, sameOrigin, brevo } from './_lib.js';

const REGIONS = ['GLOBAL', 'EMEA', 'EU', 'UK', 'NA', 'SA', 'AS', 'CN', 'ME', 'NAF'];
const LANGS = ['en', 'fr', 'de', 'it', 'es', 'pt'];
const SITE = 'https://www.whyitlands.com';

const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const unb64u = (s) => atob(s.replace(/-/g, '+').replace(/_/g, '/'));

async function hmac(env, data) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode('wil-doi:' + env.BREVO_API_KEY), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return b64u(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(data)));
}

const COPY = {
  en: ['Confirm your WhyItLands subscription', 'One click and you will receive the weekly briefing: where it lands, and why.', 'Confirm my subscription', 'If you did not ask for this, ignore this email and nothing will happen.'],
  fr: ['Confirmez votre inscription à WhyItLands', 'Un clic et vous recevrez le point hebdomadaire : où ça atterrit, et pourquoi.', 'Confirmer mon inscription', 'Si vous n’avez rien demandé, ignorez cet e-mail : il ne se passera rien.'],
  de: ['Bestätigen Sie Ihr WhyItLands-Abo', 'Ein Klick, und Sie erhalten das wöchentliche Briefing: wo es ankommt, und warum.', 'Abo bestätigen', 'Wenn Sie das nicht angefordert haben, ignorieren Sie diese E-Mail.'],
  it: ['Conferma l’iscrizione a WhyItLands', 'Un clic e riceverai il briefing settimanale: dove arriva, e perché.', 'Conferma l’iscrizione', 'Se non l’hai richiesto, ignora questa e-mail.'],
  es: ['Confirma tu suscripción a WhyItLands', 'Un clic y recibirás el análisis semanal: dónde aterriza, y por qué.', 'Confirmar suscripción', 'Si no lo has pedido, ignora este correo.'],
  pt: ['Confirme sua inscrição no WhyItLands', 'Um clique e você receberá o briefing semanal: onde chega, e por quê.', 'Confirmar inscrição', 'Se você não pediu isso, ignore este e-mail.']
};

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request, env)) return json({ ok: false, error: 'forbidden' }, 403);
  let b; try { b = await readBody(request); } catch (e) { return json({ ok: false, error: 'bad_request' }, 400); }
  if (clean(b.hp)) return json({ ok: true });
  const email = clean(b.email, 200).toLowerCase();
  if (!isEmail(email)) return json({ ok: false, error: 'invalid_email' }, 400);
  const region = REGIONS.includes(b.region) ? b.region : 'GLOBAL';
  const lang = LANGS.includes(b.lang) ? b.lang : 'en';
  const missing = ['BREVO_API_KEY', 'BREVO_LIST_ID', 'SENDER_EMAIL'].filter((k) => !env[k]);
  if (missing.length) return json({ ok: false, error: 'missing ' + missing.join(',') }, 503);

  const payload = b64u(new TextEncoder().encode(JSON.stringify({ e: email, r: region, l: lang, x: Date.now() + 7 * 864e5 })));
  const link = `${SITE}/api/confirm?t=${payload}.${await hmac(env, payload)}`;
  const [subject, line, cta, foot] = COPY[lang];
  const html = `<div style="background:#F4F2EC;padding:28px 12px;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;overflow:hidden">
<div style="background:#0B0F1A;padding:22px 26px;color:#F4F2EC;font-size:20px;font-weight:700">WhyItLands<div style="font-family:Georgia,serif;font-style:italic;font-weight:400;font-size:15px;color:#C8CCD6;margin-top:4px">Where it lands, and why.</div></div>
<div style="padding:26px"><p style="font-size:16px;line-height:1.5;color:#0B0F1A;margin:0 0 20px">${esc(line)}</p>
<a href="${link}" style="display:inline-block;background:#FF5A36;color:#fff;font-weight:700;text-decoration:none;padding:12px 22px;border-radius:999px">${esc(cta)}</a>
<p style="font-size:13px;line-height:1.5;color:#5A6072;margin:22px 0 0">${esc(foot)}</p></div></div></div>`;
  try {
    await brevo(env, '/smtp/email', { sender: { name: 'WhyItLands', email: env.SENDER_EMAIL }, to: [{ email }], subject, htmlContent: html });
  } catch (e) { return json({ ok: false, error: 'subscribe_failed_' + e.message, detail: String(e.detail || '').slice(0, 200) }, 502); }
  return json({ ok: true });
}

export async function onRequestGet({ request, env }) {
  const t = new URL(request.url).searchParams.get('t') || '';
  const [payload, sig] = t.split('.');
  const fail = (why) => Response.redirect(`${SITE}/confirmed?error=${why}`, 302);
  if (!payload || !sig || !env.BREVO_API_KEY || !env.BREVO_LIST_ID) return fail('link');
  if ((await hmac(env, payload)) !== sig) return fail('link');
  let d; try { d = JSON.parse(unb64u(payload)); } catch (e) { return fail('link'); }
  if (!d || !isEmail(d.e) || Date.now() > d.x) return fail('expired');
  const base = { email: d.e, listIds: [Number(env.BREVO_LIST_ID)], updateEnabled: true };
  try {
    await brevo(env, '/contacts', { ...base, attributes: { REGION: d.r, LANGUAGE: d.l } });
  } catch (e) {
    try { await brevo(env, '/contacts', base); } catch (e2) { return fail('save'); }
  }
  return Response.redirect(`${SITE}/confirmed`, 302);
}
