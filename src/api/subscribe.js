// POST /api/subscribe: newsletter signup with double opt-in (Brevo).
// Needs env: BREVO_API_KEY, BREVO_LIST_ID, BREVO_DOI_TEMPLATE_ID.
import { json, clean, isEmail, readBody, sameOrigin, brevo } from './_lib.js';

const REGIONS = ['GLOBAL', 'EMEA', 'EU', 'UK', 'NA', 'SA', 'AS', 'CN', 'ME', 'NAF'];
const LANGS = ['en', 'fr', 'de', 'it', 'es', 'pt'];

export async function onRequestPost({ request, env }) {
  if (!sameOrigin(request, env)) return json({ ok: false, error: 'forbidden' }, 403);
  let b; try { b = await readBody(request); } catch (e) { return json({ ok: false, error: 'bad_request' }, 400); }
  if (clean(b.hp)) return json({ ok: true });
  const email = clean(b.email, 200).toLowerCase();
  if (!isEmail(email)) return json({ ok: false, error: 'invalid_email' }, 400);
  const region = REGIONS.includes(b.region) ? b.region : 'GLOBAL';
  const lang = LANGS.includes(b.lang) ? b.lang : 'en';
  if (!env.BREVO_API_KEY || !env.BREVO_LIST_ID || !env.BREVO_DOI_TEMPLATE_ID) return json({ ok: false, error: 'not_configured' }, 503);
  const site = new URL(request.url).origin;
  try {
    await brevo(env, '/contacts/doubleOptinConfirmation', {
      email,
      includeListIds: [Number(env.BREVO_LIST_ID)],
      templateId: Number(env.BREVO_DOI_TEMPLATE_ID),
      redirectionUrl: site + '/confirmed',
      attributes: { REGION: region, LANGUAGE: lang }
    });
  } catch (e) { return json({ ok: false, error: 'subscribe_failed' }, 502); }
  return json({ ok: true });
}

export const onRequest = () => json({ ok: false, error: 'method_not_allowed' }, 405);
