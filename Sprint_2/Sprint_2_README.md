# Sprint 2 Project Overview

In Sprint 2, the goal is to:

-   Complete the collection of a large, domain-appropriate corpus.
-   Ensure the corpus is reproducible and properly documented.
-   Prepare for the annotation phase (Sprint 3).
-   Draft the annotation plan and annotation schema.
-   Provide a small processed subset ready for annotation.
-   Optionally conduct preliminary corpus analysis.

## This sprint delivers:

-   A fully reproducible corpus construction pipeline.
-   A large unannotated corpus (≥ 1000 instances).
-   Resume-safe corpus construction with checkpointing.
-   Documentation of corpus format, filtering logic, and structure.
-   A detailed annotation plan.
-   An initial annotation schema.
-   A small processed subset (≥ 10 examples) prepared for annotation.
-   A plan for annotation overlap and inter-annotator agreement (IAA).

------------------------------------------------------------------------

# Repo and Data Storage

## Repository Structure

```         
project-root/
├── README.md
└── Sprint_2/
    ├── Sprint_2_README.md
    ├── src/
    │   └── corpus_pipeline.py
    |   └── corpus_stats.py
    ├── data/
    │   ├── raw/        (ignored via .gitignore)
    │   ├── processed/
    │   │   └── sports_outdoors_joined_Coleman.jsonl
    │   └── state/
    │       └── join_state_Coleman.json
    └── documentation/
        ├── corpus_readme.md
        ├── separate.md
        ├── annotation_plan.md
        └── annotation_guidelines.md
```

## Data Storage Policy

### Processed Corpus

Primary output: `Sprint_2/data/processed/sports_outdoors_joined_Coleman.jsonl`

Optional Label Studio export: `Sprint_2/data/processed/sports_outdoors_joined_Coleman.json`

-   Format: JSONL (primary) + JSON array (optional)
-   Size (Coleman corpus): \~56.9 MB
-   Stored directly in this repository

Since the processed corpus file is under 100MB, it is safely committed to GitHub and does not require external storage.

### Raw Data

Raw Amazon dumps are stored in: `Sprint_2/data/raw/`

These files are **not committed** due to their large size and are excluded via `.gitignore`.

They include:

-   `Sports_and_Outdoors_5.json.gz`
-   `meta_Sports_and_Outdoors.json.gz`
-   Decompressed `.json` files (required for resume functionality)

------------------------------------------------------------------------

# Corpus Construction Code

The corpus is built using: `Sprint_2/src/corpus_pipeline.py`

This script performs the following steps:

1.  Download Amazon Reviews v2 (Sports_and_Outdoors, 5-core).
2.  Decompress `.json.gz` → `.json` (required for byte-offset resume).
3.  Filter metadata by brand (e.g., `brand == "Coleman"`).
4.  Collect matching ASINs.
5.  Stream reviews and join them on ASIN.
6.  Drop reviews with empty `reviewText`.
7.  Write the merged corpus in JSONL format.
8.  Optionally export JSONL → JSON array for Label Studio.

## How to Run the Code

### Build Full Corpus

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --resume --export-json
```

-   Builds the full corpus (no limit).
-   Resumes from checkpoint if available.
-   Exports a Label Studio–friendly JSON file.

### Build a Smaller Test Corpus

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --limit 100 --resume --export-json
```

-   This builds only the first 100 joined records.

### Reset and Rebuild From Scratch

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --reset --export-json
```

This deletes:

-   The output JSONL file
-   The checkpoint file
-   The exported JSON file (if enabled)

Then rebuilds the corpus from scratch.

## Stop-and-Restart (Resume) Support

The script supports safe interruption and restart.

### How Resume Works

-   Download and extraction steps are idempotent.
-   The join step uses checkpointing.
-   Resume uses byte offsets in the decompressed reviews `.json` file.
-   Reviews are read in binary mode to guarantee accurate byte tracking.

Checkpoint file location: `Sprint_2/data/state/join_state_<Brand>.json`

The checkpoint stores:

-   Input file path
-   Output file path
-   Brand name
-   Limit (if specified)
-   Byte offset in reviews `.json`
-   Number of records already written
-   Next `review_id`

### How to Test Resume

1.  Run:

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --resume --export-json
```

2.  Interrupt during execution (`Ctrl + C`)

3.  Run again:

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --resume --export-json
```

The script will resume from the last checkpoint without:

-   Re-downloading files
-   Re-extracting files
-   Reprocessing completed data
-   Losing already written records

## Output Format

Primary output file: `Sprint_2/data/processed/sports_outdoors_joined_<Brand>.jsonl`

Each line is a JSON object:

``` json
{
  "review_id": 0,
  "asin": "...",
  "overall": 5,
  "reviewText": "...",
  "title": "...",
  "price": "...",
  "description": "...",
  "rank": "...",
  "imageURL": ["..."],
  "cat_l1": "...",
  "cat_l2": "...",
  "cat_l3": "...",
  "cat_l4": "...",
  "cat_l5": "..."
}
```

## Label Studio Export

If `--export-json` is enabled:

The script converts JSONL → standard JSON array: `sports_outdoors_joined_<Brand>.json`

This format is directly compatible with Label Studio.

The conversion:

-   Streams JSONL line-by-line (no full-file memory load)
-   Writes atomically to prevent corruption
-   Preserves UTF-8 encoding

## Reproducibility

The corpus can be rebuilt entirely from scratch using:

``` bash
python Sprint_2/src/corpus_pipeline.py --brand Coleman --reset
```

Reproducibility is ensured through:

-   Deterministic brand filtering
-   Explicit command-line configuration
-   Byte-level resume checkpointing
-   Atomic writes for checkpoint and JSON export
-   Fully documented repository structure

------------------------------------------------------------------------

# Corpus Description – Sports & Outdoors (Coleman Subset)

## Domain Appropriateness

The corpus consists of Amazon product reviews from the *Sports & Outdoors* category, filtered by the brand **Coleman**.

Product reviews are highly suitable for sentiment analysis and opinion mining tasks because:

-   Reviews contain explicit subjective language.
-   Star ratings (1–5) provide natural sentiment labels.
-   The data reflects real consumer opinions rather than neutral informational text.

This avoids the issue described in the rubric (e.g., journal articles producing mostly neutral sentiment).

# Corpus Statistics

To compute corpus statistics (number of documents, token count, rating distribution), run:

``` bash
cd Sprint_2
python src/corpus_stats.py --input data/processed/sports_outdoors_joined_Coleman.json
```

## Corpus Size

Using `corpus_stats.py`, we computed the following statistics:

-   **Total documents (reviews):** 31,349\
-   **Unique products (ASINs):** 543\
-   **Total tokens (whitespace-based):** 1,726,718

This corpus significantly exceeds the minimum requirement of 1,000 instances.

## Rating Distribution

The distribution of ratings is:

-   5.0 → 20,122
-   4.0 → 6,114
-   3.0 → 2,530
-   2.0 → 1,144
-   1.0 → 1,439

The corpus is positively skewed, which is common in product review datasets.\
This skew will be considered during annotation and modeling phases.

## Data Format

Primary storage format: **JSONL**

Each line contains a single review object with metadata and product information.

Fields include:

-   `review_id`
-   `asin`
-   `overall`
-   `reviewText`
-   `title`
-   `price`
-   `description`
-   category hierarchy (`cat_l1` – `cat_l5`)
-   optional metadata such as rank and image URLs

An optional JSON array version is eported for Label Studio compatibility.

## Known Issues and Limitations

-   Class imbalance toward 5-star reviews.
-   Possible minor noise (formatting artifacts, short reviews).
-   Token count is whitespace-based and not linguistically tokenized.
-   Reviews are limited to the 5-core subset (minimum 5 reviews per product).

Despite these limitations, the corpus is large, domain-consistent, and suitable for downstream annotation and sentiment analysis tasks.
