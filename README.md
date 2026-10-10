# ImageGen Tracker · AI 生图模型追踪

**🌐 网站 / Site: https://theodoruszq.github.io/imagegen-tracker/** · [News](https://theodoruszq.github.io/imagegen-tracker/#news) · [Demos](https://theodoruszq.github.io/imagegen-tracker/#demos)

This repo tracks (A) releases and major updates of the top AI image-generation models: GPT Image / ChatGPT Images, Nano Banana / Gemini / Imagen, Midjourney, FLUX, Seedream, Grok Imagine, Ideogram, Recraft, Qwen-Image, Hunyuan/Hy Image, Kling/Kolors, and any new SOTA contender. It also collects (B) standout showcase posts from X, preferably ones that share their prompts. GitHub Pages serves it from `main:/docs`.

## Site

A single page (`docs/index.html`) with two centered tabs:

- **News** (`#news`): model releases and updates, newest first. Each item has a bullet summary in the original post's language, with key facts in bold, and labelled source links, 官方 first and then 社区. Older verified milestones from `data/timeline.json` are merged in.
- **Demos** (`#demos`, `#demos/<model>` for a filter): a compact masonry wall of ~220px columns (2 on mobile, up to 6 on desktop) with model filter chips. It renders in batches of 30 as you scroll. Clicking a card opens a lightbox (Esc closes it, ← → navigate, swipe works on mobile) showing the full-size image(s), model/maker, author, date, the full prompt with a copy button, and the original post link. `#<uid>`, e.g. `#x-2107671007029076318`, is the permalink that opens it.
- Demo data comes from one compact file, `docs/data.json`. The wall loads only ~400px thumbnails with `width`/`height` attributes and `loading="lazy"`; the full 1600px webp loads only in the lightbox.
- English help is copied from x-digest: one remembered **中文** switch shows inline Chinese glosses for harder English terms. Visual feel is also borrowed from [theodoruszq/x-digest](https://github.com/theodoruszq/x-digest): its color palette with light/dark theme and its Lato + PingFang font stack (Lato woff2 is vendored in the repo). The layout is the site's own. No CDNs and no external requests.

## Layout

```
data/items.jsonl      one JSON object per line: source of truth + dedup index (schema below)
data/timeline.json    verified historical milestones [{date, model, maker, change, change_zh, source_url, verification}]
data/state.json       {last_run_utc, ..., skipped_uids}; last_run_utc = since-time for the next run
docs/index.html       GENERATED (News + Demos tabs)
docs/data.json        GENERATED compact demo data for the wall/lightbox
docs/demos.html       GENERATED redirect to ./#demos
docs/assets/          GENERATED copy of scripts/static/ (css, js, fonts, icon)
docs/images_blobs/<h[:2]>/<h>.webp          full images (max 1600px wide), stored exactly once
docs/images_blobs/thumbs/<h[:2]>/<h>.webp   thumbnails (max 400px wide), keyed by the same h
images_blobs/README.md                      pointer only (no bytes at repo root)
scripts/make_blobs.py  originals -> full webp + thumb (needs Pillow)
scripts/build.py       data/ -> docs/ (stdlib only, no network, idempotent; never touches images_blobs or .nojekyll)
scripts/static/        css / js / fonts / icon sources
```

## UID rules (no duplicates)

- Demos: `x-<post id>`, using the original post's id (never a repost).
- News: `news-<maker>-<model>-<version>`, lowercase with hyphens (e.g. `news-openai-gpt-image-2`, `news-google-nano-banana-2-1`). Several posts about one release collapse into one item; add them to `sources` instead of creating a new item.
- Before adding, check `data/items.jsonl` and `data/state.json.skipped_uids`. Skip reposts and near-duplicate posts of the same images. `build.py` stops with an error on a duplicate or malformed uid.

## items.jsonl schema

Common: `uid`, `type` (`news`|`demo`), `date` (YYYY-MM-DD, UTC), `model`, `maker`, `author` (X handle, no @), `source_url` (primary/official), `source_urls` [all], `title`, `image_hashes` [sha256], `archived_run`.

News only (no prompt field):
- `title`: a headline in the original post's language.
- `lang`: the source language (`en`, `zh`, ...).
- `bullets` [str]: a complete, faithful summary of the original post(s) **in the original post's language** (English source → English, Chinese source → Chinese; never auto-translate), with wording kept close to the original. Cover what's new, capabilities, specs and parameters, pricing, availability and channels, license and open weights, and links. **Bold the key facts** with `**...**` (price, speed, quality/benchmark gains, resolution, step counts, availability); `==...==` also works for a highlight. The build HTML-escapes everything else. Anything not confirmed by the official source is marked `未经官方确认` in every language, for consistency with the Chinese UI.
- `sources` [{url, label: 官方|社区, by}]: official sources first.
- `notes_internal`: not shown on the site.

Demos only:
- `prompt` (str|null): the full prompt; `null` is shown as 不详.
- `prompt_source`: e.g. the author's self-reply URL; kept out of `prompt` so 复制 copies a clean prompt.
- `prompt_status` (`found` / `partial ...` / `not found`).
- `text`: the original post text.
- `lang` / `prompt_lang`: the language of the post / prompt (`en`, `zh`, ...).
- `metrics`, `created_at`, `summary`: optional.

### English help: inline Chinese glosses (copied from x-digest)

The page stays English-first, with no full translations; do not write `*_zh` translation fields.

- `glossary` [{term, gloss}] on any item with English content: 3–10 harder English words or phrases from the title, bullets, post text or prompt.
  - `term` must be the exact surface form as it appears in the text.
  - `gloss` uses x-digest's format: part of speech plus a short Chinese meaning, e.g. `{"term": "artifact buildup", "gloss": "n. 伪影累积"}`. Allowed prefixes are `n.`, `v.`, `adj.`, `adv.`, `phr.`, `idiom`.
  - Skip trivial words and product names.
- The build marks the first occurrence of each term per item with x-digest's markup: `<span class="g">term</span><span class="g-zh zh-only" lang="zh-Hans"><i>n.</i> 中文</span>`.
- Glosses are hidden by default. The one header switch **中文** (x-digest's `.zh-switch`, remembered in `localStorage` as `igt.zh` = `'1'`) adds `html.show-zh`, which underlines each term and shows its gloss inline.
- There are no hover popovers (same as x-digest), and no runtime translation API.

## Image policy

Download the original media (`pbs.twimg.com/...?name=orig`) and run `python3 scripts/make_blobs.py <files>`:

- **Full image**: WebP, max 1600px wide, quality 85. `h = sha256(final full webp bytes)`, saved to `docs/images_blobs/<h[:2]>/<h>.webp`.
- **Thumbnail**: WebP, max 400px wide, quality 80, saved to `docs/images_blobs/thumbs/<h[:2]>/<h>.webp`.
- Identical images collapse automatically. Videos are not stored (link only); original JPG/MP4 files are never committed.
- Keep it tasteful: leave out demos whose images are suggestive beyond normal fashion photography, and add their uid to `skipped_uids`.

## Build

```
python3 scripts/build.py                  # docs/index.html, docs/data.json, docs/assets/
python3 -m http.server -d docs 8000       # preview at http://localhost:8000/#demos
```

## Cadence

A routine runs twice daily at **09:03 and 21:03 Asia/Shanghai**. Each run searches X since `last_run_utc` with roughly 40–60 read calls (cap 1000/day), adds the new news items and the 3–8 best demos, rebuilds, and pushes one commit.
