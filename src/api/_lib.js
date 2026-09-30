// Shared helpers for Cloudflare Pages Functions.
export const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });

export const clean = (v, max = 2000) => String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max);

export const isEmail = (v) => /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}$/.test(v) && v.length <= 200;

export const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export async function readBody(request) {
  if (Number(request.headers.get('content-length') || 0) > 20000) throw new Error('too_large');
  return await request.json();
}

// Same-origin check: only accept posts coming from the site itself.
export function sameOrigin(request, env) {
  const origin = request.headers.get('Origin') || '';
  if (!origin) return true;
  const host = new URL(request.url).host;
  const allowed = [host, 'whyitlands.com', 'www.whyitlands.com'].concat((env.EXTRA_ORIGINS || '').split(',').filter(Boolean));
  try { return allowed.includes(new URL(origin).host) || new URL(origin).host.endsWith('.pages.dev') || new URL(origin).host.endsWith('.workers.dev'); } catch (e) { return false; }
}

export async function brevo(env, path, payload) {
  const r = await fetch('https://api.brevo.com/v3' + path, {
    method: 'POST',
    headers: { 'api-key': env.BREVO_API_KEY, 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!r.ok && r.status !== 204) {
    const t = await r.text();
    const err = new Error('brevo_' + r.status); err.detail = t; throw err;
  }
  return r;
}
