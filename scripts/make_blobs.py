#!/usr/bin/env python3
"""Turn downloaded originals into content-addressed blobs (needs Pillow).

  python3 scripts/make_blobs.py path/to/img1.jpg path/to/img2.png ...   # prints one sha256 per input
  python3 scripts/make_blobs.py --thumbs                                 # (re)create any missing thumbs

Full image : docs/images_blobs/<h[:2]>/<h>.webp         max 1600px wide, q=85, h = sha256(full webp bytes)
Thumbnail  : docs/images_blobs/thumbs/<h[:2]>/<h>.webp  max 400px wide,  q=80, keyed by the SAME h
Identical images collapse automatically; existing files are never rewritten.
"""
import glob, hashlib, io, os, sys
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOBS = os.path.join(ROOT, "docs", "images_blobs")

def encode(im, maxw, q):
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6); return buf.getvalue()

def load(path):
    im = ImageOps.exif_transpose(Image.open(path))
    alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    return im.convert("RGBA" if alpha else "RGB")

def put(rel, data):
    p = os.path.join(BLOBS, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p):
        with open(p, "wb") as f: f.write(data)

def thumb_from_full(h):
    put(f"thumbs/{h[:2]}/{h}.webp", encode(load(os.path.join(BLOBS, h[:2], h + ".webp")), 400, 80))

def ingest(path):
    full = encode(load(path), 1600, 85); h = hashlib.sha256(full).hexdigest()
    put(f"{h[:2]}/{h}.webp", full); thumb_from_full(h); return h

if __name__ == "__main__":
    if sys.argv[1:] == ["--thumbs"]:
        n = 0
        for p in glob.glob(os.path.join(BLOBS, "[0-9a-f][0-9a-f]", "*.webp")):
            h = os.path.basename(p)[:-5]
            if not os.path.exists(os.path.join(BLOBS, "thumbs", h[:2], h + ".webp")): thumb_from_full(h); n += 1
        print(f"created {n} thumbs")
    else:
        for a in sys.argv[1:]: print(ingest(a), a)
