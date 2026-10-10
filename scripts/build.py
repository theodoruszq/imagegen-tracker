#!/usr/bin/env python3
"""Regenerate the static site in docs/ from data/.  Stdlib only, no network, idempotent.

Outputs: docs/index.html (one page, tabs #news / #demos; wall + lightbox rendered client-side),
docs/demos.html (redirect to ./#demos),
docs/data.json (compact demo data), docs/assets/ (copied from scripts/static/).
Never touches docs/images_blobs/ or docs/.nojekyll.  Removes pages from older layouts
(docs/timeline.html, docs/items/).  Style follows theodoruszq/x-digest.
"""
import hashlib, html, json, os, re, shutil, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, DOCS, STATIC = (os.path.join(ROOT, p) for p in ("data", "docs", "scripts/static"))
E = lambda s: html.escape("" if s is None else str(s), quote=True)
EXT = ('<svg class="ext" viewBox="0 0 12 12" width="11" height="11" aria-hidden="true" focusable="false">'
       '<path d="M5 2.25H3.5A1.75 1.75 0 0 0 1.75 4v4.5c0 .97.78 1.75 1.75 1.75H8A1.75 1.75 0 0 0 9.75 8.5V7" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>'
       '<path d="M7 1.75h3.25V5M10.1 1.9 5.75 6.25" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
KEYS = [("GPT Image", r"gpt[ -]?image|chatgpt images?|gpt ?2\.5"), ("Nano Banana", r"nano banana|gemini.*image|imagen"),
        ("Midjourney", r"midjourney"), ("FLUX", r"flux"), ("Seedream", r"seedream"), ("Grok Imagine", r"grok imagine"),
        ("Ideogram", r"ideogram"), ("Recraft", r"recraft"), ("Qwen-Image", r"qwen"), ("Hunyuan/Hy", r"hunyuan|\bhy[ -]?image"),
        ("Kling/Kolors", r"kling|kolors")]
KEY_ORDER = [k for k, _ in KEYS] + ["其他"]
STALE = ["timeline.html", "items"]  # pages from older layouts

def load_items():
    items, seen = [], set()
    with open(os.path.join(DATA, "items.jsonl"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip(): continue
            it = json.loads(line); uid = it.get("uid", "")
            if uid in seen: sys.exit(f"duplicate uid {uid} (line {n})")
            if not re.fullmatch(r"x-\d+|news-[a-z0-9]+(-[a-z0-9.]+)+", uid): sys.exit(f"bad uid {uid!r} (line {n})")
            if it.get("type") not in ("news", "demo"): sys.exit(f"bad type for {uid}")
            seen.add(uid); items.append(it)
    items.sort(key=lambda x: (x.get("date", ""), x["uid"]), reverse=True)
    return items

def model_keys(it):
    m = (it.get("model") or "").lower()
    return [k for k, rx in KEYS if re.search(rx, m)] or ["其他"]

def blob(h, thumb=False):
    return os.path.join(DOCS, "images_blobs", *(["thumbs"] if thumb else []), h[:2], h + ".webp")

def webp_size(path):
    with open(path, "rb") as f: b = f.read(30)
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP": sys.exit(f"not a webp: {path}")
    c = b[12:16]
    if c == b"VP8 ": w, h = struct.unpack("<HH", b[26:30]); return w & 0x3FFF, h & 0x3FFF
    if c == b"VP8L": v = struct.unpack("<I", b[21:25])[0]; return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
    if c == b"VP8X": return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    sys.exit(f"unknown webp chunk {c!r}: {path}")

def page(title, body, ver, desc):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#141414" media="(prefers-color-scheme: dark)">
  <title>{E(title)}</title>
  <meta name="description" content="{E(desc)}">
  <link rel="icon" href="assets/icon.svg" type="image/svg+xml">
  <link rel="preload" href="assets/fonts/lato-regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="assets/style.css?v={ver}">
  <script>(function(){{var d=document.documentElement;d.classList.add('js');try{{var t=localStorage.getItem('igt.theme');if(t)d.dataset.theme=t;if(localStorage.getItem('igt.zh')==='1')d.classList.add('show-zh');}}catch(e){{}}var h=location.hash.slice(1);if(h&&h!=='news')d.classList.add('tab-demos');}})();</script>
  <script src="assets/site.js?v={ver}" defer></script>
</head>
<body>
  <h1 class="sr-only">生图模型追踪 · AI ImageGen Tracker</h1>
  <header class="topbar">
    <nav class="tabs" role="tablist" aria-label="栏目">
      <a class="tab on" role="tab" href="#news" data-tab="news" aria-selected="true" aria-controls="panel-news">News</a>
      <a class="tab" role="tab" href="#demos" data-tab="demos" aria-selected="false" aria-controls="panel-demos">Demos</a>
    </nav>
    <button type="button" class="tr-toggle" data-toggle-zh role="switch" aria-checked="false" aria-label="英文内容切换为中文翻译" title="EN ↔ 中：英文内容切换为中文翻译"><span class="tr-en">EN</span><span class="tr-arrow" aria-hidden="true">↔</span><span class="tr-zh">中</span></button>
    <button type="button" class="theme-btn" data-toggle-theme aria-label="切换深色/浅色" title="切换深色/浅色"><svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z" fill="currentColor"/></svg></button>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer"><p>数据来自 <a href="https://x.com">X</a> 公开帖子与官方发布 · 每日 09:03 / 21:03（北京时间）更新 · <a href="https://github.com/theodoruszq/imagegen-tracker">GitHub</a></p></footer>
</body>
</html>
"""

def rich(text):
    """HTML-escape, then allow **bold** -> <strong class=hl>, ==mark== -> <mark>, and tag 未经官方确认."""
    t = E(text)
    t = re.sub(r"\*\*(.+?)\*\*", r'<strong class="hl">\1</strong>', t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    return t.replace("未经官方确认", '<span class="unconf">未经官方确认</span>')

def annotate(h, glossary, used):
    """Wrap the first occurrence (per item; `used` is shared across fields) of each glossary term in
    already-rendered HTML. Only text outside tags is touched; case-insensitive, word boundaries."""
    terms = sorted((g for g in glossary or [] if g.get("term") and g.get("gloss")), key=lambda g: -len(g["term"]))
    if not terms: return h
    parts = re.split(r"(<[^>]+>)", h)
    for i, seg in enumerate(parts):
        if not seg or seg.startswith("<"): continue
        hits = []  # (start, end, gloss) non-overlapping, longest terms first
        for g in terms:
            if g["term"].lower() in used: continue
            for m in re.finditer(r"(?<![\w-])" + re.escape(E(g["term"])) + r"(?![\w-])", seg, re.I):
                if all(m.end() <= x0 or m.start() >= x1 for x0, x1, _ in hits):
                    hits.append((m.start(), m.end(), g["gloss"])); used.add(g["term"].lower()); break
        for x0, x1, gloss in sorted(hits, reverse=True):
            seg = seg[:x0] + f'<span class="gl" tabindex="0" data-gl="{E(gloss)}">{seg[x0:x1]}</span>' + seg[x1:]
        parts[i] = seg
    return "".join(parts)

def write(rel, s):
    path = os.path.join(DOCS, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path) or open(path, encoding="utf-8").read() != s:
        with open(path, "w", encoding="utf-8") as f: f.write(s)

def sync_static():
    dst = os.path.join(DOCS, "assets"); h = hashlib.sha256(); want = set()
    for dp, _, fs in os.walk(STATIC):
        for fn in sorted(fs):
            s = os.path.join(dp, fn); rel = os.path.relpath(s, STATIC); d = os.path.join(dst, rel); want.add(rel)
            data = open(s, "rb").read(); h.update(rel.encode()); h.update(data)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            if not os.path.exists(d) or open(d, "rb").read() != data: shutil.copyfile(s, d)
    for dp, _, fs in os.walk(dst):
        for fn in fs:
            if os.path.relpath(os.path.join(dp, fn), dst) not in want: os.remove(os.path.join(dp, fn))
    return h.hexdigest()[:8]

def main():
    items = load_items()
    news = [i for i in items if i["type"] == "news"]; demos = [i for i in items if i["type"] == "demo"]
    tl = json.load(open(os.path.join(DATA, "timeline.json"), encoding="utf-8"))
    try: state = json.load(open(os.path.join(DATA, "state.json"), encoding="utf-8"))
    except FileNotFoundError: state = {}
    missing = [p for i in items for h in i.get("image_hashes") or [] for p in (blob(h), blob(h, True)) if not os.path.exists(p)]
    if missing: sys.exit("missing blobs/thumbs (run scripts/make_blobs.py --thumbs?):\n  " + "\n  ".join(missing))
    ver = sync_static()
    updated = state.get("last_run_utc", "—")

    # ---- docs/data.json (compact; demos only, newest first) ----
    out = []
    for d in demos:
        imgs = []
        for h in d.get("image_hashes") or []:
            (w, hh), (tw, th) = webp_size(blob(h)), webp_size(blob(h, True))
            imgs.append([h, w, hh, tw, th])
        rec = {"u": d["uid"], "d": d.get("date"), "t": d.get("title"), "m": d.get("model"), "mk": d.get("maker"),
               "a": d.get("author"), "s": d.get("source_url"), "p": d.get("prompt"), "ps": d.get("prompt_source"),
               "partial": (d.get("prompt_status") or "").startswith("partial") or None, "k": model_keys(d), "i": imgs,
               "x": d.get("text"), "xz": d.get("text_zh"), "pz": d.get("prompt_zh"), "g": [[g["term"], g["gloss"]] for g in d.get("glossary") or []]}
        out.append({k: v for k, v in rec.items() if v not in (None, "", [])})
    cnt = {}
    for d in demos:
        for k in model_keys(d): cnt[k] = cnt.get(k, 0) + 1
    payload = {"updated": updated, "keys": [[k, cnt[k]] for k in sorted(cnt, key=KEY_ORDER.index)], "items": out}
    write("data.json", json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    data_ver = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:8]

    # ---- News tab: news items (bullets + labelled sources) merged with timeline.json, newest first ----
    rows = [dict(date=t["date"], model=t["model"], maker=t["maker"], title=None, bullets=[t.get("change_zh") or t["change"]],
                 sources=[{"url": t["source_url"], "label": "", "by": ""}]) for t in tl]
    idx = {(r["date"], r["model"].lower()): r for r in rows}
    for n in news:
        srcs = n.get("sources") or [{"url": u, "label": "", "by": ""} for u in (n.get("source_urls") or [n.get("source_url")]) if u]
        srcs = sorted(srcs, key=lambda x: x.get("label") != "官方")  # official first (stable)
        r = dict(glossary=n.get("glossary"), bullets_zh=n.get("bullets_zh"), title_zh=n.get("title_zh"), lang=n.get("lang"), date=n["date"], model=n["model"], maker=n["maker"], title=n.get("title"), bullets=n.get("bullets") or [n.get("title")], sources=srcs)
        old = idx.get((n["date"], n["model"].lower()))
        if old: old.update(r)
        else: rows.append(r)
    rows.sort(key=lambda r: (r["date"], r["model"]), reverse=True)
    def src_links(srcs):
        out = []
        for i, x in enumerate(srcs):
            lab = x.get("label") or "来源"; by = f' · {E(x["by"])}' if x.get("by") else ""
            cls = " off" if x.get("label") == "官方" else (" com" if x.get("label") == "社区" else "")
            out.append(f'<a class="orig src{cls}" href="{E(x["url"])}" rel="noopener"><span class="src-lab">{E(lab)}</span>{by}{EXT}</a>')
        return '<span class="dot" aria-hidden="true">·</span>'.join(out)
    news_html = ''
    for r in rows:
        head = rich(r["title"]) if r["title"] else E(r["model"])
        used = set(); gl = r.get("glossary"); zh = r.get("bullets_zh")
        if r["title"]: head = annotate(head, gl, used)
        lis = "".join(f'<li>{annotate(rich(x), gl, used)}</li>' for x in r["bullets"])
        zh_block = ""
        if zh:  # pre-written Chinese translation, shown instead of the English when html.show-zh (global 译 toggle)
            zh_block = f'<ul class="points zh-only" lang="zh-CN">{"".join(f"<li>{rich(x)}</li>" for x in zh)}</ul>'
            if r.get("title_zh"): head = f'<span class="en-only">{head}</span><span class="zh-only" lang="zh-CN">{rich(r["title_zh"])}</span>'
        news_html += (f'      <article class="news-item{" rich" if r["title"] else ""}{" has-zh" if zh else ""}"{' lang="en"' if r.get("lang") == "en" else ""}><h2 class="item-title">{head}</h2>'
                      f'<p class="item-meta"><span class="model-tag">{E(r["model"])}</span><span>{E(r["maker"])}</span><span class="dot" aria-hidden="true">·</span><time class="ts">{E(r["date"])}</time></p>'
                      f'<ul class="points{" en-only" if zh else ""}">{lis}</ul>{zh_block}<p class="item-meta srcs">{src_links(r["sources"])}</p></article>\n')
    noscript = "".join(f'<li><a href="{E(d.get("source_url"))}">{E(d.get("title"))}</a> · @{E(d.get("author"))} · {E(d.get("date"))}</li>' for d in demos)
    demos_html = (f'      <nav class="chips" aria-label="按模型筛选" id="chips"></nav>\n'
                  f'      <div class="wall" id="wall" data-src="data.json?v={data_ver}" aria-live="polite"></div>\n'
                  f'      <div id="sentinel" aria-hidden="true"></div>\n'
                  f'      <noscript><ul class="summary-list">{noscript}</ul></noscript>\n')
    body = (f'      <section id="panel-news" class="panel news" role="tabpanel" aria-label="News">\n{news_html}      </section>\n'
            f'      <section id="panel-demos" class="panel demos" role="tabpanel" aria-label="Demos">\n{demos_html}      </section>')
    write("index.html", page("生图模型追踪 · AI ImageGen Tracker", body, ver, "AI 生图模型动态（GPT Image、Nano Banana、Midjourney、FLUX、Seedream 等）与带提示词的精选案例。"))
    write("demos.html", '<!doctype html><meta charset="utf-8"><title>Demos</title><meta http-equiv="refresh" content="0; url=./#demos"><link rel="canonical" href="./#demos"><script>location.replace("./#demos")</script><a href="./#demos">→ Demos</a>\n')

    for s in STALE:
        p = os.path.join(DOCS, s)
        if os.path.isdir(p): shutil.rmtree(p)
        elif os.path.exists(p): os.remove(p)
    print(f"built: {len(rows)} news rows ({len(news)} items + timeline), {len(demos)} demos, data.json {os.path.getsize(os.path.join(DOCS, 'data.json'))} B, assets v={ver}")

if __name__ == "__main__": main()
