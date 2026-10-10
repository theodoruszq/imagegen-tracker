(() => {
  const root = document.documentElement;
  const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} } };
  /* theme toggle (same behaviour as x-digest: follows OS unless overridden) */
  const mq = matchMedia('(prefers-color-scheme: dark)');
  const effective = () => root.dataset.theme || (mq.matches ? 'dark' : 'light');
  const btn = document.querySelector('[data-toggle-theme]'), lbl = document.querySelector('[data-theme-label]');
  const sync = () => { if (lbl) lbl.textContent = effective() === 'dark' ? '浅色' : '深色'; };
  btn?.addEventListener('click', () => {
    const next = effective() === 'dark' ? 'light' : 'dark';
    if (next === (mq.matches ? 'dark' : 'light')) { delete root.dataset.theme; store.set('igt.theme', null); }
    else { root.dataset.theme = next; store.set('igt.theme', next); }
    sync();
  });
  mq.addEventListener?.('change', sync); sync();

  /* model filter chips */
  const chips = document.querySelectorAll('.chip');
  const apply = (k) => {
    chips.forEach((c) => { const on = c.dataset.k === k; c.classList.toggle('on', on); c.setAttribute('aria-pressed', String(on)); });
    document.querySelectorAll('.card[data-models]').forEach((el) => { el.hidden = !!k && !el.dataset.models.split('|').includes(k); });
  };
  chips.forEach((c) => c.addEventListener('click', () => { apply(c.dataset.k); history.replaceState(null, '', c.dataset.k ? '#m=' + encodeURIComponent(c.dataset.k) : location.pathname); }));
  if (chips.length && location.hash.startsWith('#m=')) apply(decodeURIComponent(location.hash.slice(3)));

  /* prompt: expand/collapse (only when clamped) + copy */
  const fit = () => document.querySelectorAll('.card .prompt').forEach((p) => {
    const t = p.querySelector('.prompt-text'), b = p.querySelector('[data-expand]');
    if (b && t && !p.classList.contains('open')) b.hidden = t.scrollHeight <= t.clientHeight + 2;
  });
  document.addEventListener('click', (e) => {
    const ex = e.target.closest('[data-expand]');
    if (ex) { const p = ex.closest('.prompt'); const o = p.classList.toggle('open'); ex.textContent = o ? '收起' : '展开'; ex.setAttribute('aria-expanded', String(o)); }
    const cp = e.target.closest('[data-copy]');
    if (cp) {
      const text = cp.closest('.prompt').querySelector('.prompt-text').textContent;
      const done = () => { cp.textContent = '已复制'; setTimeout(() => (cp.textContent = '复制'), 1500); };
      const fallback = () => { const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); done(); } catch {} ta.remove(); };
      navigator.clipboard ? navigator.clipboard.writeText(text).then(done, fallback) : fallback();
    }
  });
  fit(); addEventListener('load', fit); addEventListener('resize', fit);
})();
