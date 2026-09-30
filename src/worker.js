// WhyItLands Worker: serves the static site from ./site and handles the form APIs.
import * as contact from './api/contact.js';
import * as subscribe from './api/subscribe.js';
import { json } from './api/_lib.js';

const ROUTES = { '/api/contact': contact, '/api/subscribe': subscribe, '/api/confirm': subscribe };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.hostname === 'whyitlands.com') {
      url.hostname = 'www.whyitlands.com';
      return Response.redirect(url.toString(), 301);
    }
    const route = ROUTES[url.pathname];
    if (route) {
      if (request.method === 'POST' && url.pathname !== '/api/confirm') return route.onRequestPost({ request, env, ctx });
      if (request.method === 'GET' && url.pathname === '/api/confirm') return route.onRequestGet({ request, env, ctx });
      return json({ ok: false, error: 'method_not_allowed' }, 405);
    }
    if (url.pathname.startsWith('/api/')) return json({ ok: false, error: 'not_found' }, 404);
    return env.ASSETS.fetch(request);
  }
};
