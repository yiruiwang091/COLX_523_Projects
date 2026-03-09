# Interface Plan
## (Web Interface for Corpus + Annotations)

# 1. Purpose
We will build a small web interface to help others explore our corpus and our Sprint 3 annotations interactively.

The interface supports:

1) **Search** over the full corpus and display matching texts.
2) **Annotation access** through options such as **“Annotated data only”** and **“Include annotations in results”**.

The frontend collects user inputs (query + options) and sends them to a **FastAPI** backend.

The backend queries a search index and optionally attaches adjudicated annotation outputs for display.

As an early implementation step, we have also started a working prototype using **FastAPI**, **HTML/JavaScript**, and **Whoosh**.

---

# 2. Repo Paths & Data Inputs

## 2.1 Annotation-related data we will consume (read-only in interface)
Our interface treats the following files as upstream outputs.

**Annotation inputs (for context / reproducibility)**

- `Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json`
- `Sprint_3/data/annotation_intermediary/master_1000.csv`
- `Sprint_3/data/annotation_intermediary/annotation_input_sets/` (per-annotator per-round task files)

**Final annotation outputs used by the interface**

- `Sprint_3/data/annotation_final/annotated_pair1_adjudicated.json`
- `Sprint_3/data/annotation_final/annotated_pair2_adjudicated.json`

**Adjudication artifacts**

- `Sprint_3/documentation/adjudication_note.md`
- `Sprint_3/src/adjudication.py` (pipeline script)

> Note: The detailed annotation schema and adjudication rules are documented by teammates.  
> This interface plan only specifies how the interface loads and displays the final outputs.

## 2.2 Corpus data used for search
The interface reads the full corpus JSONL produced by our earlier corpus construction pipeline.

The corpus file is expected to be stored in:

- `data/unannotated_corpus/full_corpus.jsonl`

Each document contains a stable identifier (`review_id`) and text fields such as:

- `title`
- `description`
- `reviewText`

The interface uses `review_id` as the join key to connect corpus documents with annotation records.

---

# 3. User Interface (Front-End)

## 3.1 Page layout (single-page UI)
The interface is a simple single-page search screen titled:

**Amazon Product Reviews Corpus: Coleman**

**Inputs**

- Query box: `q`
- Field dropdown: `All / Title / Description / ReviewText`
- Checkbox A: `Annotated data only`
- Checkbox B: `Include annotations in results`
- Search button

**Results**

For each search result, the interface displays:

- `review_id` (doc_id)
- title (if available)
- a short snippet from the matched text
- if `Include annotations in results` is enabled, a compact annotation summary under the result
- a `View Details` button for optional document-level inspection

The annotation summary is organized by section, such as:

- `reviewText`
- `title`
- `description`

For review annotations, sentiment is also shown when available.

## 3.2 Why this UI

- The interface is intentionally simple so that classmates can quickly explore the corpus during peer review.
- The checkbox design provides a clear way to access annotations without adding complex navigation.
- The section-based annotation display is more readable than showing annotations as raw script-like output.

---

# 4. Backend (FastAPI) Design

## 4.1 High-level architecture

**Browser (HTML/JS) → FastAPI → SearchService + CorpusStore + AnnotationStore → JSON → UI render**

## 4.2 Endpoints

### `GET /`

Serves the main HTML page (and static JS/CSS).

### `GET /api/search`

**Query parameters**

- `q: str` (optional; empty query is allowed in the prototype)
- `field: str` in `{all,title,description,reviewText}` (optional, default `all`)
- `annotated_only: bool` (optional, default `false`)
- `include_annotations: bool` (optional, default `false`)
- `limit: int` (optional, default `20`)

**Response shape**

```json
{
  "query": "tent",
  "field": "all",
  "annotated_only": false,
  "include_annotations": true,
  "results": [
    {
      "doc_id": "R123",
      "title": "...",
      "snippet": "...",
      "score": 12.3,
      "annotations": [
        {
          "section": "reviewText",
          "start": 10,
          "end": 25,
          "span_text": "...",
          "label": "durability",
          "sentiment": "negative"
        }
      ]
    }
  ]
}
```

### `GET /api/doc/{doc_id}` 

Returns the **full document text** and the **full annotation list** for the selected document.

- **Path param**

  - `doc_id` (string): document identifier (we use `review_id` as `doc_id`)

- **Response**

```json
{
  "doc_id": "<string>",
  "doc": {
    "review_id": "<string>",
    "asin": "<string>",
    "title": "<text>",
    "description": "<text>",
    "reviewText": "<text>",
    "overall": "<rating>",
    "cat_l1": "<category_level_1>",
    "cat_l2": "<category_level_2>",
    "cat_l3": "<category_level_3>",
    "cat_l4": "<category_level_4>",
    "cat_l5": "<category_level_5>"
  },
  "annotations": [
    {
      "section": "<title|description|reviewText>",
      "start": "<int>",
      "end": "<int>",
      "span_text": "<text|optional>",
      "label": "<attribute_name>",
      "sentiment": "<positive|negative|neutral|unknown|optional>"
    }
  ]
}
```

---

# 5. Code Modules (Backend) & Responsibilities

We keep the backend modular so that each component has a clear responsibility and can be tested independently.

## 5.1 `CorpusStore` (read corpus + lookup docs)

### Responsibilities

- Load the corpus JSONL at application startup.
- Provide document lookup and iteration for indexing.

### Interface methods

- `get_doc(doc_id) -> dict`
- `iter_docs() -> Iterable[dict]`

### Key assumptions

- Each record includes a stable identifier `doc_id` (e.g., `review_id`)
- Each record contains searchable text fields such as: `title`, `description`, `reviewText`

## 5.2 `AnnotationStore` (read annotation outputs)

### Responsibilities

Load final adjudicated annotation records from:

- `Sprint_3/data/annotation_final/annotated_pair1_adjudicated.json`
- `Sprint_3/data/annotation_final/annotated_pair2_adjudicated.json`

These adjudicated files contain the **final merged annotations after resolving disagreements between annotators**.

The interface uses these adjudicated outputs as the **canonical annotation source for display**.

### Build

- `annotated_doc_ids: set[str]`
- `doc_id -> annotations[]`

### Interface methods

is_annotated(doc_id) -> bool
get_annotations(doc_id) -> list[Annotation]
annotated_doc_ids() -> set[str]

### What the interface displays

Each annotation may contain:

- `section` (title / description / reviewText)
- `start` / `end` (span offsets)
- `span_text` (if available)
- `label` (attribute name)
- `sentiment` (for review spans)

Annotation extraction or normalization may reuse helper functions from:

- `Sprint_3/src/adjudication.py`

The interface **does not re-implement adjudication logic**; it only consumes the produced outputs.

## 5.3 `SearchService` (search / index)

Search is implemented using **Whoosh**.

### Responsibilities

- Build or load a Whoosh index from corpus text fields:
  - `title`
  - `description`
  - `reviewText`
- Execute keyword queries, optionally restricted to a selected field
- Return ranked search results

### Returned fields

- `doc_id`
- `title`
- `score`
- `snippet`

---

# 6. End-to-End Logic (How Options Change Behavior)

## 6.1 Normal search

The UI sends: `/api/search?q=...`

The backend:

1. Runs the query against the corpus search index
2. Returns ranked results with snippets

## 6.2 Annotated data only

The backend:

1. Runs the search normally
2. Filters results using: `doc_id in AnnotationStore.annotated_doc_ids()`

Only documents that have annotation records are returned.

## 6.3 Include annotations in results

The backend:

1. Runs the search query
2. Optionally applies the `annotated_only` filter
3. For each remaining hit, attaches:`AnnotationStore.get_annotations(doc_id)`

The UI then displays a **compact annotation summary under each search result**.

## 6.4 View Details

1. User action: Click `"View Details"`
2. Frontend request: `/api/doc/{doc_id}`
3. Backend response:

  - Full document text
  - Full annotation list

The frontend displays the **detailed document view**.

---

# 7. Implementation Plan (Milestones)

## 7.1 Sprint 3 deliverables

- This interface plan
- A UI mockup image showing:

  - Query input box
  - Field dropdown
  - Annotation checkbox options
  - Example search results
  - Annotation display area

---

## 7.2 Early implementation progress

Current progress includes:

- Created a **FastAPI skeleton** with `/` and `/api/search`
- Implemented initial versions of:

  - `CorpusStore`
  - `AnnotationStore`
  - `SearchService`

- Connected a basic **HTML frontend** to backend search endpoints
- Built an initial **Whoosh-based search prototype**

---

# 8. Justification

The interface is intentionally **minimal** so that classmates can quickly explore the corpus during peer review.

The **checkbox-based annotation access** directly satisfies the assignment requirement to provide an interface that allows users to access annotation information.

Using **adjudicated outputs as the annotation source** improves consistency and avoids exposing unresolved annotator disagreements in the interface.

A **modular backend design** (`CorpusStore`, `AnnotationStore`, `SearchService`) keeps responsibilities clearly separated and makes the system easier to extend in future work, such as:

- Improving the detail view
- Adding annotation statistics
- Refining ranking and display logic
