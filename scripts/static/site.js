/* ImageGen Tracker client: theme toggle (as in x-digest), demo wall (incremental masonry), filter chips, lightbox. */
(() => {
  const root = document.documentElement;
  const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} } };
  const mq = matchMedia('(prefers-color-scheme: dark)');
  const effective = () => root.dataset.theme || (mq.matches ? 'dark' : 'light');
  const tBtn = document.querySelector('[data-toggle-theme]'), tLbl = document.querySelector('[data-theme-label]');
  const syncT = () => { tBtn?.setAttribute('aria-pressed', String(effective() === 'dark')); };
  tBtn?.addEventListener('click', () => {
    const next = effective() === 'dark' ? 'light' : 'dark';
    if (next === (mq.matches ? 'dark' : 'light')) { delete root.dataset.theme; store.set('igt.theme', null); }
    else { root.dataset.theme = next; store.set('igt.theme', next); }
    syncT();
  });
  mq.addEventListener?.('change', syncT); syncT();
  /* global EN <-> 中 toggle (mirrors x-digest's remembered 中文 switch): swaps English content for the pre-written Chinese */
  const zBtn = document.querySelector('[data-toggle-zh]');
  const syncZ = () => zBtn?.setAttribute('aria-checked', String(root.classList.contains('show-zh')));
  zBtn?.addEventListener('click', () => {
    root.classList.toggle('show-zh'); store.set('igt.zh', root.classList.contains('show-zh') ? '1' : null); syncZ();
    document.dispatchEvent(new Event('igt:zh'));
  });
  syncZ();
  /* glossary popovers: hover/focus via CSS; tap toggles .open so it also works on touch */
  document.addEventListener('click', (e) => {
    const g = e.target.closest('.gl');
    document.querySelectorAll('.gl.open').forEach((x) => { if (x !== g) x.classList.remove('open'); });
    if (g) { g.classList.toggle('open'); const r = g.getBoundingClientRect(); g.classList.toggle('flip', r.left + 220 > innerWidth); }
  });
  document.addEventListener('mouseover', (e) => { const g = e.target.closest?.('.gl'); if (g) g.classList.toggle('flip', g.getBoundingClientRect().left + 220 > innerWidth); });

  const copyText = (text, btn) => {
    const done = () => { const o = btn.textContent; btn.textContent = '已复制'; setTimeout(() => (btn.textContent = o), 1400); };
    const fb = () => { const ta = document.createElement('textarea'); ta.value = text; ta.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); done(); } catch {} ta.remove(); };
    navigator.clipboard ? navigator.clipboard.writeText(text).then(done, fb) : fb();
  };

  const wall = document.getElementById('wall');
  if (!wall) return;
  root.classList.add('has-tabs');
  const BATCH = 30, GAP = 10, COLW = 220;
  const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const blob = (h, thumb) => 'images_blobs/' + (thumb ? 'thumbs/' : '') + h.slice(0, 2) + '/' + h + '.webp';
  const EXT = '<svg class="ext" viewBox="0 0 12 12" width="11" height="11" aria-hidden="true"><path d="M5 2.25H3.5A1.75 1.75 0 0 0 1.75 4v4.5c0 .97.78 1.75 1.75 1.75H8A1.75 1.75 0 0 0 9.75 8.5V7" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M7 1.75h3.25V5M10.1 1.9 5.75 6.25" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>';
  let all = [], list = [], shown = 0, cols = [], heights = [], key = '';

  const meta = (it) => {
    const p = el('p', 'item-meta'); const dot = () => { const s = el('span', 'dot', '·'); s.setAttribute('aria-hidden', 'true'); return s; };
    p.append(el('span', 'model-tag', it.m || '未知模型'));
    if (it.a) { p.append(dot()); const a = el('a', 'handle', '@' + it.a); a.href = 'https://x.com/' + it.a; a.rel = 'noopener'; p.append(a); }
    p.append(dot(), el('span', 'ts', it.d || ''));
    if (it.s) { p.append(dot()); const a = el('a', 'orig'); a.href = it.s; a.rel = 'noopener'; a.innerHTML = '原帖' + EXT; p.append(a); }
    return p;
  };
  /* render text with glossary terms (first occurrence) + optional Chinese version shown under html.show-zh */
  const glossify = (parent, text, gl, used) => {
    const terms = (gl || []).filter(([t]) => !used.has(t.toLowerCase())).sort((a, b) => b[0].length - a[0].length);
    if (!terms.length) { parent.append(text); return; }
    const esc = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(?<![\\w-])(' + terms.map(([t]) => esc(t)).join('|') + ')(?![\\w-])', 'gi');
    let last = 0, m;
    while ((m = re.exec(text))) {
      const k = m[1].toLowerCase(); if (used.has(k)) continue;
      const g = terms.find(([t]) => t.toLowerCase() === k); if (!g) continue;
      used.add(k); parent.append(text.slice(last, m.index));
      const sp = el('span', 'gl', m[1]); sp.tabIndex = 0; sp.dataset.gl = g[1]; parent.append(sp); last = m.index + m[1].length;
    }
    parent.append(text.slice(last));
  };
  const fillText = (node, en, zh, gl) => {
    const used = cur && cur.__used ? cur.__used : new Set();
    if (cur) cur.__used = used;
    const a = el('span', zh ? 'en-only' : ''); glossify(a, en, gl || (cur && cur.g), used); node.append(a);
    if (zh) { const b = el('span', 'zh-only', zh); b.lang = 'zh-CN'; node.append(b); }
  };
  const promptBox = (it, clamp) => {
    const box = el('div', 'prompt');
    if (!it.p) { box.append(el('span', 'prompt-none', '提示词：不详')); return box; }
    const head = el('div', 'prompt-head'); head.append(el('span', '', '提示词' + (it.partial ? '（部分）' : '')));
    const acts = el('span', 'acts');
    if (clamp) { const ex = el('button', '', '展开'); ex.type = 'button'; ex.dataset.expand = ''; ex.setAttribute('aria-expanded', 'false'); acts.append(ex); }
    const cp = el('button', '', '复制'); cp.type = 'button'; cp.addEventListener('click', () => copyText(it.p, cp)); acts.append(cp);
    head.append(acts); const pre = el('pre', 'prompt-text'); fillText(pre, it.p, it.pz, it.g); box.append(head, pre);
    if (it.pz) box.append(el('p', 'src-note zh-only', '以上为中文翻译，“复制”始终复制英文原文提示词。'));
    return box;
  };
  const card = (it) => {
    const c = el('a', 'card'); c.id = 'c-' + it.u; c.href = '#' + it.u; c.setAttribute('aria-label', (it.t || it.u) + '（查看大图与提示词）');
    if (it.i && it.i.length) {
      const [h, , , tw, th] = it.i[0];
      const im = el('img'); im.src = blob(h, true); im.width = tw; im.height = th; im.loading = 'lazy'; im.decoding = 'async'; im.alt = it.t || '';
      c.append(im); if (it.i.length > 1) c.append(el('span', 'count', it.i.length + ' 图'));
    }
    const cap = el('span', 'cap'); cap.append(el('span', 'model-tag', (it.k || ['其他'])[0]), el('span', 'cap-t', it.t || ''));
    c.append(cap); if (it.p) c.dataset.hasPrompt = '';
    c.addEventListener('click', (e) => { if (e.metaKey || e.ctrlKey || e.shiftKey) return; e.preventDefault(); openLB(it.u, 0); });
    return c;
  };
  /* JS masonry: N column stacks, each card goes to the currently shortest one (stable when appending batches) */
  const colCount = () => { const w = wall.clientWidth; return Math.max(2, Math.min(6, Math.floor((w + GAP) / (COLW + GAP)))); };
  const layout = () => {
    wall.textContent = ''; cols = []; heights = []; const n = colCount();
    for (let i = 0; i < n; i++) { const c = el('div', 'wall-col'); wall.append(c); cols.push(c); heights.push(0); }
    shown = 0; more();
  };
  const estimate = (it) => { const w = cols[0].clientWidth || 300; const im = it.i && it.i[0]; return (im ? w * im[4] / im[3] : 0) + 46; };
  const more = () => {
    const end = Math.min(shown + BATCH, list.length);
    for (; shown < end; shown++) {
      const it = list[shown]; let j = 0; for (let k = 1; k < cols.length; k++) if (heights[k] < heights[j] - 1) j = k;
      const c = card(it); cols[j].append(c); heights[j] += estimate(it) + GAP;
    }
    requestAnimationFrame(() => cols.forEach((c, i) => (heights[i] = c.offsetHeight)));
    sentinel.hidden = shown >= list.length;
  };
  const sentinel = document.getElementById('sentinel');
  if ('IntersectionObserver' in window) new IntersectionObserver((es) => { if (es.some((x) => x.isIntersecting) && shown < list.length) more(); }, { rootMargin: '1200px 0px' }).observe(sentinel);
  else addEventListener('scroll', () => { if (shown < list.length && sentinel.getBoundingClientRect().top < innerHeight + 1200) more(); }, { passive: true });

  const chipsBox = document.getElementById('chips');
  const setKey = (k) => {
    key = k; list = k ? all.filter((it) => (it.k || []).includes(k)) : all;
    chipsBox.querySelectorAll('.chip').forEach((c) => { const on = c.dataset.k === k; c.classList.toggle('on', on); c.setAttribute('aria-pressed', String(on)); });
    layout();
  };
  let rw = 0, rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { if (wall.clientWidth !== rw) { rw = wall.clientWidth; if (colCount() !== cols.length) layout(); } }, 150); });

  /* ---- lightbox ---- */
  const lb = el('div', 'lb'); lb.hidden = true; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', '案例详情');
  lb.innerHTML = '<div class="lb-stage"><img class="lb-img" alt=""><button type="button" class="lb-nav lb-prev" aria-label="上一张">‹</button><button type="button" class="lb-nav lb-next" aria-label="下一张">›</button><span class="lb-pos"></span></div><aside class="lb-side"><button type="button" class="lb-close" aria-label="关闭">✕</button><div class="lb-info"></div></aside>';
  document.body.append(lb);
  const lbImg = lb.querySelector('.lb-img'), lbInfo = lb.querySelector('.lb-info'), lbPos = lb.querySelector('.lb-pos');
  let cur = null, ci = 0, lastFocus = null;
  const byId = (u) => all.find((x) => x.u === u);
  const showImg = () => {
    const ims = cur.i || []; const n = ims.length;
    if (!n) { lbImg.hidden = true; lbPos.textContent = ''; return; }
    const [h, w, hh, tw, th] = ims[ci]; lbImg.hidden = false;
    lbImg.src = blob(h, true); lbImg.width = w; lbImg.height = hh; lbImg.alt = cur.t || '';
    const full = new Image(); full.onload = () => { if (cur && cur.i[ci] && cur.i[ci][0] === h) lbImg.src = full.src; }; full.src = blob(h, false);
    lbPos.textContent = n > 1 ? (ci + 1) + ' / ' + n : '';
    if (n > 1) { const nx = ims[(ci + 1) % n][0]; new Image().src = blob(nx, false); }
  };
  const render = () => {
    lbInfo.textContent = ''; if (cur) cur.__used = new Set();
    const h = el('h2', 'item-title', cur.t || cur.u); lbInfo.append(h, meta(cur));
    const dl = el('dl', 'facts'); [['模型', cur.m], ['厂商', cur.mk], ['作者', cur.a ? '@' + cur.a : '不详'], ['日期', cur.d]].forEach(([k, v]) => { dl.append(el('dt', '', k), el('dd', '', v || '不详')); });
    lbInfo.append(dl, promptBox(cur, false));
    if (cur.x) { lbInfo.append(el('h3', 'lb-h', '原帖文字')); const q = el('blockquote', 'post-text'); fillText(q, cur.x, cur.xz); lbInfo.append(q); }
    if (cur.ps) lbInfo.append(el('p', 'entry-meta src-note', '提示词来源：' + cur.ps));
    const links = el('p', 'lb-links');
    if (cur.s) { const a = el('a', 'orig'); a.href = cur.s; a.rel = 'noopener'; a.innerHTML = '打开原帖' + EXT; links.append(a); }
    const pl = el('a', '', '复制链接'); pl.href = '#' + cur.u; pl.addEventListener('click', (e) => { e.preventDefault(); copyText(location.href.split('#')[0] + '#' + cur.u, pl); }); links.append(pl);
    lbInfo.append(links); showImg();
  };
  const openLB = (u, i = 0, push = true) => {
    const it = byId(u); if (!it) return false;
    if (lb.hidden) { lastFocus = document.activeElement; }
    cur = it; ci = i; lb.hidden = false; document.body.classList.add('lb-open'); render();
    if (push && location.hash !== '#' + u) { if (lbPushed) history.replaceState(null, '', '#' + u); else { history.pushState(null, '', '#' + u); lbPushed = true; } }
    lb.querySelector('.lb-close').focus({ preventScroll: true }); return true;
  };
  const closeLB = (fromRoute) => {
    if (lb.hidden) return; lb.hidden = true; document.body.classList.remove('lb-open'); lbImg.removeAttribute('src');
    if (!fromRoute) { if (lbPushed) history.back(); else history.replaceState(null, '', key ? '#demos/' + encodeURIComponent(key) : '#demos'); }
    lbPushed = false;
    const c = cur && document.getElementById('c-' + cur.u); cur = null; (c || lastFocus)?.focus?.({ preventScroll: true });
  };
  const step = (d) => {
    const n = (cur.i || []).length;
    if (n > 1 && ci + d >= 0 && ci + d < n) { ci += d; showImg(); return; }
    const idx = list.indexOf(cur); const nxt = list[idx + d]; if (!nxt) return;
    while (shown <= idx + d + 1 && shown < list.length) more();
    openLB(nxt.u, d < 0 ? Math.max(0, (nxt.i || []).length - 1) : 0);
  };
  lb.querySelector('.lb-close').addEventListener('click', () => closeLB());
  lb.querySelector('.lb-prev').addEventListener('click', () => step(-1));
  lb.querySelector('.lb-next').addEventListener('click', () => step(1));
  lb.addEventListener('click', (e) => { if (e.target === lb || e.target.classList.contains('lb-stage')) closeLB(); });
  addEventListener('keydown', (e) => {
    if (lb.hidden) return;
    if (e.key === 'Escape') closeLB();
    else if (e.key === 'ArrowRight') step(1);
    else if (e.key === 'ArrowLeft') step(-1);
    else if (e.key === 'Tab') { const f = [...lb.querySelectorAll('button:not([hidden]),a[href]')]; const i = f.indexOf(document.activeElement);
      if (e.shiftKey ? i <= 0 : i === f.length - 1) { e.preventDefault(); f[e.shiftKey ? f.length - 1 : 0].focus(); } }
  });
  let tx = 0, ty = 0; const stage = lb.querySelector('.lb-stage');
  stage.addEventListener('touchstart', (e) => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  stage.addEventListener('touchend', (e) => { const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1); else if (dy > 90 && Math.abs(dy) > Math.abs(dx) * 1.5) closeLB(); }, { passive: true });
  /* ---- tabs + hash routing: #news | #demos | #demos/<model> | #<uid> (opens lightbox on Demos) ---- */
  const tabs = document.querySelectorAll('.tab'); let loaded = false, wantFilter = null, lbPushed = false;
  const setTab = (t) => {
    root.classList.toggle('tab-demos', t === 'demos');
    tabs.forEach((x) => { const on = x.dataset.tab === t; x.classList.toggle('on', on); x.setAttribute('aria-selected', String(on)); });
    
    if (t === 'demos' && loaded && cols.length !== colCount()) layout();
  };
  const route = () => {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h || h === 'news') { closeLB(true); setTab('news'); return; }
    setTab('demos');
    if (h === 'demos' || h.startsWith('demos/')) { closeLB(true); const k = h.slice(6); if (loaded) { if (k !== key) setKey(k); } else wantFilter = k; return; }
    if (loaded) { if (!openLB(h, 0, false)) closeLB(true); }
  };
  addEventListener('hashchange', route);
  route();

  fetch(wall.dataset.src).then((r) => r.json()).then((j) => {
    all = j.items || [];
    const mk = (k, label, n) => { const b = el('button', 'chip', label); b.type = 'button'; b.dataset.k = k; b.append(el('span', 'n', String(n))); b.addEventListener('click', () => { history.replaceState(null, '', k ? '#demos/' + encodeURIComponent(k) : '#demos'); setKey(k); }); return b; };
    chipsBox.append(mk('', '全部', all.length)); (j.keys || []).forEach(([k, n]) => chipsBox.append(mk(k, k, n)));
    loaded = true; rw = wall.clientWidth; setKey(wantFilter && (j.keys || []).some(([k]) => k === wantFilter) ? wantFilter : '');
    route();
  }).catch(() => { wall.textContent = '数据加载失败，请刷新重试。'; });
})();
