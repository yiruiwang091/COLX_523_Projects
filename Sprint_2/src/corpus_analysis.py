#!/usr/bin/env python3
"""
corpus_analysis.py

Optional Sprint 2 bonus: corpus stats + corpus comparisons + metadata interactions.

Implements COLX521 -style analyses:
- Simple stats (avg word length, avg doc length, etc.)
- Type-token ratio (TTR) at a fixed token budget (10k)
- Compare our corpus vs NLTK corpora (treebank, reuters, webtext, movie_reviews, brown)
- Metadata interactions: rating distribution; review length by rating; rating-length correlation

Outputs:
- JSON summary: our_corpus_stats.json
- CSV: corpus_comparison_stats.csv
- CSV: rating_distribution.csv
- CSV: review_length_by_rating.csv
- TXT: rating_length_correlation.txt

Usage:
  python Sprint_2/src/corpus_analysis.py \
    --input Sprint_2/data/processed/sports_outdoors_joined_Coleman.json \
    --outdir Sprint_2/documentation/corpus_analysis_outputs \
    --ttr-n 10000
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Optional deps: pandas / nltk
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import nltk
    from nltk.corpus import brown, treebank, reuters, webtext, movie_reviews
except Exception:
    nltk = None


# ----------------------------
# Tokenization
# ----------------------------
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")

def tokenize_words(text: str) -> List[str]:
    """Simple word tokenizer (lowercased alnum+apostrophe words)."""
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


# ----------------------------
# Reading corpus (JSON array or JSONL)
# ----------------------------
def detect_format(path: Path) -> str:
    """Return 'json_array' or 'jsonl' based on first non-whitespace char."""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        while True:
            ch = f.read(1)
            if not ch:
                break
            if ch.isspace():
                continue
            return "json_array" if ch == "[" else "jsonl"
    raise ValueError("Empty input file.")

def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def read_json_array(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def load_records(path: Path) -> Iterable[Dict[str, Any]]:
    fmt = detect_format(path)
    if fmt == "jsonl":
        return iter_jsonl(path)
    data = read_json_array(path)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array (list of objects).")
    return iter(data)


# ----------------------------
# Core corpus stats
# ----------------------------
@dataclass
class CorpusStats:
    name: str
    n_docs: int
    n_tokens: int
    n_types: int
    avg_word_len: float
    avg_doc_len_tokens: float
    median_doc_len_tokens: float
    ttr_fixed_n: float

def average_word_length(tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    return sum(len(t) for t in tokens) / len(tokens)

def type_token_ratio(tokens: List[str], num_tokens: int) -> float:
    """TTR computed over the first num_tokens tokens."""
    if not tokens:
        return 0.0
    n = min(num_tokens, len(tokens))
    window = tokens[:n]
    return len(set(window)) / float(n)

def safe_median_int(xs: List[int]) -> float:
    if not xs:
        return 0.0
    return float(statistics.median(xs))

def compute_our_corpus_stats(
    records: Iterable[Dict[str, Any]],
    ttr_n: int,
    include_title_desc: bool = False,
    limit_docs: Optional[int] = None,
) -> Tuple[CorpusStats, Dict[str, Any]]:
    rating_counts = collections.Counter()
    cat5_counts = collections.Counter()
    missing_cat5 = 0

    all_tokens: List[str] = []
    doc_lengths: List[int] = []
    n_docs = 0

    for rec in records:
        if limit_docs is not None and n_docs >= limit_docs:
            break

        review = rec.get("reviewText") or ""
        title = rec.get("title") or ""
        desc = rec.get("description") or ""

        text = review
        if include_title_desc:
            text = f"{title}\n{desc}\n{review}"

        tokens = tokenize_words(text)
        all_tokens.extend(tokens)
        doc_lengths.append(len(tokens))

        # rating bucket
        rating = rec.get("overall")
        try:
            r = int(round(float(rating)))
        except Exception:
            r = None
        if r in {1, 2, 3, 4, 5}:
            rating_counts[str(r)] += 1
        else:
            rating_counts["unk"] += 1

        cat5 = rec.get("cat_l5")
        if cat5:
            cat5_counts[str(cat5)] += 1
        else:
            missing_cat5 += 1

        n_docs += 1

    n_tokens = len(all_tokens)
    n_types = len(set(all_tokens))
    avg_wlen = average_word_length(all_tokens)
    avg_doc = (sum(doc_lengths) / len(doc_lengths)) if doc_lengths else 0.0
    med_doc = safe_median_int(doc_lengths)
    ttr = type_token_ratio(all_tokens, ttr_n)

    stats = CorpusStats(
        name="coleman_reviews",
        n_docs=n_docs,
        n_tokens=n_tokens,
        n_types=n_types,
        avg_word_len=avg_wlen,
        avg_doc_len_tokens=avg_doc,
        median_doc_len_tokens=med_doc,
        ttr_fixed_n=ttr,
    )

    extra = {
        "rating_counts": dict(rating_counts),
        "cat_l5_top20": cat5_counts.most_common(20),
        "missing_cat_l5": missing_cat5,
        "ttr_n": int(ttr_n),
        "include_title_desc": bool(include_title_desc),
        "limit_docs": limit_docs,
    }

    return stats, extra


# ----------------------------
# NLTK corpora comparisons
# ----------------------------
def ensure_nltk_corpora() -> None:
    if nltk is None:
        return
    # Download as needed
    for pkg in ["brown", "treebank", "reuters", "webtext", "movie_reviews"]:
        try:
            nltk.data.find(f"corpora/{pkg}")
        except Exception:
            nltk.download(pkg)

def nltk_words(corpus_name: str) -> List[str]:
    if nltk is None:
        raise RuntimeError("nltk not installed.")
    corp_map = {
        "brown": brown,
        "treebank": treebank,
        "reuters": reuters,
        "webtext": webtext,
        "movie_reviews": movie_reviews,
    }
    if corpus_name not in corp_map:
        raise ValueError(f"Unknown NLTK corpus: {corpus_name}")
    words = corp_map[corpus_name].words()
    # Keep only non-empty string tokens
    return [w.lower() for w in words if isinstance(w, str) and w.strip()]

def compute_nltk_stats(corpus_name: str, ttr_n: int) -> CorpusStats:
    words = nltk_words(corpus_name)
    return CorpusStats(
        name=corpus_name,
        n_docs=0,  # per-file doc counts vary; omitted
        n_tokens=len(words),
        n_types=len(set(words)),
        avg_word_len=average_word_length(words),
        avg_doc_len_tokens=0.0,
        median_doc_len_tokens=0.0,
        ttr_fixed_n=type_token_ratio(words, ttr_n),
    )


# ----------------------------
# Metadata interactions
# ----------------------------
def analyze_metadata_interactions(records_path: Path, outdir: Path) -> None:
    if pd is None:
        print("[WARN] pandas not installed; skipping metadata interaction analysis.")
        return

    fmt = detect_format(records_path)
    if fmt == "jsonl":
        rows = list(iter_jsonl(records_path))
    else:
        rows = read_json_array(records_path)

    df = pd.DataFrame(rows)

    df["reviewText"] = df["reviewText"].fillna("").astype(str)
    df["overall_num"] = pd.to_numeric(df.get("overall"), errors="coerce")
    df["rating_int"] = df["overall_num"].round().astype("Int64")
    df["review_len_tokens"] = df["reviewText"].apply(lambda s: len(tokenize_words(s)))

    # rating distribution
    rating_dist = (
        df["rating_int"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("rating")
        .reset_index(name="n_reviews")
    )
    rating_dist.to_csv(outdir / "rating_distribution.csv", index=False)

    # review length by rating
    len_by_rating = (
        df.groupby("rating_int", dropna=False)["review_len_tokens"]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .rename(columns={"rating_int": "rating"})
        .sort_values("rating")
    )
    len_by_rating.to_csv(outdir / "review_length_by_rating.csv", index=False)

    # rating-length Pearson correlation
    corr = df[["overall_num", "review_len_tokens"]].dropna().corr(numeric_only=True).iloc[0, 1]
    (outdir / "rating_length_correlation.txt").write_text(
        f"pearson_corr(overall, review_len_tokens) = {corr}\n",
        encoding="utf-8",
    )


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to processed corpus (.json array or .jsonl).")
    ap.add_argument("--outdir", required=True, help="Directory to write analysis outputs.")
    ap.add_argument("--ttr-n", type=int, default=10000, help="Token budget for TTR (default 10k).")
    ap.add_argument("--limit-docs", type=int, default=0, help="Optional: limit number of docs (0 = no limit).")
    ap.add_argument(
        "--include-title-desc",
        action="store_true",
        help="If set, compute our corpus stats using title+description+reviewText (default is reviewText only).",
    )
    ap.add_argument(
        "--skip-nltk",
        action="store_true",
        help="If set, do not compare to NLTK corpora (avoids downloads).",
    )
    args = ap.parse_args()

    in_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    limit = None if args.limit_docs <= 0 else int(args.limit_docs)

    # 1) Our corpus stats
    records_iter = load_records(in_path)
    our_stats, extra = compute_our_corpus_stats(
        records=records_iter,
        ttr_n=int(args.ttr_n),
        include_title_desc=bool(args.include_title_desc),
        limit_docs=limit,
    )

    (outdir / "our_corpus_stats.json").write_text(
        json.dumps({"stats": our_stats.__dict__, "extra": extra}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[OUR CORPUS]")
    print(json.dumps(our_stats.__dict__, indent=2))

    # 2) Compare against NLTK corpora
    comparison_rows: List[Dict[str, Any]] = [our_stats.__dict__]

    if (nltk is not None) and (not args.skip_nltk):
        try:
            ensure_nltk_corpora()
            for name in ["brown", "treebank", "reuters", "webtext", "movie_reviews"]:
                st = compute_nltk_stats(name, ttr_n=int(args.ttr_n))
                comparison_rows.append(st.__dict__)
        except Exception as e:
            print("[WARN] NLTK comparison skipped due to error:", repr(e))

    # Write comparisons CSV
    comp_csv = outdir / "corpus_comparison_stats.csv"
    with comp_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
        w.writeheader()
        for row in comparison_rows:
            w.writerow(row)

    # 3) Metadata interactions
    analyze_metadata_interactions(in_path, outdir)

    print(f"[OK] Wrote outputs to: {outdir}")


if __name__ == "__main__":
    main()