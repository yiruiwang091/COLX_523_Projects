#!/usr/bin/env python3
"""
Split Sprint 3 annotation inputs with FULL overlap via swap.

Design:
- 1,000 unique samples total
- Two annotator pairs, each pair handles 500 unique samples
- Within each pair: split 500 into Set A (250) and Set B (250)
- Round 1: Annotator1 gets A, Annotator2 gets B
- Round 2: swap (Annotator1 gets B, Annotator2 gets A)
=> Every sample gets 2 passes (100% overlap).


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
        raise ValueError("Duplicate task IDs found in master set.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-json", required=True, help="Master Label Studio tasks JSON (should contain 1000 unique).")
    ap.add_argument("--out-dir", required=True, help="Output directory for split files.")
    ap.add_argument("--seed", type=int, default=523, help="Shuffle seed for deterministic splits.")
    ap.add_argument("--pair1", nargs=2, default=["yirui", "wei"], help="Names for pair 1 (2 people).")
    ap.add_argument("--pair2", nargs=2, default=["leah", "freya"], help="Names for pair 2 (2 people).")
    ap.add_argument("--total", type=int, default=1000, help="Total unique tasks expected.")
    ap.add_argument("--per-pair", type=int, default=500, help="Unique tasks per pair.")
    ap.add_argument("--per-set", type=int, default=250, help="Set size within a pair (A/B).")
    args = ap.parse_args()

    master_path = Path(args.master_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(master_path)

    if len(tasks) < args.total:
        raise ValueError(f"Expected at least {args.total} tasks, got {len(tasks)}.")
    tasks = tasks[:args.total]  # exactly 1000

    assert_unique(tasks)

    if args.per_pair != 2 * args.per_set:
        raise ValueError("--per-pair must equal 2 * --per-set (e.g., 500 and 250).")
    if args.total != 2 * args.per_pair:
        raise ValueError("--total must equal 2 * --per-pair (e.g., 1000 and 500).")

    rng = random.Random(args.seed)
    rng.shuffle(tasks)

    # Disjoint split into 2 pairs (500 each)
    pair1_tasks = tasks[:args.per_pair]
    pair2_tasks = tasks[args.per_pair:args.per_pair * 2]

    # Split each pair into A/B (250/250)
    p1_A, p1_B = pair1_tasks[:args.per_set], pair1_tasks[args.per_set:]
    p2_A, p2_B = pair2_tasks[:args.per_set], pair2_tasks[args.per_set:]

    p1a, p1b = args.pair1
    p2a, p2b = args.pair2

    # Person-round assignments implementing the swap
    assignments: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        p1a: {"round1": p1_A, "round2": p1_B},
        p1b: {"round1": p1_B, "round2": p1_A},
        p2a: {"round1": p2_A, "round2": p2_B},
        p2b: {"round1": p2_B, "round2": p2_A},
    }

    manifest: Dict[str, Any] = {
        "seed": args.seed,
        "total_unique": args.total,
        "pair1": {"people": [p1a, p1b], "unique": args.per_pair, "set_size": args.per_set},
        "pair2": {"people": [p2a, p2b], "unique": args.per_pair, "set_size": args.per_set},
        "files": {},
    }

    # Write per-person per-round files (these are the ones you actually use)
    for person, rounds in assignments.items():
        for rnd, subset in rounds.items():
            base = f"{person}_{rnd}"
            json_path = out_dir / f"{base}_labelstudio.json"
            csv_path = out_dir / f"{base}.csv"
            write_labelstudio_json(subset, json_path)
            write_csv(subset, csv_path)
            manifest["files"][base] = {"n": len(subset), "json": str(json_path), "csv": str(csv_path)}

    (out_dir / "splits_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[OK] Wrote Sprint 3 inputs to:", out_dir)
    for k, v in manifest["files"].items():
        print(f"  - {k:18s} n={v['n']}")


if __name__ == "__main__":
    main()