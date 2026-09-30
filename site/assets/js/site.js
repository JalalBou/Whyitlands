/* WhyItLands — front-end behaviour. No cookies; preferences stay in this browser. */
(function () {
  'use strict';
  var CFG = window.WIL_CONFIG || {};
  var I18N = window.WIL_I18N || {};
  var LANGS = ['en', 'fr'];
  var EMEA = ['EU', 'UK', 'ME', 'NAF'];
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ---------- Analytics (PostHog EU, cookieless, only if a key is configured) ---------- */
  var queue = [];
  function track(ev, props) {
    props = props || {};
    props.lang = state.lang; props.region = state.region;
    if (window.posthog && window.posthog.capture) window.posthog.capture(ev, props); else queue.push([ev, props]);
  }
  if (CFG.posthogKey) {
    var s = document.createElement('script');
    s.async = true; s.src = (CFG.posthogAssets || 'https://eu-assets.i.posthog.com') + '/static/array.js';
    s.onload = function () {
      if (!window.posthog) return;
      window.posthog.init(CFG.posthogKey, { api_host: CFG.posthogHost || 'https://eu.i.posthog.com', persistence: 'memory', disable_session_recording: true, autocapture: true, capture_pageview: true, person_profiles: 'identified_only' });
      queue.forEach(function (q) { window.posthog.capture(q[0], q[1]); }); queue = [];
    };
    document.head.appendChild(s);
  }
  window.WIL_track = track;

  /* ---------- State ---------- */
  var urlLang = (location.search.match(/[?&]lang=([a-z]{2})/) || [])[1];
  var state = {
    lang: LANGS.indexOf(urlLang) > -1 ? urlLang : (LANGS.indexOf(store('wil-lang')) > -1 ? store('wil-lang') : 'en'),
    region: store('wil-region') || 'GLOBAL',
    type: 'All'
  };
  function t(k) { var d = I18N[state.lang] || I18N.en || {}; return d[k] !== undefined ? d[k] : ((I18N.en || {})[k] || ''); }

  /* ---------- Language ---------- */
  function applyLang() {
    document.documentElement.lang = state.lang;
    $$('[data-i18n]').forEach(function (el) { var v = t(el.getAttribute('data-i18n')); if (v) el.textContent = v; });
    $$('[data-i18n-ph]').forEach(function (el) { var v = t(el.getAttribute('data-i18n-ph')); if (v) el.setAttribute('placeholder', v); });
    $$('[data-i18n-aria]').forEach(function (el) { var v = t(el.getAttribute('data-i18n-aria')); if (v) el.setAttribute('aria-label', v); });
    $$('[data-region-label]').forEach(function (el) { var R = t('R') || {}; el.textContent = R[el.getAttribute('data-region-label')] || el.textContent; });
    $$('.lang-code').forEach(function (el) { el.textContent = state.lang.toUpperCase(); });
    $$('.lang-menu [role=menuitemradio]').forEach(function (b) { b.setAttribute('aria-checked', String(b.getAttribute('data-lang') === state.lang)); });
    $$('.lang-note').forEach(function (el) { el.hidden = state.lang === 'en'; });
    var topics = t('ct_topics');
    $$('[data-topic-i]').forEach(function (b) { var i = +b.getAttribute('data-topic-i'); if (topics && topics[i]) b.textContent = topics[i]; });
    renderComing();
  }
  function initLang() {
    $$('.lang').forEach(function (wrap) {
      var btn = $('.lang-btn', wrap), menu = $('.lang-menu', wrap);
      btn.addEventListener('click', function (e) { e.stopPropagation(); var open = menu.hidden; menu.hidden = !open; btn.setAttribute('aria-expanded', String(open)); if (open) { var cur = $('[aria-checked=true]', menu); (cur || $('button', menu)).focus(); } });
      $$('button', menu).forEach(function (b) {
        b.addEventListener('click', function () { state.lang = b.getAttribute('data-lang'); store('wil-lang', state.lang); menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); applyLang(); track('language_selected', {}); btn.focus(); });
      });
      menu.addEventListener('keydown', function (e) {
        var items = $$('button', menu), i = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
        if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
        if (e.key === 'Escape') { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
      });
    });
    document.addEventListener('click', function () { $$('.lang-menu').forEach(function (m) { m.hidden = true; }); $$('.lang-btn').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); }); });
  }

  /* ---------- Region ---------- */
  function inRegion(list) {
    if (state.region === 'GLOBAL') return true;
    if (!list || !list.length) return false;
    if (list.indexOf(state.region) > -1) return true;
    if (state.region === 'EMEA') return list.some(function (r) { return EMEA.indexOf(r) > -1 || r === 'EMEA'; });
    return false;
  }
  function applyRegion() {
    $$('#regionbar .chip').forEach(function (c) { c.setAttribute('aria-pressed', String(c.getAttribute('data-region') === state.region)); });
    // Filtered lists: keep the region's items; if nothing matches, show everything.
    function filterSet(els) {
      if (!els.length) return;
      var match = els.filter(function (el) { return inRegion((el.getAttribute('data-regions') || '').split(',')); });
      els.forEach(function (el) { el.hidden = match.length > 0 && match.indexOf(el) === -1; });
    }
    filterSet($$('.bento .tile[data-regions]'));
    filterSet($$('[data-filter-topics] > .topic[data-regions]'));
    filterSet($$('[data-filter-rows] tr[data-regions]'));
    $$('[data-filter-regions] .bcard').forEach(function (el) {
      var rs = (el.getAttribute('data-regions') || '').split(',');
      el.hidden = !(inRegion(rs) || rs.indexOf('GLOBAL') > -1);
      var own = el.getAttribute('data-primary') === state.region || (state.region === 'EMEA' && EMEA.indexOf(el.getAttribute('data-primary')) > -1);
      el.style.order = own ? '0' : (rs.indexOf('GLOBAL') > -1 ? '2' : '1');
      el.classList.toggle('big', own && !$('[data-filter-regions] .bcard.big:not([hidden])') ? true : false);
    });
    var firstOwn = $$('[data-filter-regions] .bcard').filter(function (el) { return !el.hidden && el.style.order === '0'; })[0];
    $$('[data-filter-regions] .bcard').forEach(function (el) { el.classList.toggle('big', el === firstOwn); });
    if (window.WIL_runSearch) window.WIL_runSearch();
    $$('[data-show]').forEach(function (el) { el.hidden = el.getAttribute('data-show').split(',').indexOf(state.region) === -1; });
    $$('[data-current-region]').forEach(function (el) { var R = t('R') || {}; el.textContent = (R[state.region] || state.region).toUpperCase(); });
    // Regional page: show the matching desk.
    var desks = $$('.desk');
    if (desks.length) {
      var key = state.region;
      if (!$('#desk-' + key)) key = key === 'EMEA' ? 'EU' : 'EU';
      desks.forEach(function (d) { d.hidden = d.id !== 'desk-' + key; });
      $$('#regionbar .chip').forEach(function (c) { c.setAttribute('aria-pressed', String(c.getAttribute('data-region') === key)); });
    }
    renderComing();
  }
  function initRegion() {
    var hash = (location.hash || '').replace('#', '').toUpperCase();
    if (/^(GLOBAL|EMEA|EU|UK|NA|SA|AS|CN|ME|NAF)$/.test(hash)) state.region = hash;
    $$('#regionbar .chip').forEach(function (c) {
      c.addEventListener('click', function () {
        state.region = c.getAttribute('data-region'); store('wil-region', state.region);
        if ($('[data-region-page]')) history.replaceState(null, '', '#' + state.region.toLowerCase());
        applyRegion(); track('region_selected', {});
      });
    });
  }

  /* ---------- Calendar ---------- */
  var COMING = [];
  try { var cd = $('#coming-data'); if (cd) COMING = JSON.parse(cd.textContent); } catch (e) {}
  function today() { var d = new Date(); return Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()); }
  function renderComing() {
    $$('[data-timeline]').forEach(function (box) {
      var scope = box.getAttribute('data-timeline'); // "home" or a region key
      var limit = +(box.getAttribute('data-limit') || 99);
      var now = today();
      var items = COMING.filter(function (c) {
        var d = Date.parse(c.date);
        if (c.exact && d < now) return false;
        if (!c.exact && c.date && Date.parse(c.date) < now - 86400000 * 120) return false;
        if (state.type !== 'All' && c.type !== state.type) return false;
        if (scope === 'home') return state.region === 'GLOBAL' ? c.global || c.exact : inRegion([c.region]);
        return c.region === scope;
      }).sort(function (a, b) { return Date.parse(a.date) - Date.parse(b.date); }).slice(0, limit);
      var R = t('R') || {};
      if (!items.length) { box.innerHTML = '<p class="empty">' + t('nothing_region') + '</p>'; return; }
      box.innerHTML = items.map(function (c) {
        var days = Math.round((Date.parse(c.date) - now) / 86400000);
        var cdTxt = c.exact ? (days <= 0 ? 'D−0' : 'D−' + days) : '·';
        var reg = scope === 'home' ? '<span class="tl-region">' + (R[c.region] || c.region).toUpperCase() + '</span>' : '';
        return '<div class="tl-row"><span class="tl-cd">' + cdTxt + '</span><span class="tl-when">' + c.when + '</span><span class="type type-' + c.type + '">' + t(c.type) + '</span><span class="tl-what">' + c.what + reg + '</span></div>';
      }).join('');
    });
  }
  function initFilters() {
    $$('.filters .chip').forEach(function (c) {
      c.addEventListener('click', function () {
        state.type = c.getAttribute('data-type');
        $$('.filters .chip').forEach(function (x) { x.setAttribute('aria-pressed', String(x.getAttribute('data-type') === state.type)); });
        renderComing(); track('calendar_filtered', { type: state.type });
      });
    });
  }

  /* ---------- Forms ---------- */
  function post(url, data) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || j.ok === false) throw new Error((j.error || 'http') + ' ' + r.status); return j; }); });
  }
  function status(el, ok, msg, err) { el.hidden = false; el.className = 'status ' + (ok ? 'ok' : 'err'); el.textContent = msg + (err && err.message ? ' [' + err.message + ']' : ''); }
  function initForms() {
    var nl = $('#nl-form');
    if (nl) nl.addEventListener('submit', function (e) {
      e.preventDefault(); var b = $('button', nl); b.disabled = true;
      post('/api/subscribe', { email: nl.email.value, region: nl.region ? nl.region.value : state.region, lang: state.lang, hp: nl.website.value })
        .then(function () { status($('#nl-status'), true, t('nl_ok')); nl.reset(); track('newsletter_signup', {}); })
        .catch(function (e) { status($('#nl-status'), false, t('err_generic'), e); })
        .then(function () { b.disabled = false; });
    });
    $$('.fb-form').forEach(function (fb) {
      fb.addEventListener('submit', function (e) {
        e.preventDefault(); var b = $('button[type=submit]', fb); b.disabled = true;
        post('/api/contact', { kind: 'feedback', message: fb.message.value, from: fb.from.value, page: location.pathname, lang: state.lang, hp: fb.website.value })
          .then(function () { status($('.status', fb), true, t('fb_ok')); fb.reset(); track('feedback_sent', { page: location.pathname }); })
          .catch(function (e) { status($('.status', fb), false, t('err_generic'), e); })
          .then(function () { b.disabled = false; });
      });
    });
    var dlg = $('#contact');
    if (dlg) {
      var topic = 0;
      $$('[data-contact]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', ''); track('contact_opened', { from: a.getAttribute('data-contact') }); }); });
      $$('[data-close]', dlg).forEach(function (x) { x.addEventListener('click', function () { dlg.close(); }); });
      dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
      $$('[data-topic-i]', dlg).forEach(function (b) { b.addEventListener('click', function () { topic = +b.getAttribute('data-topic-i'); $$('[data-topic-i]', dlg).forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); }); }); });
      var f = $('#ct-form');
      f.addEventListener('submit', function (e) {
        e.preventDefault(); var b = $('button[type=submit]', f); b.disabled = true;
        post('/api/contact', { kind: 'contact', topic: (I18N.en.ct_topics || [])[topic], name: f.name.value, email: f.email.value, org: f.org.value, message: f.message.value, consent: f.consent.checked, lang: state.lang, hp: f.website.value })
          .then(function () { f.hidden = true; status($('#ct-status'), true, t('ct_ok')); track('contact_sent', { topic: topic }); })
          .catch(function (e) { status($('#ct-status'), false, t('err_generic'), e); })
          .then(function () { b.disabled = false; });
      });
    }
  }

  /* ---------- Article: acronyms ---------- */
  function initGlossary() {
    var back = $('#backpill'); if (!back) return;
    var saved = null;
    $$('.ast').forEach(function (b) {
      b.addEventListener('click', function () {
        saved = window.scrollY; var g = $('#g-' + b.getAttribute('data-g')); if (!g) return;
        $$('.gloss .hl').forEach(function (x) { x.classList.remove('hl'); }); g.classList.add('hl');
        g.scrollIntoView({ behavior: 'smooth', block: 'center' }); back.hidden = false; track('acronym_opened', { term: b.getAttribute('data-g') });
      });
    });
    back.addEventListener('click', function () { if (saved !== null) window.scrollTo({ top: saved, behavior: 'smooth' }); back.hidden = true; });
    $$('.gloss [data-back]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); back.click(); }); });
  }

  /* ---------- Article: audio ---------- */
  function fmt(s) { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function initAudio() {
    var p = $('#player'); if (!p) return;
    var au = $('audio', p), btn = $('.pbtn', p), seek = $('input[type=range]', p), cur = $('.cur', p), dur = $('.dur', p), rateBtn = $('[data-rate]', p);
    var key = 'wil-pos-' + p.getAttribute('data-id'), started = false, rates = [1, 1.25, 1.5, 0.8], ri = 0;
    var play = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg>';
    var pause = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>';
    au.addEventListener('loadedmetadata', function () { seek.max = au.duration; dur.textContent = fmt(au.duration); var pos = +store(key); if (pos > 5 && pos < au.duration - 5) au.currentTime = pos; });
    au.addEventListener('timeupdate', function () { seek.value = au.currentTime; cur.textContent = fmt(au.currentTime); if (Math.floor(au.currentTime) % 5 === 0) store(key, String(au.currentTime)); });
    au.addEventListener('play', function () { btn.innerHTML = pause; btn.setAttribute('aria-label', 'Pause'); if (!started) { started = true; track('audio_played', { id: p.getAttribute('data-id') }); } });
    au.addEventListener('pause', function () { btn.innerHTML = play; btn.setAttribute('aria-label', 'Play'); });
    au.addEventListener('ended', function () { store(key, '0'); track('audio_completed', { id: p.getAttribute('data-id') }); });
    btn.addEventListener('click', function () { if (au.paused) au.play(); else au.pause(); });
    seek.addEventListener('input', function () { au.currentTime = +seek.value; });
    $$('[data-skip]', p).forEach(function (b) { b.addEventListener('click', function () { au.currentTime = Math.max(0, Math.min(au.duration || 0, au.currentTime + +b.getAttribute('data-skip'))); }); });
    rateBtn.addEventListener('click', function () { ri = (ri + 1) % rates.length; au.playbackRate = rates[ri]; rateBtn.textContent = rates[ri] + '×'; });
    $$('[data-listen]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); p.scrollIntoView({ behavior: 'smooth', block: 'center' }); au.play(); }); });
    if (location.hash === '#listen') { p.scrollIntoView({ block: 'center' }); }
    if ('mediaSession' in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({ title: document.title.split(' · ')[0], artist: 'WhyItLands', artwork: [{ src: '/assets/img/icon-512.png', sizes: '512x512', type: 'image/png' }] });
      navigator.mediaSession.setActionHandler('seekbackward', function () { au.currentTime -= 15; });
      navigator.mediaSession.setActionHandler('seekforward', function () { au.currentTime += 30; });
    }
  }

  /* ---------- Outbound + scroll depth ---------- */
  function initTracking() {
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href^="http"]');
      if (a && a.hostname !== location.hostname) track('source_opened', { host: a.hostname });
    });
    var marks = [25, 50, 75, 100], hit = {};
    window.addEventListener('scroll', function () {
      var h = document.documentElement, pct = (h.scrollTop + innerHeight) / h.scrollHeight * 100;
      marks.forEach(function (m) { if (pct >= m && !hit[m]) { hit[m] = 1; track('scroll_depth', { depth: m, page: location.pathname }); } });
    }, { passive: true });
  }

  function initVideo() {
    var v = $('#iv'); if (!v) return; var box = v.parentNode, b = $('.iv-play', box);
    b.addEventListener('click', function () { v.controls = true; v.play(); });
    v.addEventListener('play', function () { box.classList.add('playing'); track('video_played', {}); });
    v.addEventListener('ended', function () { track('video_completed', {}); });
  }
  initVideo();
  function initSearch() {
    var q = $('#bq'), m = $('#bm'); if (!q) return;
    function run() {
      var term = q.value.trim().toLowerCase(), mon = m.value, shown = 0;
      $$('[data-searchable] .bcard').forEach(function (el) {
        var regionOk = !el.dataset.regionHidden;
        var ok = (!term || el.getAttribute('data-text').indexOf(term) > -1) && (!mon || el.getAttribute('data-date').indexOf(mon) === 0);
        el.classList.toggle('fhide', !ok); if (ok && !el.hidden) shown++;
      });
      $('#bnone').hidden = shown > 0;
    }
    q.addEventListener('input', run); m.addEventListener('change', run);
    window.WIL_runSearch = run;
  }
  initSearch();
  initLang(); initRegion(); initFilters(); initForms(); initGlossary(); initAudio(); initTracking();
  applyRegion(); applyLang();
})();
