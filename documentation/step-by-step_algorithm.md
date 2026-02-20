# Corpus Construction Algorithm

## Objective

CBuild a reproducible proof-of-concept corpus from Amazon Reviews v2 Sports_and_Outdoors by:

- Downloading review and metadata dumps
- Optionally extracting .gz files
- Indexing metadata by asin
- Streaming reviews and joining on asin
- Writing a merged JSONL file for downstream NLP use

The full pipeline runs as a single executable script:

- `src/poc_download_and_join.py`

---

# Data Sources

- Reviews (5-core):
<https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/Sports_and_Outdoors_5.json.gz>
- Metadata:
<https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/metaFiles2/meta_Sports_and_Outdoors.json.gz>

Both are JSON Lines (.json.gz).

---

# Step-by-Step Procedure

## Step 1 — Download (Programmatic Acquisition)

The script:

1. Creates `data/raw/` if it does not exist.
2. Downloads:
   - `Sports_and_Outdoors_5.json.gz`
   - `meta_Sports_and_Outdoors.json.gz`
3. Skips download if files already exist.

This ensures reproducibility without manual steps.

---

## Step 2 — Decompression

Unless `--no-extract` is specified:

1. Decompress each `.json.gz` into `.json`
2. Store decompressed files in `data/raw/`

The script can operate on either `.json` or `.json.gz` files.

---

## Step 3 — Parse and Index Metadata

1. Read metadata file line-by-line.
2. For each record:
   - Extract `asin`
   - Extract selected fields:
     - `title`
     - `brand`
     - `price`
     - `category`
3. Normalize category structure:
   - Handle both flat and nested SNAP-style formats
   - Keep up to 5 levels as cat_l1 … cat_l5
   - Missing levels are set to null
4. Store results in: meta_index[asin] → {title, brand, price, cat_l1 … cat_l5}

This enables O(1) metadata lookup during the review–metadata join step.

---

## Step 4 — Stream Reviews and Join

1. Read reviews file line-by-line (streaming).
2. For each review:
   - Extract `asin`
   - Lookup metadata in `meta_index`
3. If metadata exists:
   - Merge review fields + metadata fields
4. If metadata does not exist:
   - Skip review (default)
   
Streaming prevents loading the full reviews file into memory.

---

## Step 5 — Output Joined Corpus

1. Create `data/processed/` if it does not exist.
2. Write merged records into: data/processed/sports_outdoors_joined.jsonl
3. Each line is a valid JSON object.
4. The number of written records can be limited using `--limit` (default: 2000 for POC).

---

# Output Schema

Each JSONL record contains:

Review-level fields:
- `asin`
- `overall`
- `summary`
- `reviewText`
- `unixReviewTime`
- `reviewerID`

Metadata fields:
- `title`
- `brand`
- `price`
- `cat_l1` ... `cat_l5`

---

# Design Rationale

- Reviews provide linguistic content.
- Metadata provides structured product attributes.
- `asin` enables deterministic integration.
- Metadata is indexed in memory for O(1) lookup.
- Reviews are streamed for scalability.
- JSONL format supports extensibility and downstream NLP pipelines.