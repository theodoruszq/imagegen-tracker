# ImageGen Tracker

Tracking top AI image-generation models and standout showcase cases from X.

- `data/items.jsonl` — one JSON object per line. `uid` is unique: `x-<post id>` for demos, `news-<maker>-<model>-<version>` for releases.
- `data/timeline.json` — SOTA model history.
- `images_blobs/<first 2 hex of sha256>/<sha256>.webp` — content-addressed images (webp, max ~1600px wide).
- `docs/` — generated static site served by GitHub Pages.
- `scripts/` — build scripts that regenerate `docs/` from `data/`.
