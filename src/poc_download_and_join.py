"""
POC: Fully reproducible pipeline for Amazon Reviews v2 (Sports_and_Outdoors).

Pipeline:
- downloads the Sports_and_Outdoors reviews (5-core) and metadata files
- decompresses the .json.gz files
- filters product metadata by brand (e.g., brand == "Coleman")
- collects corresponding asin values
- streams and joins reviews via shared key asin (only filtered asins)
- keeps reviews with non-empty reviewText
- outputs final joined corpus in JSONL format

Selected fields:
- Review: asin, overall, reviewText
- Metadata: asin, title, price, description, rank, imageURL, cat_l1–cat_l5

Run:
    python src/poc_download_and_join.py --limit 100
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple


REVIEWS_URL = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/Sports_and_Outdoors_5.json.gz"
META_URL = "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/metaFiles2/meta_Sports_and_Outdoors.json.gz"


def open_text_auto(path: Path) -> TextIO:
    """Open .json or .json.gz as text (utf-8)."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def download(url: str, dest: Path, timeout: int = 60) -> None:
    """Download a URL to dest with a minimal progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size > 0:
        print(f"[SKIP] {dest} already exists.")
        return

    print(f"[DOWN] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (POC downloader)"})

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        total = resp.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None

        tmp = dest.with_suffix(dest.suffix + ".part")
        done = 0
        start = time.time()
        last = 0.0

        with open(tmp, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)

                now = time.time()
                if now - last >= 0.25:
                    if total_bytes:
                        pct = done * 100.0 / total_bytes
                        sys.stdout.write(f"\r      {pct:6.2f}% ({done}/{total_bytes} bytes)")
                    else:
                        sys.stdout.write(f"\r      {done} bytes")
                    sys.stdout.flush()
                    last = now

        sys.stdout.write("\n")
        sys.stdout.flush()

    tmp.replace(dest)
    elapsed = max(time.time() - start, 1e-6)
    print(f"[OK ] Saved {dest} ({dest.stat().st_size} bytes) in {elapsed:.1f}s")


def gunzip(gz_path: Path, out_path: Path) -> None:
    """Decompress gz_path -> out_path (streaming)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"[SKIP] {out_path} already exists.")
        return

    print(f"[EXT] {gz_path.name} -> {out_path.name}")
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    with gzip.open(gz_path, "rb") as fin, open(tmp, "wb") as fout:
        shutil.copyfileobj(fin, fout, length=1024 * 1024)
    tmp.replace(out_path)
    print(f"[OK ] Extracted {out_path} ({out_path.stat().st_size} bytes)")


def _norm_brand(x: Any) -> str:
    if x is None:
        return ""
    if not isinstance(x, str):
        x = str(x)
    return x.strip().lower()


def safe_cat_level(categories: Any, level: int) -> Optional[str]:
    """Try to read category level from SNAP-style nested categories."""
    if isinstance(categories, list) and categories:
        first = categories[0]
        if isinstance(first, list) and len(first) > level and isinstance(first[level], str):
            return first[level]
        if all(isinstance(x, str) for x in categories) and len(categories) > level:
            return categories[level]
    return None


def _extract_image_urls(obj: Dict[str, Any]) -> List[str]:
    """
    Robustly extract image URL list across common meta schemas.
    Prefer imageURLHighRes > imageURL > imUrl.
    """
    candidates = [
        obj.get("imageURLHighRes"),
        obj.get("imageURL"),
        obj.get("imUrl"),
        obj.get("imURL"),
        obj.get("imgUrl"),
    ]
    for c in candidates:
        if isinstance(c, list):
            return [x for x in c if isinstance(x, str) and x.strip()]
        if isinstance(c, str) and c.strip():
            return [c.strip()]
    return []


def _extract_description(obj: Dict[str, Any]) -> Optional[str]:
    """
    Meta description can be:
    - str
    - list[str]
    - None
    """
    d = obj.get("description")
    if isinstance(d, str):
        s = d.strip()
        return s if s else None
    if isinstance(d, list):
        parts = [x.strip() for x in d if isinstance(x, str) and x.strip()]
        if parts:
            return " ".join(parts)
    return None


def _extract_rank(obj: Dict[str, Any]) -> Optional[str]:
    """
    Rank might be string or list/other; keep a readable string if possible.
    """
    r = obj.get("rank")
    if isinstance(r, str):
        s = r.strip()
        return s if s else None
    if isinstance(r, list):
        parts = [x.strip() for x in r if isinstance(x, str) and x.strip()]
        if parts:
            return "; ".join(parts)
    if r is not None:
        s = str(r).strip()
        return s if s else None
    return None


def build_brand_meta_index(
    meta_json_or_gz: Path,
    brand: str,
) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """
    Index metadata by asin, but only keep products with matching brand.
    Returns (meta_index, asin_set).
    """
    idx: Dict[str, Dict[str, Any]] = {}
    asin_set: Set[str] = set()

    total = 0
    with open_text_auto(meta_json_or_gz) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            obj = json.loads(line)

            asin = obj.get("asin")
            if not asin:
                continue

            brand_val = _norm_brand(obj.get("brand"))
            if brand_val != _norm_brand(brand):
                continue

            # Sports_and_Outdoors meta often uses 'category' (list[str]); sometimes 'categories'
            cats = obj.get("category") or obj.get("categories")

            # If it is list[str], trim to first 5 levels
            if isinstance(cats, list) and all(isinstance(x, str) for x in cats):
                cats = cats[:5]

            rec = {
                "asin": asin,
                "title": obj.get("title"),
                "price": obj.get("price"),
                "description": _extract_description(obj),
                "rank": _extract_rank(obj),
                "imageURL": _extract_image_urls(obj),
                "cat_l1": safe_cat_level(cats, 0),
                "cat_l2": safe_cat_level(cats, 1),
                "cat_l3": safe_cat_level(cats, 2),
                "cat_l4": safe_cat_level(cats, 3),
                "cat_l5": safe_cat_level(cats, 4),
            }

            idx[asin] = rec
            asin_set.add(asin)

    print(f"[META] Read {total} lines, kept {len(idx)} products for brand={brand!r}.")
    return idx, asin_set


def join_to_jsonl(
    reviews_json_or_gz: Path,
    meta_index: Dict[str, Dict[str, Any]],
    asin_set: Set[str],
    out_jsonl: Path,
    limit: int,
) -> None:
    """
    Stream reviews, join on asin (only for asins in asin_set),
    keep only non-empty reviewText, and write JSONL.

    Each output record is assigned a deterministic review_id
    based on streaming order.
    """
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    scanned = 0
    eligible_asin = 0
    empty_text = 0
    matched = 0
    written = 0

    review_id = 0

    with open_text_auto(reviews_json_or_gz) as fin, out_jsonl.open("w", encoding="utf-8") as fout:
        for line in fin:
            scanned += 1
            if written >= limit:
                break

            line = line.strip()
            if not line:
                continue
            total += 1

            r = json.loads(line)
            asin = r.get("asin")
            if not asin or asin not in asin_set:
                continue
            eligible_asin += 1

            review_text = r.get("reviewText")
            if not isinstance(review_text, str) or not review_text.strip():
                empty_text += 1
                continue

            meta = meta_index.get(asin)
            if meta is None:
                continue

            rec = {
                # Primary Key
                "review_id": review_id,

                # review fields
                "asin": asin,
                "overall": r.get("overall"),
                "reviewText": review_text.strip(),

                # metadata fields
                "title": meta.get("title"),
                "price": meta.get("price"),
                "description": meta.get("description"),
                "rank": meta.get("rank"),
                "imageURL": meta.get("imageURL"),
                "cat_l1": meta.get("cat_l1"),
                "cat_l2": meta.get("cat_l2"),
                "cat_l3": meta.get("cat_l3"),
                "cat_l4": meta.get("cat_l4"),
                "cat_l5": meta.get("cat_l5"),
            }

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

            review_id += 1
            written += 1
            matched += 1

    print(f"[REV ] Scanned {scanned} lines, parsed {total} non-empty JSON lines.")
    print(f"[FILT] Reviews with asin in selected brand set: {eligible_asin}")
    print(f"[FILT] Dropped empty reviewText: {empty_text}")
    print(f"[JOIN] Wrote {written} joined lines -> {out_jsonl} (matched meta={matched})")


def main() -> None:
    ap = argparse.ArgumentParser(description="POC: download + extract + brand-filter + join (Amazon v2 Sports_and_Outdoors).")
    ap.add_argument("--out", default="data", help="Base output dir (default: data)")
    ap.add_argument("--brand", default="Coleman", help='Brand filter (default: "Coleman")')
    ap.add_argument("--limit", type=int, default=2000, help="Max joined records to write (default: 2000)")
    ap.add_argument("--no-extract", action="store_true", help="Do not decompress .gz to .json")
    ap.add_argument("--timeout", type=int, default=60, help="Download timeout seconds (default: 60)")
    args = ap.parse_args()

    base = Path(args.out)
    raw = base / "raw"
    processed = base / "processed"

    reviews_gz = raw / "Sports_and_Outdoors_5.json.gz"
    meta_gz = raw / "meta_Sports_and_Outdoors.json.gz"
    reviews_json = raw / "Sports_and_Outdoors_5.json"
    meta_json = raw / "meta_Sports_and_Outdoors.json"

    brand_clean = args.brand.strip().title().replace(" ", "")
    joined_jsonl = processed / f"sports_outdoors_joined_{brand_clean}.jsonl"

    print("=== POC: Amazon v2 Sports_and_Outdoors download + brand-filter + join ===")
    print(f"Brand filter: {args.brand!r}")

    # 1) Download
    download(REVIEWS_URL, reviews_gz, timeout=args.timeout)
    download(META_URL, meta_gz, timeout=args.timeout)

    # 2) Extract
    if not args.no_extract:
        gunzip(reviews_gz, reviews_json)
        gunzip(meta_gz, meta_json)

    # 3) Build brand meta index + asin set
    meta_source = meta_json if (not args.no_extract and meta_json.exists()) else meta_gz
    reviews_source = reviews_json if (not args.no_extract and reviews_json.exists()) else reviews_gz

    meta_index, asin_set = build_brand_meta_index(meta_source, brand=args.brand)

    # 4) Stream join (only selected asins, keep non-empty reviewText)
    join_to_jsonl(
        reviews_json_or_gz=reviews_source,
        meta_index=meta_index,
        asin_set=asin_set,
        out_jsonl=joined_jsonl,
        limit=max(args.limit, 1),
    )

    print("Done.")


if __name__ == "__main__":
    main()