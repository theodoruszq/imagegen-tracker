# ImageGen Tracker · AI 生图模型追踪

Tracks (A) releases and major updates of the top AI image-generation models (GPT Image / ChatGPT Images, Nano Banana / Gemini / Imagen, Midjourney, FLUX, Seedream, Grok Imagine, Ideogram, Recraft, Qwen-Image, Hunyuan/Hy Image, Kling/Kolors, plus any new SOTA contender) and (B) standout showcase posts from X, preferably ones that share their prompts.

Site: https://theodoruszq.github.io/imagegen-tracker/ (GitHub Pages, `main:/docs`).

## Layout

```
data/items.jsonl        one JSON object per line: the source of truth and dedup index
data/timeline.json      verified SOTA history: [{date, model, maker, change, source_url, verification}]
data/state.json         {last_run_utc, ..., skipped_uids}; last_run_utc is the since-time for the next run
docs/                   GENERATED static site (do not hand-edit, except images_blobs/ and .nojekyll)
docs/images_blobs/<first 2 hex of sha256>/<sha256>.webp   all images, stored exactly once
images_blobs/README.md  pointer only; no image bytes live at the repo root
scripts/build.py        regenerates docs/ from data/ (stdlib Python, no network, idempotent)
```

Images are stored once, under `docs/images_blobs/`, so Pages serves them directly and the bytes are never duplicated.

## UID rules (no duplicates)

- Demos: `x-<post id>`, using the original post's id (never a repost).
- News: `news-<maker>-<model>-<version>`, lowercase with hyphens (e.g. `news-openai-gpt-image-2`, `news-google-nano-banana-2-1`). Several posts about one release collapse into one item; append extra links to `source_urls` instead of adding a new item.
- Before adding anything, check `data/items.jsonl` and `data/state.json.skipped_uids`. Skip reposts and near-duplicate posts of the same images. Duplicate images collapse automatically because blobs are content-addressed.

## items.jsonl schema

| field | type | notes |
|---|---|---|
| uid | str | see rules above |
| type | `news` \| `demo` | |
| date | `YYYY-MM-DD` | UTC date of the post or announcement |
| model | str | model(s) involved, free text |
| maker | str | company; `multiple` for multi-model demos |
| author | str | X handle without @ |
| source_url | str | primary link |
| source_urls | [str] | all links (news: official post + coverage) |
| title | str | one-line description |
| summary | str | notes, caveats, why it matters |
| prompt | str \| null | full prompt if found (author's post or self-replies), else null (shown as 不详) |
| prompt_status | str | demos: `found`, `partial`, `not found`, plus detail |
| text | str \| null | original post text (demos) |
| image_hashes | [sha256] | each maps to `docs/images_blobs/<h[:2]>/<h>.webp` |
| created_at, metrics, archived_run | str | optional |

## Image policy

Download the original media (`pbs.twimg.com/...?name=orig`) and convert it to WebP (Pillow, max 1600 px wide, quality 85). `sha256` is computed over the **final webp bytes**, and the file is saved as `docs/images_blobs/<h[:2]>/<h>.webp`. Videos are not stored (link only). Keep content tasteful: leave out demos whose images are suggestive beyond normal fashion photography.

## Build

```
python3 scripts/build.py          # regenerates docs/*.html, docs/items/, docs/assets/
python3 -m http.server -d docs 8000   # local preview
```

## Cadence

A routine runs twice daily at **09:03 and 21:03 Asia/Shanghai** (every day). Each run searches X since `last_run_utc` with roughly 40–60 read calls (cap 1000/day), adds the new news items and the 3–8 best demos, rebuilds, and commits.
