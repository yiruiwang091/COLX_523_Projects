# Sprint 3 Project Overview

In Sprint 3, the goal is to:

* Finalize the annotation workflow for the processed Coleman review corpus.
* Generate annotation input sets and complete pair-based double annotation with 100% overlap.
* Apply the annotation guidelines consistently for attribute-level sentiment labeling.
* Measure inter-annotator agreement (IAA) and assess annotation reliability.
* Adjudicate disagreements to derive one final “best” annotation per review.
* Document the annotation process, intermediate files, and final output format.
* Begin planning the corpus exploration interface for the next stage.   

This sprint delivers:

* A complete set of annotation guidelines for span-level attribute and sentiment annotation. 
* A master sampled annotation input file of 1,000 unique reviews, plus inspection-ready CSV outputs. 
* Two pair-level annotation input sets, one for each annotator pair, covering all 1,000 reviews with full overlap. 
* Intermediate annotation files and manifests stored in `Sprint_3/data/annotation_intermediary/`. 
* Inter-annotator agreement analysis and discussion of annotation consistency. 
* A reproducible adjudication procedure for resolving disagreements and producing final annotations. 
* A final adjudicated annotation dataset for downstream modeling and analysis. 
* A short interface plan and mockup for corpus search and annotated-data access. 

## Repo and data storage

xxx

## Annotation + explanation + code

### Step 1: Annotation input generation

#### 1.1 Sample 1,000 unique reviews (master file)

We use `Sprint_2/src/make_annotation_input.py` to sample from the processed corpus (`Sprint_2/data/processed/`) and output a Label Studio tasks JSON plus a human-readable CSV. The script supports `.jsonl` input and can stratify by star rating for balanced sets. 

```bash
mkdir -p Sprint_3/data/annotation_intermediary

python Sprint_2/src/make_annotation_input.py \
  --input Sprint_2/data/processed/sports_outdoors_joined_Coleman.jsonl \
  --n 1000 --seed 523 \
  --out-json Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json \
  --out-csv  Sprint_3/data/annotation_intermediary/master_1000.csv \
  --stratify-by-rating
```

**Outputs**

* `Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json` — Label Studio task file for the full 1,000 sampled reviews
* `Sprint_3/data/annotation_intermediary/master_1000.csv` — inspection-friendly CSV ver.

#### 1.2 Split into per annotator pair sets

We then split the master file using `Sprint_3/src/split_annotation_sets.py`. Our design uses **two annotator pairs**, where each pair processes 500 unique samples. Each annotator within a pair labels the same 500 samples, ensuring **every one of the 1,000 samples receives two passes (100% overlap)**. 

```bash
mkdir -p Sprint_3/data/annotation_intermediary/annotation_input_sets

python Sprint_3/src/split_annotation_sets.py \
  --master-json Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json \
  --out-dir     Sprint_3/data/annotation_intermediary/annotation_input_sets \
  --seed 523 \
  --pair1 yirui wei \
  --pair2 leah freya
```

**Outputs**

* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair1_yirui_wei_labelstudio.json` — Label Studio task file for pair 1
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair1_yirui_wei.csv` — inspection-friendly CSV for pair 1
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair2_leah_freya_labelstudio.json` — Label Studio task file for pair 2
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair2_leah_freya.csv` — inspection-friendly CSV for pair 2
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/splits_manifest.json` — manifest documenting the split assignment


### Step 2: Human annotation in Label Studio

Each pair then annotated its assigned 500-review set in Label Studio following the annotation guidelines in `Sprint_3/documentation/annotation_guidelines.md`. The annotation task is span-based, covering three text regions per item—title, description, and review text—and assigns open-ended attribute labels to minimal spans. For review-text spans only, annotators also assign sentiment labels (`positive`, `negative`, `neutral`, `unknown`).

These files are the direct products of the annotation process:

* `Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair1_raw.json` — raw Label Studio export for one annotator pair
* `Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair2_raw.json` — raw Label Studio export for the other annotator pair

The raw pair exports still contain one annotation record per annotator per review. They are therefore not yet the final corpus annotation.


#### Step 3: Adjudication: derive one best annotation per review

To convert the two raw annotations for each review into a single final annotation, we use `Sprint_3/src/adjudication.py`. The script takes one raw pair export at a time and produces a single adjudicated record per `review_id`. A detailed explanation of the script and our adjudication strategy is documented in `Sprint_3/documentation/adjudication_note.md`.

In summary, the final adjudicated annotation for each review is produced by comparing the two annotators’ span-level annotations, preserving exact agreement, keeping one-sided spans, and resolving conflicts through fixed tie-breaking rules. Label conflicts are resolved by preferring non-generic, more frequent, and more specific labels, while sentiment conflicts are resolved by preferring defined and more informative sentiment values. Because all decisions are rule-based and logged, the adjudication process is fully reproducible and transparent.

```bash
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
```

**Outputs**
* `Sprint_3/data/annotation_final/annotated_pair1_adjudicated.json` — JSON file of final annotations of 500 reviews
* `Sprint_3/data/annotation_final/annotated_pair1_adjudicated.jsonl` — JSONL file of final annotations of 500 reviews
* `Sprint_3/data/annotation_final/pair1_adjudication_conflicts.csv` — CSV conflict log of one annotator pair
* `Sprint_3/data/annotation_final/annotated_pair2_adjudicated.json` — JSON file of final annotations of another 500 reviews
* `Sprint_3/data/annotation_final/annotated_pair2_adjudicated.jsonl` — JSONL file of final annotations of another 500 reviews
* `Sprint_3/data/annotation_final/pair2_adjudication_conflicts.csv` — CSV conflict log of another annotator pair

### Discussion of the Annotation Process

- During annotation, we maintained a shared attribute glossary so that newly introduced labels could be reused consistently across annotators rather than drifting into synonyms or small naming variants. This helped keep the final attribute inventory to a manageable and desirable set of about 45 labels, even though the schema itself was open-ended and allowed new labels when needed. 

- Our annotation setup required fine-grained span-level work across title, description, and review text, with review mentions additionally receiving sentiment labels. In practice, this meant that a single entry could contain many separate attribute mentions, each of which had to be identified with a minimal span and then assigned an attribute label, making the task much more repetitive and time-consuming than simpler document-level or binary labeling setups. Given the tight project timeline, this created a substantial workload pressure. 

- We encountered some one-sided spans and genuine disagreement cases, especially when one annotator chose a broader label and the other chose a more specific one for the same text. To handle these cases efficiently, consistently, and reproducibly, we used predefined adjudication rules implemented in code rather than manually editing the final files, and we retained conflict logs so that disagreement cases remained transparent and auditable.

## Interannotator agreement study

xx

## Plan for the interface

xx

## Prompt completion

xx
