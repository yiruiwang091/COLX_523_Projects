"""
Adjudicate two-annotator Label Studio exports into a single "best final annotation" per review_id.

Usage:
python Sprint_3/src/adjudication.py \
  --pair pair1 \
  --input Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair1_raw.json \
  --out-json  Sprint_3/data/annotation_final/annotated_pair1_adjudicated.json \
  --out-jsonl Sprint_3/data/annotation_final/annotated_pair1_adjudicated.jsonl \
  --out-log   Sprint_3/data/annotation_final/pair1_adjudication_conflicts.csv \
  --include-span-text

python Sprint_3/src/adjudication.py \
  --pair pair2 \
  --input Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair2_raw.json \
  --out-json  Sprint_3/data/annotation_final/annotated_pair2_adjudicated.json \
  --out-jsonl Sprint_3/data/annotation_final/annotated_pair2_adjudicated.jsonl \
  --out-log   Sprint_3/data/annotation_final/pair2_adjudication_conflicts.csv \
  --include-span-text

"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


GENERIC = {
    "design",
    "overall",
    "performance",
}


def norm_label(x: Any) -> Optional[str]:
    if not isinstance(x, str):
        return None
    s = x.strip().lower()
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    return s or None


def norm_sent(x: Any) -> Optional[str]:
    if not isinstance(x, str):
        return None
    s = x.strip().lower()
    return s or None


def listify(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def normalize_misplaced_dict_in_names(rec: Dict[str, Any], span_key: str, name_key: str) -> None:
    """
    Defensive normalization for a known export weirdness:
    sometimes dicts containing {"start","end","text":[labels...]} end up inside *_attr_name.
    Move span info into *_attr_span and flatten labels into *_attr_name.
    """
    if name_key not in rec or not isinstance(rec[name_key], list):
        return
    if span_key not in rec or not isinstance(rec[span_key], list):
        rec[span_key] = [] if span_key not in rec else rec[span_key]

    new_names: List[Any] = []
    for x in rec[name_key]:
        if (
            isinstance(x, dict)
            and "start" in x
            and "end" in x
            and "text" in x
            and isinstance(x["text"], list)
        ):
            rec[span_key].append({"start": x["start"], "end": x["end"]})
            new_names.extend(x["text"])
        else:
            new_names.append(x)

    rec[name_key] = new_names


def extract_items(rec: Dict[str, Any], section: str) -> List[Dict[str, Any]]:
    """
    Convert one record's fields into normalized items:
      {"start": int, "end": int, "label": str, ("sentiment": str?)}
    """
    if section == "title":
        span_key, name_key = "title_attr_span", "title_attr_name"
        sentiment = None
    elif section == "desc":
        span_key, name_key = "desc_attr_span", "desc_attr_name"
        sentiment = None
    elif section == "review":
        span_key, name_key = "review_attr_span", "review_attr_name"
        sentiment = rec.get("sentiment", None)
    else:
        raise ValueError(f"Unknown section: {section}")

    normalize_misplaced_dict_in_names(rec, span_key, name_key)

    spans = listify(rec.get(span_key, []))
    names = listify(rec.get(name_key, []))
    sents = listify(sentiment) if section == "review" else []

    n = min(len(spans), len(names))
    out: List[Dict[str, Any]] = []
    for i in range(n):
        sp = spans[i]
        lab = norm_label(names[i])
        if lab is None:
            continue
        if not (isinstance(sp, dict) and "start" in sp and "end" in sp):
            continue

        try:
            start = int(sp["start"])
            end = int(sp["end"])
        except Exception:
            continue

        it = {"start": start, "end": end, "label": lab}
        if section == "review":
            it["sentiment"] = norm_sent(sents[i]) if i < len(sents) else None
        out.append(it)

    return out


def choose_label(label_a: str, label_b: str, freq: Counter) -> Tuple[str, str]:
    """
    Deterministic tie-breaker for label conflicts on the same span.
    """
    a_gen = label_a in GENERIC
    b_gen = label_b in GENERIC
    if a_gen and not b_gen:
        return label_b, "prefer_non_generic"
    if b_gen and not a_gen:
        return label_a, "prefer_non_generic"

    fa, fb = freq[label_a], freq[label_b]
    if fa != fb:
        return (label_a if fa > fb else label_b), "prefer_more_frequent"

    if len(label_a) != len(label_b):
        return (label_a if len(label_a) > len(label_b) else label_b), "prefer_longer_label"

    return min(label_a, label_b), "lexicographic_tie"


def choose_sentiment(sa: Optional[str], sb: Optional[str]) -> Tuple[Optional[str], str]:
    """
    Deterministic tie-breaker for sentiment conflicts.
    """
    if sa == sb:
        return sa, "agree"
    if sa is None:
        return sb, "missing_one"
    if sb is None:
        return sa, "missing_one"

    if sa == "unknown" and sb != "unknown":
        return sb, "prefer_non_unknown"
    if sb == "unknown" and sa != "unknown":
        return sa, "prefer_non_unknown"

    if sa == "neutral" and sb in {"positive", "negative"}:
        return sb, "prefer_polar_over_neutral"
    if sb == "neutral" and sa in {"positive", "negative"}:
        return sa, "prefer_polar_over_neutral"

    return "unknown", "set_unknown_on_conflict"


def fill_text_fields(rec_out: Dict[str, Any], original: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optionally populate span['text'] by slicing original text fields.
    """
    title = original.get("title", "") or ""
    desc = original.get("description", "") or ""
    rtxt = original.get("reviewText", "") or ""

    for key, txt in [
        ("title_attr_span", title),
        ("desc_attr_span", desc),
        ("review_attr_span", rtxt),
    ]:
        spans = rec_out.get(key, [])
        for sp in spans:
            if sp.get("text") is None and isinstance(sp.get("start"), int) and isinstance(sp.get("end"), int):
                s, e = sp["start"], sp["end"]
                s = max(0, min(s, len(txt)))
                e = max(0, min(e, len(txt)))
                if e < s:
                    s, e = e, s
                sp["text"] = txt[s:e]
    return rec_out


def adjudicate_pair(
    data: List[Dict[str, Any]],
    pair_name: str,
    expected_annotators: Tuple[int, int],
    include_span_text: bool = True,
) -> Tuple[List[Dict[str, Any]], pd.DataFrame, Dict[str, Any]]:
    a_id, b_id = expected_annotators

    # Historical fix: annotator 1 should be treated as annotator 2.
    for rec in data:
        if rec.get("annotator") == 1:
            rec["annotator"] = 2

    raw_annotators = Counter(rec.get("annotator") for rec in data if rec.get("annotator") is not None)

    kept = [rec for rec in data if rec.get("annotator") in {a_id, b_id}]
    dropped = [rec for rec in data if rec.get("annotator") not in {a_id, b_id}]

    present = sorted({rec.get("annotator") for rec in kept})
    if present != sorted([a_id, b_id]):
        raise ValueError(
            f"{pair_name}: expected annotators {sorted([a_id, b_id])}, but found {present}. "
            f"Raw annotators in input file: {dict(raw_annotators)}"
        )

    # Frequency stats for tie-breaks.
    freq: Counter = Counter()
    for rec in kept:
        for sec in ["title", "desc", "review"]:
            for it in extract_items(rec, sec):
                freq[it["label"]] += 1

    by_rid: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for rec in kept:
        by_rid[rec.get("review_id")].append(rec)

    adjudicated: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []

    for rid in sorted(by_rid.keys()):
        recs = by_rid[rid]
        rA = next((r for r in recs if r.get("annotator") == a_id), None)
        rB = next((r for r in recs if r.get("annotator") == b_id), None)

        if rA is None and rB is None:
            continue

        base_src = rA if rA is not None else rB
        base = {
            k: base_src.get(k)
            for k in ["review_id", "asin", "overall", "title", "description", "reviewText", "text", "id"]
        }
        base["annotator"] = "adjudicated"
        base["source_annotators"] = sorted(
            [x.get("annotator") for x in recs if x.get("annotator") is not None]
        )

        out: Dict[str, Any] = {}

        for sec, span_key, name_key in [
            ("title", "title_attr_span", "title_attr_name"),
            ("desc", "desc_attr_span", "desc_attr_name"),
            ("review", "review_attr_span", "review_attr_name"),
        ]:
            items_a = extract_items(rA, sec) if rA is not None else []
            items_b = extract_items(rB, sec) if rB is not None else []

            map_a: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
            map_b: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)

            for it in items_a:
                map_a[(it["start"], it["end"])].append(it)
            for it in items_b:
                map_b[(it["start"], it["end"])].append(it)

            all_spans = sorted(set(map_a.keys()) | set(map_b.keys()))
            final_items: List[Dict[str, Any]] = []

            for span in all_spans:
                la = map_a.get(span, [])
                lb = map_b.get(span, [])

                if la and lb:
                    labels_a = {x["label"] for x in la}
                    labels_b = {x["label"] for x in lb}
                    inter = labels_a & labels_b

                    if inter:
                        for lab in sorted(inter):
                            fi = {"start": span[0], "end": span[1], "label": lab}
                            if sec == "review":
                                sa = next((x.get("sentiment") for x in la if x["label"] == lab), None)
                                sb = next((x.get("sentiment") for x in lb if x["label"] == lab), None)
                                sent, sent_rule = choose_sentiment(sa, sb)
                                fi["sentiment"] = sent
                                if sent_rule != "agree":
                                    conflict_rows.append(
                                        {
                                            "review_id": rid,
                                            "section": sec,
                                            "start": span[0],
                                            "end": span[1],
                                            "type": "sentiment_conflict",
                                            "annotator_a": sa,
                                            "annotator_b": sb,
                                            "chosen": sent,
                                            "rule": sent_rule,
                                        }
                                    )
                            final_items.append(fi)
                    else:
                        lab_a = max(labels_a, key=lambda x: (freq[x], len(x), x))
                        lab_b = max(labels_b, key=lambda x: (freq[x], len(x), x))
                        chosen, rule = choose_label(lab_a, lab_b, freq)

                        fi = {"start": span[0], "end": span[1], "label": chosen}
                        if sec == "review":
                            sa = next((x.get("sentiment") for x in la if x["label"] == lab_a), None)
                            sb = next((x.get("sentiment") for x in lb if x["label"] == lab_b), None)
                            sent, _ = choose_sentiment(sa, sb)
                            fi["sentiment"] = sent

                        final_items.append(fi)
                        conflict_rows.append(
                            {
                                "review_id": rid,
                                "section": sec,
                                "start": span[0],
                                "end": span[1],
                                "type": "label_conflict",
                                "annotator_a": lab_a,
                                "annotator_b": lab_b,
                                "chosen": chosen,
                                "rule": rule,
                            }
                        )
                else:
                    only = la if la else lb
                    which_side = "a_only" if la else "b_only"

                    for it in only:
                        fi = {"start": it["start"], "end": it["end"], "label": it["label"]}
                        if sec == "review":
                            fi["sentiment"] = it.get("sentiment")
                        final_items.append(fi)
                        conflict_rows.append(
                            {
                                "review_id": rid,
                                "section": sec,
                                "start": it["start"],
                                "end": it["end"],
                                "type": "span_only_one_annotator",
                                "which": which_side,
                                "chosen": it["label"],
                                "rule": "union_keep",
                            }
                        )

            final_items.sort(key=lambda x: (x["start"], x["end"], x["label"]))

            out[span_key] = [{"start": it["start"], "end": it["end"], "text": None} for it in final_items]
            out[name_key] = [it["label"] for it in final_items]
            if sec == "review":
                out["sentiment"] = [it.get("sentiment") for it in final_items]

        rec_out = {**base, **out}
        adjudicated.append(rec_out)

    if include_span_text:
        source_by_rid: Dict[Any, Dict[str, Any]] = {}
        for rec in kept:
            rid = rec.get("review_id")
            if rid not in source_by_rid:
                source_by_rid[rid] = rec

        for i, rec_out in enumerate(adjudicated):
            rid = rec_out.get("review_id")
            src = source_by_rid.get(rid, {})
            adjudicated[i] = fill_text_fields(rec_out, src)

    df_conf = pd.DataFrame(conflict_rows)

    stats = {
        "pair": pair_name,
        "expected_annotators": [a_id, b_id],
        "raw_annotators_in_file": dict(raw_annotators),
        "kept_records": len(kept),
        "dropped_records": len(dropped),
        "unique_review_ids": len(by_rid),
        "adjudicated_reviews": len(adjudicated),
        "conflict_rows": int(len(df_conf)),
        "label_conflicts": int((df_conf["type"] == "label_conflict").sum()) if not df_conf.empty else 0,
        "sentiment_conflicts": int((df_conf["type"] == "sentiment_conflict").sum()) if not df_conf.empty else 0,
        "one_sided_spans": int((df_conf["type"] == "span_only_one_annotator").sum()) if not df_conf.empty else 0,
    }

    return adjudicated, df_conf, stats


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Adjudicate one raw pair file into a single final annotation file."
    )
    p.add_argument(
        "--pair",
        required=True,
        choices=["pair1", "pair2"],
        help="pair1 expects annotators 4 & 5; pair2 expects annotators 2 & 3.",
    )
    p.add_argument("--input", required=True, help="Path to raw annotated JSON.")
    p.add_argument("--out-json", required=True, help="Output adjudicated JSON path.")
    p.add_argument("--out-jsonl", required=True, help="Output adjudicated JSONL path.")
    p.add_argument("--out-log", required=True, help="Output conflicts CSV path.")
    p.add_argument(
        "--include-span-text",
        action="store_true",
        help="Fill span['text'] by slicing title/description/reviewText.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Hard-coded mapping based on your actual files.
    expected = (4, 5) if args.pair == "pair1" else (2, 3)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    adjudicated, df_conf, stats = adjudicate_pair(
        data=data,
        pair_name=args.pair,
        expected_annotators=expected,
        include_span_text=bool(args.include_span_text),
    )

    for path in [args.out_json, args.out_jsonl, args.out_log]:
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(adjudicated, f, ensure_ascii=False, indent=2)

    with open(args.out_jsonl, "w", encoding="utf-8") as f:
        for rec in adjudicated:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    df_conf.to_csv(args.out_log, index=False, encoding="utf-8")

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()