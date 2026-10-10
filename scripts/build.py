#!/usr/bin/env python3
"""Regenerate docs/ (static site) from data/.  Stdlib only, no network, idempotent.

Writes docs/index.html, docs/timeline.html, docs/demos.html, docs/items/<uid>.html and
docs/assets/ (copied from scripts/static/).  Never touches docs/images_blobs/ or docs/.nojekyll.
Visual style follows theodoruszq/x-digest (see scripts/static/style.css header).
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

def load_items():
    items, seen = [], set()
    with open(os.path.join(DATA, "items.jsonl"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip(): continue
            it = json.loads(line)
            uid = it.get("uid", "")
            if uid in seen: sys.exit(f"duplicate uid {uid} (line {n})")
            if not re.fullmatch(r"x-\d+|news-[a-z0-9]+(-[a-z0-9.]+)+", uid): sys.exit(f"bad uid {uid!r} (line {n})")
            if it.get("type") not in ("news", "demo"): sys.exit(f"bad type for {uid}")
            seen.add(uid); items.append(it)
    items.sort(key=lambda x: (x.get("date", ""), x["uid"]), reverse=True)
    return items

def model_keys(it):
    m = (it.get("model") or "").lower()
    return [k for k, rx in KEYS if re.search(rx, m)] or ["其他"]

def blob(h): return os.path.join(DOCS, "images_blobs", h[:2], h + ".webp")

def webp_size(path):
    """(w, h) from a WebP header, or None."""
    try:
        with open(path, "rb") as f: b = f.read(30)
        if b[:4] != b"RIFF" or b[8:12] != b"WEBP": return None
        c = b[12:16]
        if c == b"VP8 ": w, h = struct.unpack("<HH", b[26:30]); return w & 0x3FFF, h & 0x3FFF
        if c == b"VP8L": v = struct.unpack("<I", b[21:25])[0]; return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        if c == b"VP8X": return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    except OSError: pass
    return None

def img(h, depth, alt="", cls=""):
    wh = webp_size(blob(h)); dim = f' width="{wh[0]}" height="{wh[1]}"' if wh else ""
    return f'<img{cls} loading="lazy" decoding="async" src="{"../"*depth}images_blobs/{h[:2]}/{h}.webp"{dim} alt="{E(alt)}">'

def page(title, body, active, depth, ver, body_cls, desc=""):
    p = "../" * depth
    tools = [("index", "index.html", "首页"), ("timeline", "timeline.html", "时间线"), ("demos", "demos.html", "案例墙")]
    tb = '<span class="tool-sep" aria-hidden="true">/</span>'.join(
        f'<a class="tool{" on" if k == active else ""}" href="{p}{h}">{l}</a>' for k, h, l in tools)
    tb += '<span class="tool-sep" aria-hidden="true">/</span><button type="button" class="tool" data-toggle-theme><span data-theme-label>深色</span></button>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#141414" media="(prefers-color-scheme: dark)">
  <title>{E(title)} · 生图模型追踪</title>
  <meta name="description" content="{E(desc or 'AI 生图模型发布与精选案例（含提示词），每日两次更新。')}">
  <link rel="icon" href="{p}assets/icon.svg" type="image/svg+xml">
  <link rel="preload" href="{p}assets/fonts/lato-regular.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{p}assets/style.css?v={ver}">
  <script>(function(){{var d=document.documentElement;d.classList.add('js');try{{var t=localStorage.getItem('igt.theme');if(t)d.dataset.theme=t;}}catch(e){{}}}})();</script>
  <script src="{p}assets/site.js?v={ver}" defer></script>
</head>
<body class="{body_cls}">
  <a class="skip-link" href="#main">跳到正文</a>
  <div class="toolbar">{tb}</div>
  <div class="site-shell">
    <main id="main">
{body}
      <div class="row"><div class="rail"></div><footer class="col site-footer"><p>数据来自 <a href="https://x.com">X</a> 公开帖子与官方发布 · 每日 09:03 / 21:03（北京时间）更新 · <a href="https://github.com/theodoruszq/imagegen-tracker">GitHub</a></p></footer></div>
    </main>
  </div>
</body>
</html>
"""

def meta_line(it, depth, with_model=True):
    parts = []
    if with_model: parts.append(f'<span class="model-tag">{E(it.get("model"))}</span>')
    if it.get("author"): parts.append(f'<a class="handle" href="https://x.com/{E(it["author"])}" rel="noopener">@{E(it["author"])}</a>')
    parts.append(f'<span class="ts">{E(it.get("date"))}</span>')
    if it.get("source_url"): parts.append(f'<a class="orig" href="{E(it["source_url"])}" rel="noopener">原帖{EXT}</a>')
    return '<p class="item-meta">' + '<span class="dot" aria-hidden="true">·</span>'.join(parts) + "</p>"

def prompt_block(it, clamp):
    if not it.get("prompt"):
        return '<div class="prompt"><span class="prompt-none">提示词：不详</span></div>'
    status = it.get("prompt_status") or ""
    note = "（部分）" if status.startswith("partial") else ""
    exp = '<button type="button" data-expand aria-expanded="false">展开</button>' if clamp else ""
    return (f'<div class="prompt"><div class="prompt-head"><span>提示词{note}</span><span class="acts">{exp}'
            f'<button type="button" data-copy>复制</button></span></div><pre class="prompt-text">{E(it["prompt"])}</pre></div>')

def card(it, depth=0):
    hs = it.get("image_hashes") or []; href = f'{"../"*depth}items/{E(it["uid"])}.html'
    im = ""
    if hs:
        cnt = f'<span class="count">{len(hs)} 图</span>' if len(hs) > 1 else ""
        im = f'<a class="card-img" href="{href}">{img(hs[0], depth, it.get("title"))}{cnt}</a>'
    return (f'<article class="card" data-models="{E("|".join(model_keys(it)))}">{im}'
            f'<h3 class="item-title"><a href="{href}">{E(it.get("title"))}</a></h3>{meta_line(it, depth)}{prompt_block(it, True)}</article>')

def news_item(it, depth=0):
    return (f'<article class="item"><h3 class="item-title"><a href="{"../"*depth}items/{E(it["uid"])}.html">{E(it.get("title"))}</a></h3>'
            f'{meta_line(it, depth, with_model=False).replace("<p class=\"item-meta\">", "<p class=\"item-meta\"><span>" + E(it.get("maker")) + "</span><span class=\"dot\" aria-hidden=\"true\">·</span>", 1)}</article>')

def row(rail, inner, col_cls="col"):
    return f'      <div class="row"><div class="rail">{rail}</div><div class="{col_cls}">{inner}</div></div>\n'

def write(rel, s, written):
    path = os.path.join(DOCS, rel); os.makedirs(os.path.dirname(path), exist_ok=True); written.add(os.path.normpath(path))
    if not os.path.exists(path) or open(path, encoding="utf-8").read() != s:
        with open(path, "w", encoding="utf-8") as f: f.write(s)

def sync_static():
    dst = os.path.join(DOCS, "assets"); h = hashlib.sha256()
    for dp, _, fs in os.walk(STATIC):
        for fn in sorted(fs):
            s = os.path.join(dp, fn); d = os.path.join(dst, os.path.relpath(s, STATIC))
            data = open(s, "rb").read(); h.update(fn.encode()); h.update(data)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            if not os.path.exists(d) or open(d, "rb").read() != data: shutil.copyfile(s, d)
    return h.hexdigest()[:8]

def main():
    items = load_items()
    news = [i for i in items if i["type"] == "news"]; demos = [i for i in items if i["type"] == "demo"]
    tl = json.load(open(os.path.join(DATA, "timeline.json"), encoding="utf-8"))
    try: state = json.load(open(os.path.join(DATA, "state.json"), encoding="utf-8"))
    except FileNotFoundError: state = {}
    missing = [h for i in items for h in i.get("image_hashes") or [] if not os.path.exists(blob(h))]
    if missing: sys.exit(f"missing blobs: {missing}")
    ver = sync_static(); W = set()

    # index
    b = row("", f'<header class="archive-header"><h1>生图模型追踪</h1><p>追踪主流 AI 生图模型的发布与重大更新，并收集 X 上带提示词的精选案例。'
                f'共 {len(news)} 条动态、{len(demos)} 个案例；最近更新 {E(state.get("last_run_utc", "—"))}（UTC）。</p></header>', "col")
    b += row('<h2 class="rail-label">模型动态</h2>', "".join(news_item(i) for i in news[:10]) +
             '<p class="entry-meta" style="padding-top:10px"><a href="timeline.html">完整时间线 →</a></p>', "col section")
    b += row('<h2 class="rail-label">最新案例</h2>', f'<div class="wall">{"".join(card(i) for i in demos[:8])}</div>'
             '<p class="entry-meta" style="padding:0 20px"><a href="demos.html">全部案例 →</a></p>', "col")
    write("index.html", page("首页", b, "index", 0, ver, "page-index"), W)

    # timeline (timeline.json + news items not already listed)
    rows = [dict(date=t["date"], model=t["model"], maker=t["maker"], change=t["change"], url=t["source_url"], link=None) for t in tl]
    have = {(r["date"], r["model"].lower()) for r in rows}
    for n in news:
        if (n["date"], n["model"].lower()) not in have:
            rows.append(dict(date=n["date"], model=n["model"], maker=n["maker"], change=n["title"], url=n["source_url"], link=f"items/{n['uid']}.html"))
    rows.sort(key=lambda r: r["date"], reverse=True)
    b = row("", '<header class="archive-header"><h1>SOTA 时间线</h1><p>仅收录有可核实来源的节点，日期为 UTC。</p></header>')
    for year in sorted({r["date"][:4] for r in rows}, reverse=True):
        inner = "".join(
            f'<article class="tl-item"><div class="tl-date">{E(r["date"])}</div><div><h3 class="item-title">'
            + (f'<a href="{E(r["link"])}">{E(r["model"])}</a>' if r["link"] else E(r["model"]))
            + f'</h3><p class="item-meta"><span>{E(r["maker"])}</span><span class="dot" aria-hidden="true">·</span><a class="orig" href="{E(r["url"])}" rel="noopener">来源{EXT}</a></p><p>{E(r["change"])}</p></div></article>'
            for r in rows if r["date"][:4] == year)
        b += row(f'<h2 class="rail-label" id="y{year}"><a href="#y{year}">{year}</a></h2>', inner, "col section")
    write("timeline.html", page("SOTA 时间线", b, "timeline", 0, ver, "page-timeline"), W)

    # demo wall (masonry via CSS columns) + filter chips
    cnt = {}
    for d in demos:
        for k in model_keys(d): cnt[k] = cnt.get(k, 0) + 1
    chips = f'<button type="button" class="chip on" data-k="" aria-pressed="true">全部<span class="n">{len(demos)}</span></button>' + "".join(
        f'<button type="button" class="chip" data-k="{E(k)}" aria-pressed="false">{E(k)}<span class="n">{cnt[k]}</span></button>'
        for k in sorted(cnt, key=KEY_ORDER.index))
    b = (f'      <header class="archive-header"><h1>案例墙</h1><p>X 上的精选生图案例，附提示词（可展开、复制）。按模型筛选：</p></header>\n'
         f'      <nav class="chips" aria-label="按模型筛选">{chips}</nav>\n      <div class="wall">{"".join(card(d) for d in demos)}</div>\n')
    write("demos.html", page("案例墙", b, "demos", 0, ver, "page-wall"), W)

    # detail pages
    for it in items:
        srcs = it.get("source_urls") or [it.get("source_url")]
        links = "<br>".join(f'<a href="{E(u)}" rel="noopener">{E(u)}</a>' for u in srcs if u)
        facts = [("类型", "精选案例" if it["type"] == "demo" else "模型动态"), ("日期", E(it.get("date"))), ("模型", E(it.get("model"))),
                 ("厂商", E(it.get("maker"))),
                 ("作者", f'<a href="https://x.com/{E(it.get("author"))}" rel="noopener">@{E(it.get("author"))}</a>' if it.get("author") else "不详"),
                 ("来源", links)]
        if it.get("metrics"): facts.append(("数据", E(it["metrics"])))
        facts.append(("UID", f'<code>{E(it["uid"])}</code>'))
        dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)
        back = ("../demos.html", "← 案例墙") if it["type"] == "demo" else ("../timeline.html", "← 时间线")
        body = (f'<article class="post"><a class="back-link" href="{back[0]}">{back[1]}</a><h1>{E(it.get("title"))}</h1>{meta_line(it, 1)}'
                f'<dl class="facts">{dl}</dl>')
        if it.get("summary"): body += f'<h2>摘要</h2><p>{E(it["summary"])}</p>'
        body += "<h2>提示词</h2>" + prompt_block(it, False)
        src = it.get("prompt_source") or (it.get("prompt_status") if it["type"] == "demo" else None)
        if src: body += f'<p class="entry-meta" style="white-space:normal;margin-top:6px">提示词来源：{E(src)}</p>'
        if it.get("text"): body += f'<h2>原帖文字</h2><blockquote class="quote">{E(it["text"])}</blockquote>'
        hs = it.get("image_hashes") or []
        if hs: body += '<h2>图片</h2><div class="gallery">' + "".join(f'<a href="../images_blobs/{h[:2]}/{h}.webp">{img(h, 1, it.get("title"))}</a>' for h in hs) + "</div>"
        write(f"items/{it['uid']}.html", page(it.get("title") or it["uid"], row(f'<span class="rail-label">{E(it.get("date", "")[:7])}</span>', body), "", 1, ver, "page-item", it.get("summary") or ""), W)

    # prune stale generated pages (docs/items/*.html only; never blobs or .nojekyll)
    idir = os.path.join(DOCS, "items")
    for fn in os.listdir(idir):
        p = os.path.normpath(os.path.join(idir, fn))
        if fn.endswith(".html") and p not in W: os.remove(p)
    print(f"built: {len(news)} news, {len(demos)} demos, {len(rows)} timeline rows, assets v={ver}")

if __name__ == "__main__": main()
