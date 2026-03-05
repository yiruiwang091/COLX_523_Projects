#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-generated from adjudication.ipynb on 2026-03-05.

This script contains the code cells from the notebook, in order.
"""

# ===== Cell 1 =====
# for pair 1
import json, os, re, pandas as pd
from collections import defaultdict, Counter

IN_PATH = "Sprint_3/data/annotation_final/pair_1.json"
OUT_JSON = "Sprint_3/data/annotation_final/pair_1_adjudicated_500.json"
OUT_JSONL = "Sprint_3/data/annotation_final/pair_1_adjudicated_500.jsonl"
OUT_LOG = "Sprint_3/data/annotation_final/pair_1_adjudication_conflicts.csv"

REMOVE_LABELS = {"brand", "product_type"}

GENERIC = {
    "design","quality","overall","overall_quality","performance","functionality","usability",
    "overall_performance","overall_rating","general"
}

def norm_label(x):
    if not isinstance(x, str):
        return None
    s = x.strip().lower()
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    return s

def norm_sent(x):
    if not isinstance(x, str):
        return None
    return x.strip().lower()

def listify(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def normalize_misplaced_dict_in_names(rec, span_key, name_key):
    if name_key not in rec or not isinstance(rec[name_key], list):
        return
    if span_key not in rec or not isinstance(rec[span_key], list):
        rec[span_key] = [] if span_key not in rec else rec[span_key]
    new_names = []
    for x in rec[name_key]:
        if isinstance(x, dict) and "start" in x and "end" in x and "text" in x and isinstance(x["text"], list):
            rec[span_key].append({"start": x["start"], "end": x["end"]})
            for lab in x["text"]:
                new_names.append(lab)
        else:
            new_names.append(x)
    rec[name_key] = new_names

def extract_items(rec, section):
    if section == "title":
        span_key, name_key, text_key = "title_attr_span", "title_attr_name", "title"
        sentiment = None
    elif section == "desc":
        span_key, name_key, text_key = "desc_attr_span", "desc_attr_name", "description"
        sentiment = None
    else:
        span_key, name_key, text_key = "review_attr_span", "review_attr_name", "reviewText"
        sentiment = rec.get("sentiment", None)
    normalize_misplaced_dict_in_names(rec, span_key, name_key)
    spans = listify(rec.get(span_key, []))
    names = rec.get(name_key, [])
    names = listify(names)
    sents = listify(sentiment) if section=="review" else []
    # align
    n = min(len(spans), len(names))
    items = []
    for i in range(n):
        sp = spans[i]
        lab = norm_label(names[i])
        if lab is None:
            continue
        if lab in REMOVE_LABELS:
            continue
        if not (isinstance(sp, dict) and "start" in sp and "end" in sp):
            continue
        try:
            start = int(sp["start"]); end = int(sp["end"])
        except Exception:
            continue
        it = {"start": start, "end": end, "label": lab}
        if section=="review":
            sent = norm_sent(sents[i]) if i < len(sents) else None
            it["sentiment"] = sent
        items.append(it)
    return items

# load
with open(IN_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# label frequency (global) to break ties
freq = Counter()
for rec in data:
    for sec in ["title","desc","review"]:
        for it in extract_items(rec, sec):
            freq[it["label"]] += 1

def choose_label(label_a, label_b):
    # prefer non-generic
    a_gen = label_a in GENERIC
    b_gen = label_b in GENERIC
    if a_gen and not b_gen:
        return label_b, "prefer_non_generic"
    if b_gen and not a_gen:
        return label_a, "prefer_non_generic"
    # prefer more frequent
    fa, fb = freq[label_a], freq[label_b]
    if fa != fb:
        return (label_a if fa > fb else label_b), "prefer_more_frequent"
    # prefer longer (more specific)
    if len(label_a) != len(label_b):
        return (label_a if len(label_a) > len(label_b) else label_b), "prefer_longer_label"
    # stable tie-breaker
    return (min(label_a, label_b)), "lexicographic_tie"

def choose_sentiment(sa, sb):
    # if identical or one missing
    if sa == sb:
        return sa, "agree"
    if sa is None:
        return sb, "missing_one"
    if sb is None:
        return sa, "missing_one"
    # prefer non-unknown over unknown
    if sa == "unknown" and sb != "unknown":
        return sb, "prefer_non_unknown"
    if sb == "unknown" and sa != "unknown":
        return sa, "prefer_non_unknown"
    # prefer non-neutral over neutral when disagreement (more informative)
    if sa == "neutral" and sb in {"positive","negative"}:
        return sb, "prefer_polar_over_neutral"
    if sb == "neutral" and sa in {"positive","negative"}:
        return sa, "prefer_polar_over_neutral"
    # otherwise mark unknown (conservative, per guideline)
    return "unknown", "set_unknown_on_conflict"

# group by review_id
by_rid = defaultdict(list)
for rec in data:
    by_rid[rec["review_id"]].append(rec)

assert all(len(v)==2 for v in by_rid.values()), "Expected exactly two records per review_id"

adjudicated = []
conflict_rows = []

for rid, recs in sorted(by_rid.items()):
    # pick base metadata from first
    base = {k: recs[0].get(k) for k in ["review_id","asin","overall","title","description","reviewText","text","id"]}
    base["annotator"] = "adjudicated"
    base["source_annotators"] = sorted([recs[0].get("annotator"), recs[1].get("annotator")])
    
    # for each section merge
    out = {}
    for sec, span_key, name_key in [
        ("title","title_attr_span","title_attr_name"),
        ("desc","desc_attr_span","desc_attr_name"),
        ("review","review_attr_span","review_attr_name"),
    ]:
        items_a = extract_items(recs[0], sec)
        items_b = extract_items(recs[1], sec)
        # index by (start,end)
        map_a = defaultdict(list)
        map_b = defaultdict(list)
        for it in items_a:
            map_a[(it["start"],it["end"])].append(it)
        for it in items_b:
            map_b[(it["start"],it["end"])].append(it)
        all_spans = sorted(set(map_a.keys()) | set(map_b.keys()))
        final_items = []
        for span in all_spans:
            la = map_a.get(span, [])
            lb = map_b.get(span, [])
            # if both have at least one item for span
            if la and lb:
                # if any exact label match between sides, keep those (union of matches)
                labels_a = {x["label"] for x in la}
                labels_b = {x["label"] for x in lb}
                inter = labels_a & labels_b
                if inter:
                    for lab in sorted(inter):
                        fi = {"start": span[0], "end": span[1], "label": lab}
                        if sec=="review":
                            sa = next((x.get("sentiment") for x in la if x["label"]==lab), None)
                            sb = next((x.get("sentiment") for x in lb if x["label"]==lab), None)
                            sent, sent_rule = choose_sentiment(sa, sb)
                            fi["sentiment"] = sent
                            if sent_rule != "agree":
                                conflict_rows.append({
                                    "review_id": rid, "section": sec, "start": span[0], "end": span[1],
                                    "type": "sentiment_conflict", "wei": sa, "yirui": sb,
                                    "chosen": sent, "rule": sent_rule
                                })
                        final_items.append(fi)
                else:
                    # conflict: same span but different label(s): choose one
                    # pick first label from each side (if multiple, choose most frequent)
                    lab_a = max(labels_a, key=lambda x: (freq[x], len(x), x))
                    lab_b = max(labels_b, key=lambda x: (freq[x], len(x), x))
                    chosen, rule = choose_label(lab_a, lab_b)
                    fi = {"start": span[0], "end": span[1], "label": chosen}
                    if sec=="review":
                        sa = next((x.get("sentiment") for x in la if x["label"]==lab_a), None)
                        sb = next((x.get("sentiment") for x in lb if x["label"]==lab_b), None)
                        sent, sent_rule = choose_sentiment(sa, sb)
                        fi["sentiment"] = sent
                    final_items.append(fi)
                    conflict_rows.append({
                        "review_id": rid, "section": sec, "start": span[0], "end": span[1],
                        "type": "label_conflict", "wei": lab_a, "yirui": lab_b,
                        "chosen": chosen, "rule": rule
                    })
            else:
                # only one side has it -> keep all from that side (could be multiple labels on same span)
                only = la if la else lb
                who = "rec0" if la else "rec1"
                for it in only:
                    fi = {"start": it["start"], "end": it["end"], "label": it["label"]}
                    if sec=="review":
                        fi["sentiment"] = it.get("sentiment")
                    final_items.append(fi)
                    conflict_rows.append({
                        "review_id": rid, "section": sec, "start": it["start"], "end": it["end"],
                        "type": "span_only_one_annotator", "wei": it["label"] if la else None,
                        "yirui": it["label"] if lb else None,
                        "chosen": it["label"], "rule": "union_keep"
                    })
        # sort and write to output keys
        final_items.sort(key=lambda x: (x["start"], x["end"], x["label"]))
        out[span_key] = [{"start": it["start"], "end": it["end"], "text": None} for it in final_items]
        out[name_key] = [it["label"] for it in final_items]
        if sec=="review":
            out["sentiment"] = [it.get("sentiment") for it in final_items]
    # build record
    rec_out = {**base, **out}
    adjudicated.append(rec_out)

len(adjudicated), adjudicated[0].keys()

# ===== Cell 2 =====
# Fill span text from the original record texts for readability (optional but useful)
def fill_text_fields(rec_out, original):
    # title
    t = original.get("title","") or ""
    d = original.get("description","") or ""
    rtxt = original.get("reviewText","") or ""
    for sec, key, txt in [("title","title_attr_span",t),("desc","desc_attr_span",d),("review","review_attr_span",rtxt)]:
        spans = rec_out.get(key, [])
        for sp in spans:
            if sp.get("text") is None and isinstance(sp.get("start"), int) and isinstance(sp.get("end"), int):
                s,e=sp["start"], sp["end"]
                s=max(0,min(s,len(txt))); e=max(0,min(e,len(txt)))
                if e<s: s,e=e,s
                sp["text"]=txt[s:e]
    return rec_out

# choose one original per rid for text slicing (they should match)
orig_by_rid = {rid: recs[0] for rid, recs in by_rid.items()}
for i, rec_out in enumerate(adjudicated):
    rid = rec_out["review_id"]
    adjudicated[i] = fill_text_fields(rec_out, orig_by_rid[rid])

# Save JSON and JSONL
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(adjudicated, f, ensure_ascii=False, indent=2)

with open(OUT_JSONL, "w", encoding="utf-8") as f:
    for rec in adjudicated:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# Save conflicts
df_conf = pd.DataFrame(conflict_rows)
df_conf.to_csv(OUT_LOG, index=False, encoding="utf-8")

# quick stats
stats = {
    "total_reviews": len(adjudicated),
    "conflict_rows": len(df_conf),
    "label_conflicts": int((df_conf["type"]=="label_conflict").sum()) if not df_conf.empty else 0,
    "sentiment_conflicts": int((df_conf["type"]=="sentiment_conflict").sum()) if not df_conf.empty else 0,
    "one_sided_spans": int((df_conf["type"]=="span_only_one_annotator").sum()) if not df_conf.empty else 0,
}
OUT_JSON, OUT_JSONL, OUT_LOG, stats

# ===== Cell 3 =====
# for pair 2
import json, os, re
import pandas as pd
from collections import defaultdict, Counter

IN_PATH = "Sprint_3/data/annotation_final/pair_1.json"
OUT_JSON = "Sprint_3/data/annotation_final/pair_2_adjudicated_500.json"
OUT_JSONL = "Sprint_3/data/annotation_final/pair_2_adjudicated_500.jsonl"
OUT_LOG = "Sprint_3/data/annotation_final/pair_2_adjudication_conflicts.csv"

REMOVE_LABELS = {"brand", "product_type"}
GENERIC = {
    "design","quality","overall","overall_quality","performance","functionality","usability",
    "overall_performance","overall_rating","general"
}

def norm_label(x):
    if not isinstance(x, str):
        return None
    s = x.strip().lower()
    s = s.replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    return s

def norm_sent(x):
    if not isinstance(x, str):
        return None
    return x.strip().lower()

def listify(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def normalize_misplaced_dict_in_names(rec, span_key, name_key):
    if name_key not in rec or not isinstance(rec[name_key], list):
        return
    if span_key not in rec or not isinstance(rec[span_key], list):
        rec[span_key] = [] if span_key not in rec else rec[span_key]
    new_names = []
    for x in rec[name_key]:
        if isinstance(x, dict) and "start" in x and "end" in x and "text" in x and isinstance(x["text"], list):
            rec[span_key].append({"start": x["start"], "end": x["end"]})
            for lab in x["text"]:
                new_names.append(lab)
        else:
            new_names.append(x)
    rec[name_key] = new_names

def extract_items(rec, section):
    if section == "title":
        span_key, name_key, text_key = "title_attr_span", "title_attr_name", "title"
        sentiment = None
    elif section == "desc":
        span_key, name_key, text_key = "desc_attr_span", "desc_attr_name", "description"
        sentiment = None
    else:
        span_key, name_key, text_key = "review_attr_span", "review_attr_name", "reviewText"
        sentiment = rec.get("sentiment", None)

    normalize_misplaced_dict_in_names(rec, span_key, name_key)
    spans = listify(rec.get(span_key, []))
    names = listify(rec.get(name_key, []))
    sents = listify(sentiment) if section=="review" else []

    n = min(len(spans), len(names))
    items = []
    for i in range(n):
        sp = spans[i]
        lab = norm_label(names[i])
        if lab is None or lab in REMOVE_LABELS:
            continue
        if not (isinstance(sp, dict) and "start" in sp and "end" in sp):
            continue
        try:
            start = int(sp["start"]); end = int(sp["end"])
        except Exception:
            continue
        it = {"start": start, "end": end, "label": lab}
        if section=="review":
            it["sentiment"] = norm_sent(sents[i]) if i < len(sents) else None
        items.append(it)
    return items

# load
with open(IN_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# determine annotators
annotators = sorted({rec.get("annotator") for rec in data if rec.get("annotator") is not None})
annotators_count = Counter(rec.get("annotator") for rec in data)
annotators, annotators_count.most_common()[:10]

# ===== Cell 4 =====
# # The file should contain exactly 2 annotators for pair 2; but it contains 3 (1,2,3).
# We'll infer the main pair as the two annotators with the largest counts: (3,2).
a_id, b_id = [x for x,_ in annotators_count.most_common(2)]
a_id, b_id

# ===== Cell 5 =====
# build label frequency (global) for tie-breaks, considering only main pair
freq = Counter()
for rec in data:
    if rec.get("annotator") not in {a_id, b_id}:
        continue
    for sec in ["title","desc","review"]:
        for it in extract_items(rec, sec):
            freq[it["label"]] += 1

def choose_label(label_a, label_b):
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
    return (min(label_a, label_b)), "lexicographic_tie"

def choose_sentiment(sa, sb):
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
    if sa == "neutral" and sb in {"positive","negative"}:
        return sb, "prefer_polar_over_neutral"
    if sb == "neutral" and sa in {"positive","negative"}:
        return sa, "prefer_polar_over_neutral"
    return "unknown", "set_unknown_on_conflict"

def fill_text_fields(rec_out, original):
    t = original.get("title","") or ""
    d = original.get("description","") or ""
    rtxt = original.get("reviewText","") or ""
    for key, txt in [("title_attr_span",t),("desc_attr_span",d),("review_attr_span",rtxt)]:
        spans = rec_out.get(key, [])
        for sp in spans:
            if sp.get("text") is None and isinstance(sp.get("start"), int) and isinstance(sp.get("end"), int):
                s,e = sp["start"], sp["end"]
                s=max(0,min(s,len(txt))); e=max(0,min(e,len(txt)))
                if e<s: s,e=e,s
                sp["text"] = txt[s:e]
    return rec_out

# group by review_id for main pair only
by_rid = defaultdict(list)
for rec in data:
    if rec.get("annotator") in {a_id, b_id}:
        by_rid[rec["review_id"]].append(rec)

# ensure each review_id has two recs (some might be missing from annotator 2)
paired_rids = [rid for rid, recs in by_rid.items() if len(recs)==2]
len(paired_rids), len(by_rid)

# ===== Cell 6 =====
# For missing ones, we'll still produce 500 by including single-annotator records from annotator 3 (the majority).
# Choose fallback annotator: a_id (3)
fallback_id = a_id

adjudicated = []
conflict_rows = []

for rid in sorted(by_rid.keys()):
    recs = by_rid[rid]
    if len(recs) == 2:
        rA = recs[0] if recs[0].get("annotator")==a_id else recs[1]
        rB = recs[0] if recs[0].get("annotator")==b_id else recs[1]
    else:
        # only one record (likely from annotator 3)
        rA = recs[0]
        rB = None

    base = {k: rA.get(k) for k in ["review_id","asin","overall","title","description","reviewText","text","id"]}
    base["annotator"] = "adjudicated"
    base["source_annotators"] = sorted(list({x.get("annotator") for x in recs}))

    out = {}
    for sec, span_key, name_key in [
        ("title","title_attr_span","title_attr_name"),
        ("desc","desc_attr_span","desc_attr_name"),
        ("review","review_attr_span","review_attr_name"),
    ]:
        items_a = extract_items(rA, sec)
        items_b = extract_items(rB, sec) if rB is not None else []

        map_a = defaultdict(list)
        map_b = defaultdict(list)
        for it in items_a:
            map_a[(it["start"],it["end"])].append(it)
        for it in items_b:
            map_b[(it["start"],it["end"])].append(it)

        all_spans = sorted(set(map_a.keys()) | set(map_b.keys()))
        final_items = []

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
                        if sec=="review":
                            sa = next((x.get("sentiment") for x in la if x["label"]==lab), None)
                            sb = next((x.get("sentiment") for x in lb if x["label"]==lab), None)
                            sent, sent_rule = choose_sentiment(sa, sb)
                            fi["sentiment"] = sent
                            if sent_rule != "agree":
                                conflict_rows.append({
                                    "review_id": rid, "section": sec, "start": span[0], "end": span[1],
                                    "type": "sentiment_conflict", "a": sa, "b": sb,
                                    "chosen": sent, "rule": sent_rule
                                })
                        final_items.append(fi)
                else:
                    lab_a = max(labels_a, key=lambda x: (freq[x], len(x), x))
                    lab_b = max(labels_b, key=lambda x: (freq[x], len(x), x))
                    chosen, rule = choose_label(lab_a, lab_b)
                    fi = {"start": span[0], "end": span[1], "label": chosen}
                    if sec=="review":
                        sa = next((x.get("sentiment") for x in la if x["label"]==lab_a), None)
                        sb = next((x.get("sentiment") for x in lb if x["label"]==lab_b), None)
                        sent, sent_rule = choose_sentiment(sa, sb)
                        fi["sentiment"] = sent
                    final_items.append(fi)
                    conflict_rows.append({
                        "review_id": rid, "section": sec, "start": span[0], "end": span[1],
                        "type": "label_conflict", "a": lab_a, "b": lab_b,
                        "chosen": chosen, "rule": rule
                    })
            else:
                only = la if la else lb
                who = a_id if la else b_id
                for it in only:
                    fi = {"start": it["start"], "end": it["end"], "label": it["label"]}
                    if sec=="review":
                        fi["sentiment"] = it.get("sentiment")
                    final_items.append(fi)
                    conflict_rows.append({
                        "review_id": rid, "section": sec, "start": it["start"], "end": it["end"],
                        "type": "span_only_one_annotator", "a": it["label"] if la else None,
                        "b": it["label"] if lb else None,
                        "chosen": it["label"], "rule": f"union_keep_only_{who}"
                    })

        final_items.sort(key=lambda x: (x["start"], x["end"], x["label"]))
        out[span_key] = [{"start": it["start"], "end": it["end"], "text": None} for it in final_items]
        out[name_key] = [it["label"] for it in final_items]
        if sec=="review":
            out["sentiment"] = [it.get("sentiment") for it in final_items]

    rec_out = {**base, **out}
    rec_out = fill_text_fields(rec_out, rA)  # use rA text
    if rB is None:
        conflict_rows.append({
            "review_id": rid, "section": "all", "start": None, "end": None,
            "type": "missing_second_annotator_record",
            "a": rA.get("annotator"), "b": None,
            "chosen": "fallback_single_annotator", "rule": "keep_single"
        })
    adjudicated.append(rec_out)

len(adjudicated), adjudicated[0]["source_annotators"]

# ===== Cell 7 =====
# Save outputs
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(adjudicated, f, ensure_ascii=False, indent=2)

with open(OUT_JSONL, "w", encoding="utf-8") as f:
    for rec in adjudicated:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

df_conf = pd.DataFrame(conflict_rows)
df_conf.to_csv(OUT_LOG, index=False, encoding="utf-8")

stats = {
    "total_reviews": len(adjudicated),
    "annotators_in_file": annotators,
    "pair_used": (a_id, b_id),
    "paired_reviews_with_both": len(paired_rids),
    "reviews_missing_second": int((df_conf["type"]=="missing_second_annotator_record").sum()),
    "label_conflicts": int((df_conf["type"]=="label_conflict").sum()),
    "sentiment_conflicts": int((df_conf["type"]=="sentiment_conflict").sum()),
}
OUT_JSON, OUT_JSONL, OUT_LOG, stats

# ===== Cell 8 =====

