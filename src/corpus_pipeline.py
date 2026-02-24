# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python [conda env:base] *
#     language: python
#     name: conda-base-py
# ---

# %%
"""
Corpus Construction Pipeline for Amazon Reviews v2 (Sports_and_Outdoors).

Pipeline:
- download Sports_and_Outdoors reviews (5-core) and metadata dumps
- decompress .json.gz -> .json (REQUIRED; always extracts for byte-offset resume)
- filter product metadata by brand (e.g., brand == "Coleman") to collect ASINs
- stream and join reviews on ASIN (only selected ASINs)
- drop reviews with empty reviewText
- write final merged corpus in JSONL format

Stop & restart (resume) support:
- Download and extraction are idempotent (skip if outputs already exist).
- Join supports checkpointing (byte offset in decompressed reviews .json).
  Use --resume to continue from the last checkpoint and append to the output JSONL.
- Use --reset to delete existing output + checkpoint and rebuild from scratch.

Selected fields:
- Review: review_id, asin, overall, reviewText
- Metadata: asin, title, price, description, rank, imageURL, cat_l1–cat_l5

Run (full corpus):
    python src/corpus_pipeline.py --brand Coleman --resume

Run (small test):
    python src/corpus_pipeline.py --brand Coleman --limit 1000 --resume

Test resume:
    python src/corpus_pipeline.py --brand Coleman --resume
    # Ctrl+C during join
    python src/corpus_pipeline.py --brand Coleman --resume
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple


REVIEWS_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/"
    "categoryFilesSmall/Sports_and_Outdoors_5.json.gz"
)
META_URL = (
    "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/"
    "metaFiles2/meta_Sports_and_Outdoors.json.gz"
)


# -----------------------------
# IO helpers
# -----------------------------
def open_text(path: Path) -> TextIO:
    """Open a text file (utf-8) with robust error handling."""
    return path.open("r", encoding="utf-8", errors="replace")


def download(url: str, dest: Path, timeout: int = 60) -> None:
    """Download a URL to dest with a minimal progress indicator."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size > 0:
        print(f"[SKIP] {dest} already exists.")
        return

    print(f"[DOWN] {url}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Corpus pipeline downloader)"},
    )

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
    """Decompress gz_path -> out_path (streaming). Always extracts for resume support."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"[SKIP] {out_path} already exists.")
        return

    if not gz_path.exists():
        raise FileNotFoundError(f"Missing input: {gz_path}")

    print(f"[EXT] {gz_path.name} -> {out_path.name}")
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    with gzip.open(gz_path, "rb") as fin, open(tmp, "wb") as fout:
        shutil.copyfileobj(fin, fout, length=1024 * 1024)
    tmp.replace(out_path)
    print(f"[OK ] Extracted {out_path} ({out_path.stat().st_size} bytes)")


# -----------------------------
# Parsing helpers
# -----------------------------
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
    """Robustly extract image URL list across common meta schemas."""
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
    """Meta description can be: str | list[str] | None."""
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
    """Rank might be string or list/other; keep a readable string if possible."""
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


# -----------------------------
# Checkpointing (resume)
# -----------------------------
@dataclass
class JoinState:
    """State for resuming the streaming join over reviews .json."""
    input_path: str
    output_path: str
    brand: str
    limit: Optional[int]          # None means full corpus (no limit)
    offset: int                   # byte offset in reviews_json
    written: int                  # total joined lines written so far
    next_review_id: int
    updated_at_unix: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_path": self.input_path,
            "output_path": self.output_path,
            "brand": self.brand,
            "limit": self.limit,
            "offset": self.offset,
            "written": self.written,
            "next_review_id": self.next_review_id,
            "updated_at_unix": self.updated_at_unix,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JoinState":
        raw_limit = d.get("limit", None)
        limit: Optional[int]
        if raw_limit is None:
            limit = None
        else:
            try:
                limit = int(raw_limit)
            except Exception:
                limit = None

        return JoinState(
            input_path=str(d.get("input_path", "")),
            output_path=str(d.get("output_path", "")),
            brand=str(d.get("brand", "")),
            limit=limit,
            offset=int(d.get("offset", 0)),
            written=int(d.get("written", 0)),
            next_review_id=int(d.get("next_review_id", 0)),
            updated_at_unix=float(d.get("updated_at_unix", 0.0)),
        )


def _atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    """Write JSON atomically to avoid corrupt state on crashes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_state(state_path: Path) -> Optional[JoinState]:
    if not state_path.exists():
        return None
    try:
        d = json.loads(state_path.read_text(encoding="utf-8"))
        return JoinState.from_dict(d)
    except Exception as e:
        print(f"[WARN] Failed to read checkpoint {state_path}: {e}")
        return None


def save_state(state_path: Path, st: JoinState) -> None:
    st.updated_at_unix = time.time()
    _atomic_write_json(state_path, st.to_dict())


def reset_outputs(out_jsonl: Path, state_path: Path) -> None:
    """Delete output and checkpoint to rebuild from scratch."""
    if out_jsonl.exists():
        out_jsonl.unlink()
        print(f"[DEL ] Removed {out_jsonl}")
    if state_path.exists():
        state_path.unlink()
        print(f"[DEL ] Removed {state_path}")


# -----------------------------
# Core pipeline
# -----------------------------
def build_brand_meta_index(meta_json: Path, brand: str) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """
    Index metadata by asin, but only keep products with matching brand.
    Returns (meta_index, asin_set).
    """
    idx: Dict[str, Dict[str, Any]] = {}
    asin_set: Set[str] = set()

    total = 0
    with open_text(meta_json) as f:
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

            cats = obj.get("category") or obj.get("categories")
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


def join_to_jsonl_with_resume(
    reviews_json: Path,
    meta_index: Dict[str, Dict[str, Any]],
    asin_set: Set[str],
    out_jsonl: Path,
    state_path: Path,
    brand: str,
    limit: Optional[int],     # None => full corpus
    resume: bool,
    checkpoint_every: int,
) -> None:
    """
    Stream reviews (from decompressed .json), join on asin (only for asins in asin_set),
    keep only non-empty reviewText, and write JSONL.

    limit:
        - None  -> build full corpus (no limit)
        - int   -> stop after writing that many joined records

    Resume behavior:
        - If resume=True and state exists, seek to saved byte offset and append to output.
        - Otherwise start from beginning and overwrite output.
    """
    if checkpoint_every < 1:
        checkpoint_every = 200

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Counters (for this run segment)
    scanned = 0
    parsed = 0
    eligible_asin = 0
    empty_text = 0
    matched_meta = 0

    # Determine start mode
    start_offset = 0
    written = 0
    review_id = 0
    out_mode = "w"

    st = load_state(state_path) if resume else None
    if st is not None:
        # Safety checks (avoid accidentally appending to mismatched run)
        if (
            Path(st.input_path) == reviews_json
            and Path(st.output_path) == out_jsonl
            and st.brand == brand
            and st.limit == limit
        ):
            start_offset = max(int(st.offset), 0)
            written = max(int(st.written), 0)
            review_id = max(int(st.next_review_id), 0)
            out_mode = "a"
            print(f"[RES ] Resuming join from offset={start_offset}, written={written}, next_review_id={review_id}")
        else:
            print("[WARN] Checkpoint mismatch (paths/brand/limit). Starting from scratch.")

    # If a limited run already satisfied, skip
    if limit is not None and written >= limit:
        print(f"[SKIP] Output already has written={written} >= limit={limit}. Nothing to do.")
        return

    with reviews_json.open("r", encoding="utf-8", errors="replace") as fin, out_jsonl.open(out_mode, encoding="utf-8") as fout:
        # Seek to checkpoint offset if needed
        if start_offset > 0:
            fin.seek(start_offset)
            fin.readline()  # align to next full line (avoid partial JSON line)

        last_ckpt_written = written

        try:
            for line in fin:
                scanned += 1

                # Stop condition (only if limit is set)
                if limit is not None and written >= limit:
                    break

                line = line.strip()
                if not line:
                    continue

                parsed += 1
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
                    "review_id": review_id,
                    "asin": asin,
                    "overall": r.get("overall"),
                    "reviewText": review_text.strip(),
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
                written += 1
                review_id += 1
                matched_meta += 1

                # Periodic checkpoint
                if written - last_ckpt_written >= checkpoint_every:
                    fout.flush()
                    offset = fin.tell()
                    save_state(
                        state_path,
                        JoinState(
                            input_path=str(reviews_json),
                            output_path=str(out_jsonl),
                            brand=brand,
                            limit=limit,
                            offset=offset,
                            written=written,
                            next_review_id=review_id,
                            updated_at_unix=time.time(),
                        ),
                    )
                    last_ckpt_written = written
                    print(f"[CKPT] written={written}, offset={offset}")

        except KeyboardInterrupt:
            # Save checkpoint on interrupt
            fout.flush()
            offset = fin.tell()
            save_state(
                state_path,
                JoinState(
                    input_path=str(reviews_json),
                    output_path=str(out_jsonl),
                    brand=brand,
                    limit=limit,
                    offset=offset,
                    written=written,
                    next_review_id=review_id,
                    updated_at_unix=time.time(),
                ),
            )
            print(f"\n[INT ] Interrupted. Saved checkpoint at written={written}, offset={offset}.")
            raise

    # Final checkpoint save
    save_state(
        state_path,
        JoinState(
            input_path=str(reviews_json),
            output_path=str(out_jsonl),
            brand=brand,
            limit=limit,
            offset=reviews_json.stat().st_size,  # best-effort "done" offset
            written=written,
            next_review_id=review_id,
            updated_at_unix=time.time(),
        ),
    )

    print(f"[REV ] Scanned {scanned} lines (from resume point), parsed {parsed} JSON lines.")
    print(f"[FILT] Reviews with asin in selected brand set: {eligible_asin}")
    print(f"[FILT] Dropped empty reviewText: {empty_text}")
    print(f"[JOIN] Wrote {matched_meta} new joined lines. Total written now={written} -> {out_jsonl}")
    print(f"[STAT] Checkpoint saved to {state_path}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Corpus construction pipeline: download + extract(.json required) + brand-filter + join with resume (Amazon v2 Sports_and_Outdoors)."
    )
    ap.add_argument("--out", default="data", help="Base output dir (default: data)")
    ap.add_argument("--brand", default="Coleman", help='Brand filter (default: "Coleman")')
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max joined records to write (default: None = build full corpus)",
    )
    ap.add_argument("--timeout", type=int, default=60, help="Download timeout seconds (default: 60)")
    ap.add_argument("--resume", action="store_true", help="Resume join from checkpoint and append output")
    ap.add_argument("--reset", action="store_true", help="Delete existing output + checkpoint and rebuild from scratch")
    ap.add_argument("--checkpoint-every", type=int, default=200, help="Write checkpoint every N joined records (default: 200)")
    args = ap.parse_args()

    base = Path(args.out)
    raw = base / "raw"
    processed = base / "processed"
    state_dir = base / "state"

    reviews_gz = raw / "Sports_and_Outdoors_5.json.gz"
    meta_gz = raw / "meta_Sports_and_Outdoors.json.gz"
    reviews_json = raw / "Sports_and_Outdoors_5.json"
    meta_json = raw / "meta_Sports_and_Outdoors.json"

    brand_clean = args.brand.strip().title().replace(" ", "")
    out_jsonl = processed / f"sports_outdoors_joined_{brand_clean}.jsonl"
    state_path = state_dir / f"join_state_{brand_clean}.json"

    print("=== Corpus Construction Pipeline: Amazon v2 Sports_and_Outdoors (resume supported) ===")
    print(f"Brand filter: {args.brand!r}")
    print(f"Reviews gz   : {reviews_gz}")
    print(f"Meta gz      : {meta_gz}")
    print(f"Reviews json : {reviews_json}")
    print(f"Meta json    : {meta_json}")
    print(f"Output JSONL : {out_jsonl}")
    print(f"Checkpoint   : {state_path}")
    if args.limit is None:
        print("Limit        : None (build full corpus)")
    else:
        print(f"Limit        : {args.limit}")

    if args.reset:
        reset_outputs(out_jsonl, state_path)

    # 1) Download
    download(REVIEWS_URL, reviews_gz, timeout=args.timeout)
    download(META_URL, meta_gz, timeout=args.timeout)

    # 2) Extract (always, to support byte-offset resume)
    gunzip(reviews_gz, reviews_json)
    gunzip(meta_gz, meta_json)

    # 3) Build brand meta index + asin set
    meta_index, asin_set = build_brand_meta_index(meta_json, brand=args.brand)

    # 4) Stream join with resume
    join_to_jsonl_with_resume(
        reviews_json=reviews_json,
        meta_index=meta_index,
        asin_set=asin_set,
        out_jsonl=out_jsonl,
        state_path=state_path,
        brand=args.brand,
        limit=args.limit,  # None => full corpus
        resume=args.resume,
        checkpoint_every=args.checkpoint_every,
    )

    print("Done.")


if __name__ == "__main__":
    main()
