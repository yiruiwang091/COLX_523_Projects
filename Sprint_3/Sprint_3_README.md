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

# Repo and data storage

```
COLX523_Freya_Leah_Wei_Yirui/
└── Sprint_3/
    ├── data/
    │   ├── unannotated_corpus/
    │   │   ├── full_corpus.jsonl
    │   │   └── full_corpus.json
    │   ├── annotation_intermediary/
    │   │   ├── master_1000.csv
    │   │   ├── master_1000_labelstudio.json
    │   │   ├── annotation_output_sets/
    │   │   │   ├── attribute_glossary.csv
    │   │   │   ├── annotated_pair2_raw.json
    │   │   │   └── annotated_pair1_raw.json
    │   │   └── annotation_input_sets/
    │   │       ├── splits_manifest.json
    │   │       ├── pair2_leah_freya.csv
    │   │       ├── pair2_leah_freya_labelstudio.json
    │   │       ├── pair1_yirui_wei.csv
    │   │       └── pair1_yirui_wei_labelstudio.json
    │   └── annotation_final/
    │       ├── pair2_adjudication_conflicts.csv
    │       ├── pair1_adjudication_conflicts.csv
    │       ├── annotated_pair2_adjudicated.jsonl
    │       ├── annotated_pair2_adjudicated.json
    │       ├── annotated_pair1_adjudicated.jsonl
    │       └── annotated_pair1_adjudicated.json
    ├── src/
    │   ├── split_annotation_sets.py
    │   ├── label_studio_project_setup/
    │   │   ├── start_annotation.sh
    │   │   ├── setup_labelstudio.py
    │   │   ├── preannotate.py
    │   │   ├── ml_backend.py
    │   │   ├── label_config.xml
    │   │   ├── Dockerfile.ml
    │   │   └── docker-compose.yml
    │   ├── interface/
    │   │   ├── templates/
    │   │   │   └── index.html
    │   │   ├── search_service.py
    │   │   ├── index/
    │   │   │   ├── MAIN_WRITELOCK
    │   │   │   ├── MAIN_q09r0owt4vv6ihu8.seg
    │   │   │   └── _MAIN_1.toc
    │   │   ├── corpus_store.py
    │   │   ├── app.py
    │   │   └── annotation_store.py
    │   ├── human_auto_ann.ipynb
    │   └── adjudication.py
    ├── image/
    │   ├── corpus_search.png
    │   ├── corpus_detail.png
    │   ├── annotation_search.png
    │   └── annotation_detail.png
    └── documentation/
        ├── ui_mockup.md
        ├── interface_plan.md
        ├── iaa_analysis.md
        └── adjudication_note.md
```
## Repository Organization

* `Sprint_3/` is organized by function so that code, documentation, images, and data artifacts are clearly separated.
* `src/` contains all executable project code for:
  * annotation input generation
  * Label Studio setup
  * auto-annotation backend
  * adjudication
  * interface prototype
* `documentation/` contains written supporting materials, including:
  * interface planning
  * UI mockups
  * IAA analysis
  * adjudication notes
* `image/` stores screenshots and interface visuals used for documentation.
* `data/` stores all corpus and annotation-related files, organized by stage of the workflow.
* `Sprint_3_README.md` documents the sprint goals, workflow, outputs, and reproducibility steps.

This structure separates implementation code from data artifacts and documentation, making the project easier to navigate and reproduce.

## Data Storage Structure

The `data/` directory is organized to reflect the full lifecycle of the annotation workflow.

* **`unannotated_corpus/`**
  Stores the original corpus before annotation.

* **`annotation_intermediary/`**
  Contains intermediate data used during annotation preparation and collection:

  * `master_1000.*` – the sampled set of 1,000 reviews used for annotation
  * `annotation_input_sets/` – datasets distributed to annotators and a manifest documenting the split assignment
  * `annotation_output_sets/` – raw annotation exports and a attribute glossary returned from annotators

* **`annotation_final/`**
  Stores the final adjudicated annotation dataset and conflict logs.

---

# Annotation

## Step 1: Annotation input generation

### 1.1 Sample 1,000 unique reviews (master file)

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

### 1.2 Split into per annotator pair sets

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


## Step 2: Human annotation in Label Studio

Each pair then annotated its assigned 500-review set in Label Studio following the annotation guidelines in `Sprint_3/documentation/annotation_guidelines.md`. The annotation task is span-based, covering three text regions per item—title, description, and review text—and assigns open-ended attribute labels to minimal spans. For review-text spans only, annotators also assign sentiment labels (`positive`, `negative`, `neutral`, `unknown`).

We set up Label Studio using a Docker container to provide a centralized annotation environment for the team. The container was deployed on a machine within the campus local network and exposed through the campus LAN, allowing multiple annotators to access the interface and collaborate simultaneously through their browsers. All annotation data were stored in the running Docker container, enabling real-time updates and ensuring that annotations from different team members were immediately synchronized and available for further analysis. To support automatic annotation, we wrapped the GPT-5 mini model in a FastAPI service and deployed it as a backend API running on a dedicated port. This service receives text inputs from the annotation platform and returns predicted spans for attribute mentions. By connecting this API endpoint to Label Studio, we enabled the platform’s auto-annotation functionality, allowing the model to generate real-time annotation suggestions that annotators could review and modify during the labeling process. All files including server and docker definition and command are store in `./COLX523_Freya_Leah_Wei_Yirui/Sprint_3/src/label_studio_project_setup/`.

Direct products of the annotation process:
* `Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair1_raw.json` — raw Label Studio export for one annotator pair
* `Sprint_3/data/annotation_intermediary/annotation_output_sets/annotated_pair2_raw.json` — raw Label Studio export for the other annotator pair
* `Sprint_3/data/annotation_intermediary/annotation_output_sets/attribute_glossary.csv` — shared attribute glossary among annotators

The raw pair exports still contain one annotation record per annotator per review. They are therefore not yet the final corpus annotation.


## Step 3: Adjudication: derive one best annotation per review

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

## Discussion of the Annotation Process

- During annotation, we maintained a shared attribute glossary so that newly introduced labels could be reused consistently across annotators rather than drifting into synonyms or small naming variants. This helped keep the final attribute inventory to a manageable and desirable set of about 45 labels, even though the schema itself was open-ended and allowed new labels when needed. 

- Our annotation setup required fine-grained span-level work across title, description, and review text, with review mentions additionally receiving sentiment labels. In practice, this meant that a single entry could contain many separate attribute mentions, each of which had to be identified with a minimal span and then assigned an attribute label, making the task much more repetitive and time-consuming than simpler document-level or binary labeling setups. Given the tight project timeline, this created a substantial workload pressure. 

- We encountered some one-sided spans and genuine disagreement cases, especially when one annotator chose a broader label and the other chose a more specific one for the same text. To handle these cases efficiently, consistently, and reproducibly, we used predefined adjudication rules implemented in code rather than manually editing the final files, and we retained conflict logs so that disagreement cases remained transparent and auditable.

---

# Interannotator agreement study

To measure the consistency between annotations, we conducted an inter-annotator agreement (IAA) analysis between two annotators: a human annotator and the AI system. Each item contains three annotation fields (title, review, and description), where spans corresponding to attribute mentions are annotated. For each item and each field, we compared the spans identified by the two annotators. We take annotated data as input, and output the IAA score in predefined metrics.

The file to reproduce IAA is at: `./Sprint_3/src/human_auto_ann.ipynb`. Detailed analysis of IAA is at `Sprint_3/documentation/iaa_analysis.md`.

A span was considered matched if the overlap between the two spans exceeded a predefined threshold based on span overlap (IoU > 0.5). Based on these matches, we computed precision, recall, and F1 score to measure the agreement between the two annotators. Precision measures how many AI spans match the human annotations, while recall measures how many human spans are successfully identified by the AI.

Overall, the results show a moderate to strong level of agreement between the human annotator and the AI system. Most attribute mentions identified by the human annotator were also captured by the AI model, although some disagreements occurred due to differences in span boundaries or missing spans. These results suggest that the AI model can identify attribute mentions reasonably well, but human verification is still useful to ensure annotation accuracy.

---

# Plan for the Interface

## Purpose

To support interactive exploration of the corpus and annotation results, we designed a lightweight web interface for corpus search and annotation inspection.

The interface allows users to search the corpus and optionally access the adjudicated attribute annotations produced in Sprint 3.

## Plan

Users can submit keyword queries and choose which text field to search (title, description, review text, or all fields). 

The interface also provides two annotation-related options:

- **Annotated data only** – restrict results to documents that contain adjudicated annotations
- **Include annotations in results** – display a compact summary of attribute annotations under each search result  

Each result includes a **View Details** button that opens a document-level view showing the full document text together with its annotation records.

The prototype interface follows a simple client–server architecture:

- **Frontend:** HTML + JavaScript single-page interface
- **Backend:** FastAPI service exposing `/api/search` and `/api/doc/{doc_id}` endpoints
- **Search engine:** Whoosh index built from corpus fields (`title`, `description`, `reviewText`)  

## Inputs

The interface reads the processed corpus from: `Sprint_3/data/unannotated_corpus/full_corpus.jsonl`

Load adjudicated annotation outputs from:

- `Sprint_3/data/annotation_final/annotated_pair1_adjudicated.json`
- `Sprint_3/data/annotation_final/annotated_pair2_adjudicated.json`

The backend implementation is organized into modular components located in: `Sprint_3/src/interface/`

- `corpus_store.py` – loads corpus documents
- `annotation_store.py` – loads adjudicated annotations
- `search_service.py` – builds the Whoosh index and executes search queries
- `app.py` – FastAPI application and API endpoints  

A detailed interface design specification is provided in: `Sprint_3/documentation/interface_plan.md`

## UI Mockup

Example interface screenshots and UI mockups are included in: `Sprint_3/image/`

## Running the Interface Prototype

A working prototype of the corpus search interface has been implemented using **FastAPI**, **Whoosh**, and a simple **HTML/JavaScript frontend**.

### Step 1: Navigate to the interface directory

From the project root, move to the interface source directory:

```bash
cd Sprint_3/src/interface
```

### Step 2: Start the FastAPI server

Run the following command:

```bash
uvicorn app:app --reload
```

This will start a local development server.

### Step 3: Open the interface in a browser

After the server starts, open this address in a web browser.

```text
http://127.0.0.1:8000
```

### Step 4: Use the interface

The interface allows users to:

- enter a keyword query
- select the search field (All, Title, Description, or ReviewText)
- optionally enable:
  - Annotated data only
  - Include annotations in results

Search results will display ranked documents from the corpus.

Click `View Details` to inspect the full document content and its associated annotations.

> Notes

The interface reads data from:

- the processed corpus file
`Sprint_3/data/unannotated_corpus/full_corpus.jsonl`
- the final adjudicated annotation outputs
`Sprint_3/data/annotation_final/`

The search index is automatically built from the corpus when the server starts.

---

# Team Report

All members collaborated on human annotation in Label Studio.

### **Wei**
  - Designed and implemented a web interface for corpus search and annotation inspection
  - xxx
  - xx
  
### **Yirui**  
  - Designed adjudication strategies to choose the single best annotation per review
  - Implemented code for adjudication to convert the raw annotation into the final annotation
  - xx
  
### **Freya (the scrum leader this week)**  
  - Implemented annotation input generation, documented the annotation process, and refined the code for adjudication
  - Organized the Sprint_3 repository and defined data storage and reproducibility policies
  - Facilitated workflow and provided ad-hoc support to the team

### **Leah**  
  - Set up Label Studio using a Docker container to provide a centralized annotation environment for the team
  - Enabled automatic annotation by GPT-5 mini model on Label Studio to support the annotation process by providing recommendations
  - Conducted an inter-annotator agreement (IAA) analysis 
  
All major design decisions were discussed collaboratively.  
Pull requests were reviewed by team members prior to merging: 
  - Yirui reviewed Freya's work
  - Freya reviewed Wei’s work
  - Wei reviewed Leah’s work
  - Leah reviewed Yirui’s work
---

# Prompt completion

xx
