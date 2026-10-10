#!/usr/bin/env python3
"""Regenerate docs/ (static site) from data/. Stdlib only, no network, idempotent.
Never touches docs/images_blobs/ or docs/.nojekyll."""
import json, os, html, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); DOCS = os.path.join(ROOT, "docs")
E = lambda s: html.escape("" if s is None else str(s), quote=True)

def load_items():
    items, seen = [], set()
    with open(os.path.join(DATA, "items.jsonl"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            it = json.loads(line)
            if it["uid"] in seen: sys.exit(f"duplicate uid {it['uid']} (line {n})")
            if not re.fullmatch(r"x-\d+|news-[a-z0-9]+(-[a-z0-9]+)+", it["uid"]): sys.exit(f"bad uid {it['uid']}")
            seen.add(it["uid"]); items.append(it)
    items.sort(key=lambda x: (x.get("date", ""), x["uid"]), reverse=True)
    return items

CSS = """*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;color:#1d1d1f;background:#f6f7f9;line-height:1.6}
a{color:#0a58ca;text-decoration:none}a:hover{text-decoration:underline}
header{background:#111827;color:#fff;padding:12px 20px;display:flex;flex-wrap:wrap;gap:16px;align-items:center}
header .brand{font-weight:700;font-size:18px;color:#fff}header nav a{color:#d1d5db;margin-right:14px}header nav a.on{color:#fff;font-weight:600}
main{max-width:1180px;margin:0 auto;padding:20px}h1{font-size:24px;margin:8px 0 16px}h2{font-size:19px;margin:28px 0 12px}
.muted{color:#6b7280;font-size:13px}.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:10px;padding:0 8px;font-size:12px;margin-right:4px}
.news{list-style:none;padding:0;margin:0}.news li{background:#fff;border-radius:10px;padding:12px 14px;margin-bottom:10px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;background:#e5e7eb;display:block}.card .b{padding:10px 12px}.card .t{font-weight:600;font-size:14px;color:#111}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}.chip{border:1px solid #d1d5db;background:#fff;border-radius:16px;padding:4px 12px;cursor:pointer;font-size:13px}.chip.on{background:#111827;color:#fff;border-color:#111827}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #eee;font-size:14px;vertical-align:top}th{background:#f3f4f6}
.detail dl{display:grid;grid-template-columns:90px 1fr;gap:6px 12px;background:#fff;padding:14px;border-radius:10px}.detail dt{color:#6b7280}.detail dd{margin:0;word-break:break-word}
pre{background:#0f172a;color:#e2e8f0;padding:14px;border-radius:10px;white-space:pre-wrap;word-break:break-word;font-size:13px;position:relative}
.copy{float:right;margin-bottom:6px;border:0;background:#2563eb;color:#fff;border-radius:6px;padding:4px 10px;cursor:pointer}
.imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}.imgs img{width:100%;border-radius:10px;background:#e5e7eb}
.text{background:#fff;padding:14px;border-radius:10px;white-space:pre-wrap}footer{text-align:center;color:#9ca3af;font-size:12px;padding:30px}
@media(max-width:600px){main{padding:12px}.detail dl{grid-template-columns:70px 1fr}}"""

def page(title, body, active, depth=0):
    p = "../" * depth
    nav = "".join(f'<a href="{p}{href}" class="{"on" if k==active else ""}">{lbl}</a>'
                  for k, href, lbl in [("index","index.html","首页"),("timeline","timeline.html","SOTA 时间线"),("demos","demos.html","案例墙")])
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · 生图模型追踪</title><link rel="stylesheet" href="{p}assets/style.css"></head><body>
<header><a class="brand" href="{p}index.html">🎨 生图模型追踪</a><nav>{nav}</nav></header><main>{body}</main>
<footer>数据来自 X 公开帖子与官方发布 · 每日 09:03 / 21:03（北京时间）更新 · 由 scripts/build.py 生成</footer></body></html>"""

def img_src(h, depth): return f'{"../"*depth}images_blobs/{h[:2]}/{h}.webp'

def card(it, depth=0):
    hs = it.get("image_hashes") or []
    im = f'<img loading="lazy" src="{img_src(hs[0],depth)}" alt="{E(it.get("title"))}">' if hs else ""
    pr = "有提示词" if it.get("prompt") else "无提示词"
    return f"""<a class="card" data-models="{E(" | ".join(model_keys(it)))}" href="{"../"*depth}items/{E(it['uid'])}.html">{im}<div class="b">
<div class="t">{E(it.get('title'))}</div><div class="muted">@{E(it.get('author'))} · {E(it.get('date'))} · {pr}</div></div></a>"""

KEYS = [("GPT Image","gpt image|gpt-image|chatgpt images|gpt 2\\.5|gpt2\\.5"),("Nano Banana","nano banana"),("Midjourney","midjourney"),
        ("FLUX","flux"),("Seedream","seedream"),("Grok Imagine","grok imagine"),("Ideogram","ideogram"),("Recraft","recraft"),
        ("Qwen-Image","qwen"),("Hunyuan/Hy","hunyuan|hy image"),("Kling/Kolors","kling|kolors")]
def model_keys(it):
    m = (it.get("model") or "").lower()
    ks = [k for k, rx in KEYS if re.search(rx, m)]
    return ks or ["其他"]

def news_li(it, depth=0):
    return f'<li><span class="tag">{E(it.get("maker"))}</span><b><a href="{"../"*depth}items/{E(it["uid"])}.html">{E(it.get("model"))}</a></b> <span class="muted">{E(it.get("date"))}</span><div>{E(it.get("title"))}</div></li>'

def write(rel, s):
    path = os.path.join(DOCS, rel); os.makedirs(os.path.dirname(path), exist_ok=True)
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != s:
        with open(path, "w", encoding="utf-8") as f: f.write(s)

def main():
    items = load_items()
    news = [i for i in items if i["type"] == "news"]; demos = [i for i in items if i["type"] == "demo"]
    tl = json.load(open(os.path.join(DATA, "timeline.json"), encoding="utf-8"))
    try: state = json.load(open(os.path.join(DATA, "state.json"), encoding="utf-8"))
    except FileNotFoundError: state = {}
    write("assets/style.css", CSS)
    # index
    body = f"""<h1>AI 生图模型追踪</h1><p class="muted">共 {len(news)} 条模型动态、{len(demos)} 个精选案例 · 最近更新（UTC）：{E(state.get('last_run_utc','—'))}</p>
<h2>最新模型动态</h2><ul class="news">{''.join(news_li(i) for i in news[:10])}</ul>
<h2>最新精选案例 <a class="muted" href="demos.html">全部 →</a></h2><div class="grid">{''.join(card(i) for i in demos[:12])}</div>"""
    write("index.html", page("首页", body, "index"))
    # timeline: merge timeline.json + news items not already there
    rows = [dict(date=t["date"], model=t["model"], maker=t["maker"], change=t["change"], url=t["source_url"], link=None) for t in tl]
    have = {(r["date"], r["model"].lower()) for r in rows}
    for n in news:
        if (n["date"], n["model"].lower()) not in have:
            rows.append(dict(date=n["date"], model=n["model"], maker=n["maker"], change=n["title"], url=n["source_url"], link=f"items/{n['uid']}.html"))
    rows.sort(key=lambda r: r["date"], reverse=True)
    tr = "".join(f'<tr><td>{E(r["date"])}</td><td><b>{E(r["model"])}</b>{" · <a href=%s>详情</a>" % E(r["link"]) if r["link"] else ""}</td><td>{E(r["maker"])}</td><td>{E(r["change"])}</td><td><a href="{E(r["url"])}" target="_blank" rel="noopener">来源</a></td></tr>' for r in rows)
    write("timeline.html", page("SOTA 时间线", f'<h1>SOTA 时间线</h1><p class="muted">仅收录可核实来源的节点；日期为 UTC。</p><div style="overflow-x:auto"><table><tr><th>日期</th><th>模型</th><th>厂商</th><th>变化</th><th>来源</th></tr>{tr}</table></div>', "timeline"))
    # demo wall
    keys = sorted({k for d in demos for k in model_keys(d)}, key=lambda k: [x for x, _ in KEYS].index(k) if k in [x for x,_ in KEYS] else 99)
    chips = '<button class="chip on" data-k="">全部</button>' + "".join(f'<button class="chip" data-k="{E(k)}">{E(k)}</button>' for k in keys)
    js = """<script>document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');const k=c.dataset.k;document.querySelectorAll('.card').forEach(el=>{el.style.display=(!k||el.dataset.models.split(' | ').includes(k))?'':'none'})})</script>"""
    write("demos.html", page("案例墙", f'<h1>案例墙</h1><p class="muted">按模型筛选（同一帖子可能涉及多个模型）</p><div class="chips">{chips}</div><div class="grid">{"".join(card(d) for d in demos)}</div>{js}', "demos"))
    # detail pages
    copyjs = """<script>document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(document.getElementById(b.dataset.t).innerText).then(()=>{b.textContent='已复制';setTimeout(()=>b.textContent='复制',1500)})})</script>"""
    for it in items:
        srcs = it.get("source_urls") or [it.get("source_url")]
        links = "<br>".join(f'<a href="{E(u)}" target="_blank" rel="noopener">{E(u)}</a>' for u in srcs if u)
        pr = f'<button class="copy" data-t="p">复制</button><pre id="p">{E(it["prompt"])}</pre>' if it.get("prompt") else '<p>不详</p>'
        imgs = "".join(f'<a href="../{img_src(h,0)}" target="_blank"><img loading="lazy" src="{img_src(h,1)}" alt=""></a>' for h in it.get("image_hashes") or [])
        txt = f'<h2>原帖文字</h2><div class="text">{E(it["text"])}</div>' if it.get("text") else ""
        body = f"""<div class="detail"><h1>{E(it.get('title'))}</h1><dl>
<dt>类型</dt><dd>{'模型动态' if it['type']=='news' else '精选案例'}</dd><dt>日期</dt><dd>{E(it.get('date'))}</dd>
<dt>模型</dt><dd>{E(it.get('model'))}</dd><dt>厂商</dt><dd>{E(it.get('maker'))}</dd>
<dt>作者</dt><dd><a href="https://x.com/{E(it.get('author'))}" target="_blank" rel="noopener">@{E(it.get('author'))}</a></dd>
<dt>原帖</dt><dd>{links}</dd>{f"<dt>数据</dt><dd>{E(it['metrics'])}</dd>" if it.get('metrics') else ''}
<dt>摘要</dt><dd>{E(it.get('summary'))}</dd><dt>UID</dt><dd><code>{E(it['uid'])}</code></dd></dl>
<h2>提示词</h2>{pr}{txt}{'<h2>图片</h2><div class="imgs">'+imgs+'</div>' if imgs else ''}</div>{copyjs}"""
        write(f"items/{it['uid']}.html", page(it.get("title") or it["uid"], body, "", depth=1))
    # remove stale item pages (only within docs/items)
    keep = {f"{i['uid']}.html" for i in items}
    for fn in os.listdir(os.path.join(DOCS, "items")):
        if fn.endswith(".html") and fn not in keep: os.remove(os.path.join(DOCS, "items", fn))
    # verify referenced blobs exist
    missing = [h for i in items for h in i.get("image_hashes") or [] if not os.path.exists(os.path.join(DOCS, "images_blobs", h[:2], h + ".webp"))]
    if missing: sys.exit(f"missing blobs: {missing}")
    print(f"built: {len(news)} news, {len(demos)} demos, {len(rows)} timeline rows")

if __name__ == "__main__": main()
