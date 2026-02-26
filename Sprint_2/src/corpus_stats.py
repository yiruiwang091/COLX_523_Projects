#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter

def token_count(text: str) -> int:
    # Simple, dependency-free tokenization (counts non-whitespace spans)
    return len(re.findall(r"\S+", text or ""))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    total_docs = 0
    total_tokens = 0
    rating_counts = Counter()
    asin_set = set()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)   # <-- This is the key fix

        for obj in data:
            total_docs += 1

            review_text = obj.get("reviewText", "")
            total_tokens += len(review_text.split())

            rating_counts[obj.get("overall")] += 1
            asin_set.add(obj.get("asin"))

    print("=== Corpus Stats ===")
    print(f"Total documents: {total_docs}")
    print(f"Unique products: {len(asin_set)}")
    print(f"Total tokens: {total_tokens}")

    print("\n=== Rating distribution ===")
    for k, v in rating_counts.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
        main()