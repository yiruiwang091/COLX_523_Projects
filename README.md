# COLX523_Sprint 1

## Project Overview

In this project, our team is building a structured corpus from Amazon v2 (Sports_and_Outdoors category).  

The goal of Sprint 1 is to:
1. Set up a properly structured GitHub repository
2. Define a teamwork contract
3. Propose our corpus design
4. Demonstrate a working corpus collection POC

---

# Repository Structure

This repository follows a standard project structure:

project-root/
├── README.md
├── src/
│ └── poc_download_and_join.py
├── data/
│ ├── raw/
│ └── processed/
└── documentation/
│ ├── step-by-step_algorithm.md
│ ├── team_contract.md
│ └── project_proposal.md

- `src/` – runnable Python scripts
- `data/raw/` – downloaded original dataset files (`.json.gz` and `.json`)
- `data/processed/` – processed outputs
- `documentation/` – step-by-step algorithm, team contract and project proposal

---

# Teamwork Contract

Our teamwork contract is documented in:

- `documentation/team_contract.md`

It outlines:
- Work distribution and task sequencing
- Meeting schedule and documentation practices
- Communication expectations
- Code review process and git workflow
- Scrum leadership rotation
- Code of conduct

Each team member has also included a self-reflection and skill ranking.

---

# Corpus Proposal

Our proposal is documented in: 

- `documentation/project_proposal.md`

## Data Source
Amazon Review Data (2018), Sports & Outdoors category.
We focus on the Coleman subset and join reviews with product metadata via the shared asin key.

## Corpus Overview
This corpus supports attribute-level sentiment analysis of product reviews.

Instead of labeling entire reviews, we annotate text spans that express opinions about specific product attributes (e.g., durability, ease of setup, comfort), together with sentiment polarity (positive / negative / neutral).

The dataset contains:
- ~31,000 English reviews
- Product-level metadata (brand, category, price, etc.)
- Span-level attribute–sentiment annotations

## Purpose
The corpus is designed to:
- Enable attribute-level product quality analysis
- Support downstream modeling of attribute–sentiment extraction
- Provide a browser interface for non-expert exploration and annotation

---

# Corpus Collection POC

To demonstrate that we can collect and construct the proposed corpus, we implemented: 

- `src/poc_download_and_join.py`

It demonstrates a fully reproducible pipeline:
- downloads the **Sports_and_Outdoors** reviews (5-core) and metadata files,
- decompresses them,
- joins reviews and metadata via the shared key `asin`,
- outputs a joined corpus in **JSONL** format.

## How to Run

From the repository root:

### Recommended (Fast POC Mode)

To quickly validate the pipeline without downloading the full dataset:

```bash
python src/poc_download_and_join.py --limit 100
```

This runs the complete join pipeline but writes only the first 100 joined records.
This mode is sufficient for verifying reproducibility and correctness.

### Full Run (Not Recommended for POC)

```bash
python src/poc_download_and_join.py
```

This downloads the full Sports_and_Outdoors (5-core) review file and metadata,
then constructs the complete joined corpus.

Note: The full dataset is large and may take significant time to download.
For demonstration and grading purposes, the limited mode above is recommended.

## Outputs

After running, the script creates:
- data/raw/Sports_and_Outdoors_5.json.gz
- data/raw/meta_Sports_and_Outdoors.json.gz
- data/raw/Sports_and_Outdoors_5.json
- data/raw/meta_Sports_and_Outdoors.json
- data/processed/sports_outdoors_joined.jsonl

Each line in the JSONL file is a joined record created by matching the review file and metadata file on `asin`.

We keep a **selected subset of fields** from each source:
- Review fields (`asin`, `overall`, `summary`, `reviewText`, `unixReviewTime`, `reviewerID`)
- Metadata fields (`title`, `brand`, `price`, `cat_l1`–`cat_l5`)

### Example Record

```json
{
  "asin": "0000032034",
  "overall": 5.0,
  "summary": "Five Stars",
  "reviewText": "What a spectacular tutu! Very slimming.",
  "unixReviewTime": 1433289600,
  "reviewerID": "A180LQZBUWVOLF",
  "title": "Adult Ballet Tutu Yellow",
  "brand": "BubuBibi",
  "price": "$12.50",
  "cat_l1": "Sports & Outdoors",
  "cat_l2": "Sports & Fitness",
  "cat_l3": "Other Sports",
  "cat_l4": "Dance",
  "cat_l5": "Clothing"
}
```

## Why both files are required

The final corpus structure requires joining reviews with metadata via `asin`.  
Therefore, both datasets are necessary and complementary.

---

# Step-by-Step Algorithm

The full corpus construction algorithm is documented in:
- `documentation/step-by-step_algorithm.md`

It covers the end-to-end pipeline implemented in `src/poc_download_and_join.py`, including:
- Programmatic download of reviews + metadata
- POC-size control via `--limit`
- Metadata parsing and in-memory indexing by `asin`
- Writing the joined corpus to JSONL (`data/processed/sports_outdoors_joined.jsonl`)

---

# Sprint Completion

All Sprint 1 deliverables have been completed:
- Repository setup
- Teamwork contract
- Corpus proposal
- Working corpus collection POC
- Clear documentation and runnable script
