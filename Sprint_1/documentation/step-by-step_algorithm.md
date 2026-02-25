# Corpus Construction Algorithm

## Objective

Build a fully reproducible proof-of-concept corpus from Amazon Reviews v2 (Sports_and_Outdoors) by:

- Downloading review and metadata dumps (`.json.gz`)
- Optionally extracting compressed files
- Filtering product metadata by **brand** (default: `"Coleman"`)
- Collecting corresponding `asin` values
- Streaming reviews and joining on `asin`
- Keeping only reviews with non-empty `reviewText`
- Writing a merged JSONL corpus for downstream NLP use

The full pipeline runs as a single executable script:

- `src/poc_download_and_join.py`

---

## Data Sources

- Reviews (5-core):
<https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/categoryFilesSmall/Sports_and_Outdoors_5.json.gz>
- Metadata:
<https://mcauleylab.ucsd.edu/public_datasets/data/amazon_v2/metaFiles2/meta_Sports_and_Outdoors.json.gz>

Both files are in JSON Lines format and compressed as `.json.gz`.

---

## Step-by-Step Procedure

### Step 1 — Download (Programmatic Acquisition)

The script:

1. Creates `data/raw/` if it does not exist.
2. Downloads:
   - `Sports_and_Outdoors_5.json.gz`
   - `meta_Sports_and_Outdoors.json.gz`
3. Skips downloading if files already exist and are non-empty.

This guarantees reproducibility without manual intervention.

---

### Step 2 — Decompression

1. Decompress `.json.gz` into `.json`
2. Store decompressed files in `data/raw/`

The script automatically works with either `.json` or `.json.gz`.

---

### Step 3 — Brand-Filtered Metadata Indexing

1. Read metadata line-by-line.
2. Normalize and match `brand` (case-insensitive) with `--brand` argument.
3. Keep only products matching the selected brand.
4. Extract selected metadata fields:
   - `asin`
   - `title`
   - `price`
   - `description`
   - `rank`
   - `imageURL`
   - `category` (normalized and split into hierarchical levels `cat_l1`–`cat_l5`)
5. Handle both flat and nested SNAP-style category structures.
6. Store:
   - `meta_index[asin] → metadata record`
   - `asin_set → set of selected product asins`

This enables efficient O(1) metadata lookup during joining.

---

### Step 4 — Stream Reviews and Join

1. Read reviews line-by-line (streaming).
2. For each review:
   - Keep only if `asin` exists in `asin_set`
   - Drop if `reviewText` is missing or empty
   - Join review fields with metadata fields
3. Assign a deterministic `review_id` as the primary key based on streaming order.

Streaming ensures scalability without loading the entire reviews file into memory.

---

### Step 5 — Output Joined Corpus

1. Write merged records into: `data/processed/sports_outdoors_joined_Coleman.jsonl`
2. Each line is a valid JSON object.
3. Output size can be limited using `--limit` (default: 2000).

## Run Example

```bash
python src/poc_download_and_join.py --limit 100
```

Optional arguments:

- `--out data`
- `--no-extract`
- `--timeout 60`

---

## Output Schema

Each JSONL record contains:

### Primary Key
- `review_id` (int)

### Review Fields
- `asin`
- `overall`
- `reviewText`

### Metadata Fields
- `title`
- `price`
- `description`
- `rank`
- `imageURL`
- `cat_l1`
- `cat_l2`
- `cat_l3`
- `cat_l4`
- `cat_l5`

---

## Design Rationale

- Brand-level filtering produces a focused corpus for product-issue analysis.
- `asin` provides deterministic integration between reviews and metadata.
- Metadata is indexed in memory for O(1) lookup.
- Reviews are streamed for scalability.
- JSONL format supports extensibility and downstream NLP workflows.