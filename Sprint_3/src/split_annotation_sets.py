"""
Split Sprint 3 annotation inputs into TWO sets (one per annotator pair - every sample gets 2 passes)

- Reads a master Label Studio tasks JSON (list of dicts)
- Deterministically shuffles with --seed
- Assigns first 500 tasks to pair1, next 500 tasks to pair2
- Writes one Label Studio JSON + one CSV per pair
- Writes splits_manifest.json for reproducibility


Usage:
python Sprint_3/src/split_annotation_sets.py \
  --master-json Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json \
  --out-dir     Sprint_3/data/annotation_intermediary/annotation_input_sets \
  --seed 523 \
  --pair1 yirui wei \
  --pair2 leah freya
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, List


CSV_FIELDS = [
    "review_id", "asin", "overall", "title", "description", "reviewText",
    "cat_l1", "cat_l2", "cat_l3", "cat_l4", "cat_l5",
]


def load_tasks(path: Path) -> List[Dict[str, Any]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise ValueError("Master JSON must be a JSON list of Label Studio tasks.")
    return tasks


def get_task_key(task: Dict[str, Any]) -> Any:
    """Prefer task['id']; fall back to data.review_id for uniqueness checks."""
    if "id" in task and task["id"] is not None:
        return task["id"]
    return (task.get("data") or {}).get("review_id")


def assert_unique(tasks: List[Dict[str, Any]]) -> None:
    keys = [get_task_key(t) for t in tasks]
    if any(k is None for k in keys):
        raise ValueError("Some tasks missing both 'id' and 'data.review_id'; can't validate uniqueness.")
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate task identifiers found in master set.")


def write_labelstudio_json(tasks: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(tasks: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for t in tasks:
            data = t.get("data", {}) or {}
            meta = t.get("meta", {}) or {}
            w.writerow({
                "review_id": data.get("review_id", ""),
                "asin": data.get("asin", ""),
                "overall": data.get("overall", ""),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "reviewText": data.get("reviewText", ""),
                "cat_l1": meta.get("cat_l1", ""),
                "cat_l2": meta.get("cat_l2", ""),
                "cat_l3": meta.get("cat_l3", ""),
                "cat_l4": meta.get("cat_l4", ""),
                "cat_l5": meta.get("cat_l5", ""),
            })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-json", required=True, help="Master Label Studio tasks JSON (should contain 1000 unique).")
    ap.add_argument("--out-dir", required=True, help="Output directory for pair-level files.")
    ap.add_argument("--seed", type=int, default=523, help="Shuffle seed for deterministic splits.")
    ap.add_argument("--pair1", nargs=2, default=["yirui", "wei"], help="Names for pair 1 (2 people).")
    ap.add_argument("--pair2", nargs=2, default=["leah", "freya"], help="Names for pair 2 (2 people).")
    ap.add_argument("--total", type=int, default=1000, help="Total unique tasks to use from master.")
    ap.add_argument("--per-pair", type=int, default=500, help="Unique tasks per pair.")
    args = ap.parse_args()

    master_path = Path(args.master_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(master_path)

    if len(tasks) < args.total:
        raise ValueError(f"Expected at least {args.total} tasks, got {len(tasks)}.")
    tasks = tasks[:args.total]  # exactly total

    assert_unique(tasks)

    if args.total != 2 * args.per_pair:
        raise ValueError("--total must equal 2 * --per-pair (e.g., 1000 and 500).")

    rng = random.Random(args.seed)
    rng.shuffle(tasks)

    pair1_tasks = tasks[:args.per_pair]
    pair2_tasks = tasks[args.per_pair: args.per_pair * 2]

    p1a, p1b = args.pair1
    p2a, p2b = args.pair2

    pair1_base = f"pair1_{p1a}_{p1b}"
    pair2_base = f"pair2_{p2a}_{p2b}"

    pair1_json = out_dir / f"{pair1_base}_labelstudio.json"
    pair1_csv = out_dir / f"{pair1_base}.csv"
    pair2_json = out_dir / f"{pair2_base}_labelstudio.json"
    pair2_csv = out_dir / f"{pair2_base}.csv"

    write_labelstudio_json(pair1_tasks, pair1_json)
    write_csv(pair1_tasks, pair1_csv)
    write_labelstudio_json(pair2_tasks, pair2_json)
    write_csv(pair2_tasks, pair2_csv)

    manifest: Dict[str, Any] = {
        "seed": args.seed,
        "total_unique": args.total,
        "per_pair_unique": args.per_pair,
        "pair1": {
            "people": [p1a, p1b],
            "n": len(pair1_tasks),
            "out_json": str(pair1_json),
            "out_csv": str(pair1_csv),
        },
        "pair2": {
            "people": [p2a, p2b],
            "n": len(pair2_tasks),
            "out_json": str(pair2_json),
            "out_csv": str(pair2_csv),
        },
    }

    (out_dir / "splits_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[OK] Wrote pair-level inputs to:", out_dir)
    print(f"  - {pair1_base}: n={len(pair1_tasks)}")
    print(f"  - {pair2_base}: n={len(pair2_tasks)}")
    print("  - splits_manifest.json written")


if __name__ == "__main__":
    main()