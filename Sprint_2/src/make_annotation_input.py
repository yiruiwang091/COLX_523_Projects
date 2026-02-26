"""
make_annotation_input.py

Generate a small annotation-input file (>=10 records) from the processed corpus.

Inputs supported:
- JSONL (one JSON object per line)  [recommended]
- JSON  (a JSON array of objects)  [works for ~31k docs, but loads into memory]

Outputs:
- Label Studio tasks JSON (list[dict]): [{"id": ..., "data": {...}, "meta": {...}}, ...]
- CSV with key fields for easy review

Typical usage (JSONL):
  python Sprint_2/src/make_annotation_input.py \
    --input Sprint_2/data/processed/sports_outdoors_joined_Coleman.jsonl \
    --n 10 --seed 123 \
    --out-json Sprint_2/data/annotation_inputs/annotation_input_10_labelstudio.json \
    --out-csv  Sprint_2/data/annotation_inputs/annotation_input_10.csv \
    --stratify-by-rating

Typical usage (JSON array):
  python Sprint_2/src/make_annotation_input.py \
    --input Sprint_2/data/processed/sports_outdoors_joined_Coleman.json \
    --n 10 --seed 123 \
    --out-json Sprint_2/data/annotation_inputs/annotation_input_10_labelstudio.json \
    --out-csv  Sprint_2/data/annotation_inputs/annotation_input_10.csv \
    --stratify-by-rating
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Reading helpers
# -----------------------------
def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def read_json_array(path: Path) -> List[Dict[str, Any]]:
    # NOTE: loads entire file; ok for ~31k docs.
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


# -----------------------------
# Sampling helpers
# -----------------------------
def reservoir_sample(stream: Iterable[Dict[str, Any]], k: int, rng: random.Random) -> List[Dict[str, Any]]:
    """Uniform sample of k items from an iterator, without knowing stream length."""
    sample: List[Dict[str, Any]] = []
    for t, item in enumerate(stream, start=1):
        if len(sample) < k:
            sample.append(item)
        else:
            j = rng.randint(1, t)
            if j <= k:
                sample[j - 1] = item
    return sample


def rating_bucket(x: Any) -> str:
    """
    Bucket by star rating into "1","2","3","4","5","unk".
    We round to nearest int because 'overall' is often float.
    """
    try:
        if x is None:
            return "unk"
        v = float(x)
        r = int(round(v))
        if 1 <= r <= 5:
            return str(r)
        return "unk"
    except Exception:
        return "unk"


def stratified_sample_by_rating(
    stream: Iterable[Dict[str, Any]],
    n: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Try to get a diverse set across ratings 1..5.
    Strategy:
      - First pass: reservoir-sample up to (n*4) per bucket to keep memory bounded.
      - Then allocate picks across buckets.
    """
    # Keep a moderate pool per bucket so we can pick later without holding whole corpus.
    pool_cap = max(n * 4, 20)
    pools: Dict[str, List[Dict[str, Any]]] = {str(i): [] for i in range(1, 6)}
    pools["unk"] = []

    # Reservoir per bucket (independent)
    seen: Dict[str, int] = {k: 0 for k in pools.keys()}

    for item in stream:
        b = rating_bucket(item.get("overall"))
        seen[b] += 1
        pool = pools[b]
        t = seen[b]

        if len(pool) < pool_cap:
            pool.append(item)
        else:
            j = rng.randint(1, t)
            if j <= pool_cap:
                pool[j - 1] = item

    # Target allocation: spread evenly across 1..5, then fill remainder.
    base = n // 5
    remainder = n % 5
    targets: Dict[str, int] = {str(i): base for i in range(1, 6)}
    for i in range(1, remainder + 1):
        targets[str(i)] += 1

    # If some buckets don't have enough, redistribute.
    deficit = 0
    for b in [str(i) for i in range(1, 6)]:
        if len(pools[b]) < targets[b]:
            deficit += targets[b] - len(pools[b])
            targets[b] = len(pools[b])

    # Redistribute deficit to buckets with extra capacity (including "unk" as last resort)
    if deficit > 0:
        for b in [str(i) for i in range(5, 0, -1)] + ["unk"]:
            if deficit <= 0:
                break
            extra = len(pools[b]) - targets.get(b, 0)
            if extra <= 0:
                continue
            take = min(extra, deficit)
            targets[b] = targets.get(b, 0) + take
            deficit -= take

    # Now sample from each pool according to targets.
    out: List[Dict[str, Any]] = []
    for b, k in targets.items():
        if k <= 0:
            continue
        pool = pools[b]
        rng.shuffle(pool)
        out.extend(pool[:k])

    # Final shuffle (so output isn't grouped by rating)
    rng.shuffle(out)

    # If still short (rare), just return whatever we got.
    return out[:n]


# -----------------------------
# Output helpers
# -----------------------------
def make_label_studio_task(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal Label Studio task structure.

    Keep the *full* fields needed for an attribute + sentiment annotation:
    title, description, reviewText (and IDs for traceability).
    """
    rid = rec.get("review_id")
    asin = rec.get("asin")
    overall = rec.get("overall")

    title = rec.get("title") or ""
    description = rec.get("description") or ""
    review_text = rec.get("reviewText") or ""

    # Optional convenience field for UI display
    combined = (
        f"TITLE:\n{title}\n\n"
        f"DESCRIPTION:\n{description}\n\n"
        f"REVIEW:\n{review_text}"
    )

    return {
        "id": int(rid) if isinstance(rid, int) or (isinstance(rid, str) and rid.isdigit()) else rid,
        "data": {
            "review_id": rid,
            "asin": asin,
            "overall": overall,
            "title": title,
            "description": description,
            "reviewText": review_text,
            "text": combined,  # handy if Label Studio config uses a single text field
        },
        "meta": {
            "cat_l1": rec.get("cat_l1"),
            "cat_l2": rec.get("cat_l2"),
            "cat_l3": rec.get("cat_l3"),
            "cat_l4": rec.get("cat_l4"),
            "cat_l5": rec.get("cat_l5"),
        },
    }


def write_labelstudio_json(tasks: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(records: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Keep CSV simple + human-reviewable
    fieldnames = [
        "review_id",
        "asin",
        "overall",
        "title",
        "description",
        "reviewText",
        "cat_l1",
        "cat_l2",
        "cat_l3",
        "cat_l4",
        "cat_l5",
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            row = {k: r.get(k, "") for k in fieldnames}
            w.writerow(row)


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Create small annotation input files (Label Studio JSON + CSV).")
    ap.add_argument("--input", required=True, help="Path to corpus (.jsonl or .json array).")
    ap.add_argument("--n", type=int, default=10, help="Number of records to export (default: 10).")
    ap.add_argument("--seed", type=int, default=123, help="Random seed for reproducible sampling.")
    ap.add_argument("--out-json", required=True, help="Output Label Studio JSON path.")
    ap.add_argument("--out-csv", required=True, help="Output CSV path (for inspection).")
    ap.add_argument(
        "--stratify-by-rating",
        action="store_true",
        help="Try to diversify samples across star ratings 1..5.",
    )
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    rng = random.Random(args.seed)
    n = max(int(args.n), 1)

    # Read stream
    suffix = in_path.suffix.lower()
    if suffix == ".jsonl":
        stream = iter_jsonl(in_path)
        if args.stratify_by_rating:
            picked = stratified_sample_by_rating(stream, n=n, rng=rng)
        else:
            picked = reservoir_sample(stream, k=n, rng=rng)
    elif suffix == ".json":
        data = read_json_array(in_path)
        if not isinstance(data, list):
            raise ValueError("Expected JSON array input (list of objects).")
        if args.stratify_by_rating:
            picked = stratified_sample_by_rating(iter(data), n=n, rng=rng)
        else:
            rng.shuffle(data)
            picked = data[:n]
    else:
        raise ValueError("Unsupported input type. Use .jsonl or .json")

    # Write outputs
    tasks = [make_label_studio_task(r) for r in picked]
    write_labelstudio_json(tasks, Path(args.out_json))
    write_csv(picked, Path(args.out_csv))

    print(f"[OK] Exported {len(picked)} records")
    print(f"     Label Studio JSON: {args.out_json}")
    print(f"     CSV             : {args.out_csv}")


if __name__ == "__main__":
    main()