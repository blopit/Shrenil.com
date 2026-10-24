// Shrenil.com — portfolio.js: the control layer of the CentrOS iOS design on the web.
// Appearance (Dark · Light · Match device; Sky · Solid; New sky), the top bar's inline title, the tab bar
// that minimises while you read, the contact sheet, deep links into disclosures, copy-email, print.
// Progressive enhancement only: every page works without this file.
(() => {
  'use strict';
  const win = window, doc = document, root = doc.documentElement;
  const KEY = { appearance: 'centros.appearance', background: 'centros.background' };
  const THEME_COLOR = { dark: '#000000', light: '#F2F2F7' };
  const media = (q) => (win.matchMedia ? win.matchMedia(q) : null);
  const listen = (mq, fn) => { if (!mq) return; if (mq.addEventListener) mq.addEventListener('change', fn); else if (mq.addListener) mq.addListener(fn); };
  const reduceMotion = media('(prefers-reduced-motion: reduce)');
  const deviceLight = media('(prefers-color-scheme: light)');
  const phone = media('(max-width: 767px), (max-height: 500px)');
  const topBar = media('(min-width: 1024px)');
  const moving = () => !(reduceMotion && reduceMotion.matches);
  const store = {
    get(k) { try { return win.localStorage.getItem(k); } catch (_) { return null; } },
    set(k, v) { try { if (v == null) win.localStorage.removeItem(k); else win.localStorage.setItem(k, v); } catch (_) { /* blocked: the choice lasts for this page view */ } },
  };
  const sky = (method, arg) => { const s = win.CentrosSky; if (s && typeof s[method] === 'function') { try { s[method](arg); } catch (_) { /* the sky is decoration */ } } };
  const clampY = () => Math.min(Math.max(win.scrollY || 0, 0), Math.max(0, root.scrollHeight - win.innerHeight));
  const isKeyboard = (el) => { try { return el.matches(':focus-visible'); } catch (_) { return true; } };

  const whenReady = [];
  const ready = () => requestAnimationFrame(() => {
    whenReady.forEach((f) => f());
    void root.offsetWidth;
    root.classList.add('is-ready');
  });
  if (doc.readyState === 'complete') ready(); else win.addEventListener('load', ready, { once: true });

  const prefs = {
    appearance: root.getAttribute('data-appearance') || 'dark',
    background: root.classList.contains('sky-solid') ? 'solid' : 'sky',
  };
  const resolved = () => (prefs.appearance === 'light' || (prefs.appearance === 'system' && deviceLight && deviceLight.matches) ? 'light' : 'dark');
  const picks = [...doc.querySelectorAll('select[data-pref]')];
  const newSky = doc.querySelector('[data-new-sky]');
  const skyDrawing = () => {
    const s = win.CentrosSky;
    if (!s || typeof s.reseed !== 'function' || typeof s.info !== 'function') return false;
    try { const m = String(s.info().mode || ''); return m !== 'fallback' && m !== 'solid'; } catch (_) { return false; }
  };
  const syncControls = () => {
    picks.forEach((sel) => {
      if (sel.dataset.pref === 'background') {             // the app's Background: sky / solid (a still sky under reduced motion is still the sky)
        const o = sel.querySelector('option[value="sky"]');
        if (o && o.textContent !== 'Sky') o.textContent = 'Sky';
      }
      sel.value = prefs[sel.dataset.pref];
      const shown = sel.parentElement && sel.parentElement.querySelector('[data-pick-value]');
      const opt = sel.options[sel.selectedIndex];
      if (shown && opt) shown.textContent = opt.textContent;
    });
    if (newSky) newSky.hidden = prefs.background === 'solid' || !skyDrawing();
  };
  win.addEventListener('centros:sky', syncControls);
  const apply = () => {
    const theme = resolved();
    root.setAttribute('data-appearance', prefs.appearance);
    if (root.getAttribute('data-theme') !== theme) root.setAttribute('data-theme', theme);
    root.classList.toggle('sky-solid', prefs.background === 'solid');
    doc.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute('content', THEME_COLOR[theme]));
    syncControls();
  };
  const readStored = () => {
    const a = store.get(KEY.appearance), b = store.get(KEY.background);
    prefs.appearance = a === 'light' || a === 'system' ? a : 'dark';
    prefs.background = b === 'solid' ? 'solid' : 'sky';
  };
  picks.forEach((sel) => sel.addEventListener('change', () => {
    if (sel.dataset.pref === 'appearance') {
      prefs.appearance = sel.value === 'light' || sel.value === 'system' ? sel.value : 'dark';
      store.set(KEY.appearance, prefs.appearance === 'dark' ? null : prefs.appearance);
    } else {
      prefs.background = sel.value === 'solid' ? 'solid' : 'sky';
      store.set(KEY.background, prefs.background === 'sky' ? null : 'solid');
    }
    apply();
  }));
  const newSkyBtn = doc.querySelector('[data-new-sky-btn]');
  if (newSkyBtn) newSkyBtn.addEventListener('click', () => {
    sky('reseed');
    const st = doc.querySelector('[data-new-sky-status]');
    if (st) { st.textContent = ''; setTimeout(() => { st.textContent = 'A new sky is drawing'; }, 50); }
  });
  listen(deviceLight, () => { if (prefs.appearance === 'system') apply(); });
  win.addEventListener('storage', (e) => {
    if (e.key !== null && e.key !== KEY.appearance && e.key !== KEY.background) return;
    readStored();
    apply();
  });
  syncControls();

  const topbar = doc.querySelector('[data-topbar]');
  const largeTitle = doc.querySelector('[data-large-title]');
  const edge = () => root.classList.toggle('is-scrolled', clampY() > 2);
  if (topbar && largeTitle && 'IntersectionObserver' in win) {
    let io = null, band = -1, t = 0;
    const watch = () => {
      const h = Math.round(topbar.getBoundingClientRect().height);
      if (io && h === band) return;
      band = h;
      if (io) io.disconnect();
      io = new IntersectionObserver(([e]) => {
        root.classList.toggle('is-titled', !e.isIntersecting && e.boundingClientRect.top < band);
      }, { rootMargin: `-${band}px 0px 0px 0px`, threshold: 0 });
      io.observe(largeTitle);
    };
    watch();
    win.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(watch, 150); }, { passive: true });
  }

  const bar = doc.querySelector('[data-tabbar]');
  let jumpUntil = 0, expandBar = null, barScroll = () => {};
  const markJump = () => { jumpUntil = performance.now() + 400; if (expandBar) expandBar(); };
  if (bar) {
    const TOP = 80, DELTA = 8, MIN_SCROLL = 240;
    let min = false, pinned = false, armed = false, minAtDown = false, lastY = clampY();
    const current = bar.querySelector('.tab[aria-current="page"]');
    const pushed = !current;
    const setMin = (next) => {
      if (next && (pushed || pinned || (topBar && topBar.matches) || root.classList.contains('is-sheet') || root.scrollHeight - win.innerHeight < MIN_SCROLL)) next = false;
      if (next === min) return;
      min = next;
      bar.classList.toggle('is-min', next);
      if (current) { if (next) current.setAttribute('aria-expanded', 'false'); else current.removeAttribute('aria-expanded'); }
    };
    listen(topBar, () => setMin(false));
    expandBar = () => setMin(false);
    barScroll = () => {
      const y = clampY();
      if (!armed || performance.now() < jumpUntil) { lastY = y; return; }
      if (y < TOP) { setMin(false); lastY = y; return; }
      const dy = y - lastY;
      if (Math.abs(dy) < DELTA) return;
      setMin(dy > 0);
      lastY = y;
    };
    bar.addEventListener('pointerdown', () => { minAtDown = min; });
    bar.addEventListener('click', (e) => {
      const t = e.target instanceof Element ? e.target : null;
      const wasMin = min || minAtDown;
      minAtDown = false;
      if (!wasMin || !t || !t.closest('.tabbar__tabs')) return;
      const tab = t.closest('.tab');
      if (tab && tab !== current) { setMin(false); return; }
      e.preventDefault(); setMin(false);
    });
    bar.addEventListener('focusin', (e) => {
      if (isKeyboard(e.target)) pinned = true;
      setMin(false);
    });
    bar.addEventListener('focusout', (e) => { if (!bar.contains(e.relatedTarget)) pinned = false; });
    whenReady.push(() => { lastY = clampY(); armed = true; });
  }
  let ticking = false;
  win.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; edge(); barScroll(); });
  }, { passive: true });
  edge();
  win.addEventListener('hashchange', markJump);

  const sheet = doc.getElementById('sheet');
  let closeSheetNow = () => {};
  if (sheet && typeof sheet.showModal === 'function') {
    const scroller = sheet.querySelector('.sheet__scroll');
    const handle = sheet.querySelector('.sheet__bar');
    let opener = null, closing = 0, onEnd = null;
    const cancelClose = () => {
      if (closing) { clearTimeout(closing); closing = 0; }
      if (onEnd) { sheet.removeEventListener('transitionend', onEnd); onEnd = null; }
    };
    doc.querySelectorAll('[data-sheet]').forEach((a) => { a.setAttribute('aria-haspopup', 'dialog'); a.setAttribute('aria-controls', 'sheet'); });
    const openSheet = (from) => {
      if (sheet.open) return;
      cancelClose();
      opener = from || doc.activeElement;
      syncControls();
      root.classList.add('is-sheet');
      sheet.style.transform = '';
      sheet.showModal();
      if (scroller) scroller.scrollTop = 0;
      void sheet.offsetWidth;
      sheet.classList.add('is-in');
      sky('settle', true);
    };
    const closeSheet = () => {
      if (!sheet.open || closing) return;
      sheet.classList.remove('is-in', 'is-dragging');
      sheet.style.transform = '';
      const done = () => { cancelClose(); if (sheet.open) sheet.close(); };
      onEnd = (e) => { if (e.target === sheet) done(); };
      sheet.addEventListener('transitionend', onEnd);
      closing = setTimeout(done, moving() ? 650 : 50);
    };
    closeSheetNow = () => { if (sheet.open) sheet.close(); };
    sheet.addEventListener('close', () => {
      cancelClose();
      root.classList.remove('is-sheet');
      sheet.classList.remove('is-in', 'is-dragging');
      sheet.style.transform = '';
      sky('settle', false);
      const back = opener; opener = null;
      if (back && back.isConnected && typeof back.focus === 'function') back.focus({ preventScroll: true });
    });
    sheet.addEventListener('cancel', (e) => { e.preventDefault(); closeSheet(); });
    sheet.addEventListener('click', (e) => {
      if (e.target !== sheet) return;
      const r = sheet.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) closeSheet();
    });
    sheet.querySelectorAll('[data-sheet-close]').forEach((b) => b.addEventListener('click', closeSheet));
    doc.addEventListener('click', (e) => {
      const a = e.target instanceof Element ? e.target.closest('[data-sheet]') : null;
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      openSheet(a);
    });
    if (handle) {
      let y0 = null, t0 = 0, dy = 0, id = null;
      handle.addEventListener('pointerdown', (e) => {
        if (!(phone && phone.matches) || e.button !== 0 || (e.target instanceof Element && e.target.closest('button,a,input,label'))) return;
        y0 = e.clientY; t0 = performance.now(); dy = 0; id = e.pointerId;
        try { handle.setPointerCapture(id); } catch (_) { /* fine */ }
        sheet.classList.add('is-dragging');
      });
      handle.addEventListener('pointermove', (e) => {
        if (y0 === null || e.pointerId !== id) return;
        dy = Math.max(0, e.clientY - y0);
        sheet.style.transform = `translateY(${dy}px)`;
      });
      const end = (e) => {
        if (y0 === null || e.pointerId !== id) return;
        const v = dy / Math.max(1, performance.now() - t0);
        y0 = null; id = null;
        sheet.classList.remove('is-dragging');
        if (dy > 96 || v > 0.6) closeSheet(); else sheet.style.transform = '';
      };
      handle.addEventListener('pointerup', end);
      handle.addEventListener('pointercancel', end);
    }
  }

  const reveal = () => {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const t = id && doc.getElementById(id);
    if (!t) return;
    let opened = false;
    for (let d = t; d; d = d.parentElement) if (d.tagName === 'DETAILS' && !d.open) { d.open = true; opened = true; }
    if (opened) t.scrollIntoView();
  };
  win.addEventListener('hashchange', reveal);
  reveal();
  const samePage = (a) => a.hash && a.origin === location.origin && a.pathname === location.pathname && a.search === location.search;
  const land = (a) => {                                   // land focus on the target section's heading
    let t = null;
    try { t = doc.getElementById(decodeURIComponent(a.hash.slice(1))); } catch (_) { return; }
    const h = t && t.matches('section[aria-labelledby]') ? doc.getElementById(t.getAttribute('aria-labelledby')) : null;
    if (!h) return;
    if (!h.hasAttribute('tabindex')) h.setAttribute('tabindex', '-1');
    h.focus({ preventScroll: true });
  };
  doc.addEventListener('click', (e) => {
    const a = e.target instanceof Element ? e.target.closest('a[href*="#"]') : null;
    if (!a || a.hasAttribute('data-sheet') || !samePage(a) || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    markJump();
    setTimeout(() => { reveal(); land(a); }, 0);
  });

  if (location.protocol === 'https:' && win.isSecureContext && navigator.clipboard) {
    doc.querySelectorAll('[data-copy]').forEach((btn) => {
      const label = btn.textContent;
      const status = btn.parentElement ? btn.parentElement.querySelector('[role="status"]') : null;
      let timer = 0;
      btn.hidden = false;
      btn.addEventListener('click', async () => {
        let ok = true;
        try { await navigator.clipboard.writeText(btn.dataset.copy); } catch (_) { ok = false; }
        btn.textContent = ok ? 'Copied' : 'Copy failed';
        btn.classList.toggle('is-done', ok);
        if (status) status.textContent = ok ? 'Email address copied' : 'Could not copy; select the address instead';
        clearTimeout(timer);
        timer = setTimeout(() => { btn.textContent = label; btn.classList.remove('is-done'); if (status) status.textContent = ''; }, 2000);
      });
    });
  }

  let reopened = [];
  win.addEventListener('beforeprint', () => {
    closeSheetNow();
    doc.querySelectorAll('details:not([open])').forEach((d) => { d.open = true; reopened.push(d); });
  });
  win.addEventListener('afterprint', () => { reopened.forEach((d) => { d.open = false; }); reopened = []; });

  win.addEventListener('pageshow', (e) => {
    if (!e.persisted) return;
    root.classList.remove('is-ready');
    closeSheetNow();
    readStored();
    apply();
    if (expandBar) expandBar();
    edge();
    ready();
  });

  const year = doc.querySelector('[data-year]');
  if (year) year.textContent = String(new Date().getFullYear());
})();
