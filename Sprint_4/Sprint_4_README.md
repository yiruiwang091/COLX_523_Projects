# Sprint 4 Project Overview

In Sprint 4, the goal is to:

-   Deploy the corpus search interface built in Sprint 3 as a reproducible Docker service.
-   Enable teammates working on frontend development to spin up a local backend environment with a single command.
-   Provide a stable, containerized backend that serves the corpus and annotation data via a FastAPI REST API.

This sprint delivers:

-   A Dockerized FastAPI backend serving the corpus search interface.
-   A `docker-compose.yml` for one-command startup, with data mounted as a read-only volume.
-   A pinned `requirements.txt` for reproducible dependency installation.
-   A `DATA_DIR` environment variable in `app.py` so the service works both inside Docker and in local development.

------------------------------------------------------------------------

# Repo and Data Storage

```         
COLX523_Freya_Leah_Wei_Yirui/
└── Sprint_4/
    ├── data/
    │   ├── unannotated_corpus/
    │   │   ├── full_corpus.jsonl
    │   │   └── full_corpus.json
    │   └── annotation_final/
    │       ├── annotated_pair1_adjudicated.json
    │       ├── annotated_pair1_adjudicated.jsonl
    │       ├── annotated_pair2_adjudicated.json
    │       ├── annotated_pair2_adjudicated.jsonl
    │       ├── pair1_adjudication_conflicts.csv
    │       └── pair2_adjudication_conflicts.csv
    ├── src/
    │   └── interface/
    │       ├── Dockerfile
    │       ├── docker-compose.yml
    │       ├── requirements.txt
    │       ├── app.py
    │       ├── corpus_store.py
    │       ├── annotation_store.py
    │       ├── search_service.py
    │       └── templates/
    │           └── index.html
    ├── documentation/
    │   └── interface_plan.md
    └── Sprint_4_README.md
```

------------------------------------------------------------------------

# Running the Service

## Option A: Docker Compose (recommended for teammates)

This is the easiest and most reproducible way. All you need is Docker Desktop installed.

### Step 1: Navigate to the interface directory

``` bash
cd Sprint_4/src/interface
```

### Step 2: Build and start the container

``` bash
docker compose up --build
```

This will: 
- Build the Docker image from `Dockerfile`
- Mount `Sprint_4/data/` into the container at `/data` (read-only)
- Start the FastAPI server on port 8000

### Step 3: Open the interface

```         
http://localhost:8000
```

### Step 4: Stop the service

``` bash
docker compose down
```

------------------------------------------------------------------------

## Option B: Local development (no Docker)

Use this if you want to run the backend without Docker, e.g. for fast iteration.

### Step 1: Install dependencies

``` bash
pip install -r Sprint_4/src/interface/requirements.txt
```

### Step 2: Navigate to the interface directory

``` bash
cd Sprint_4/src/interface
```

### Step 3: Start the server

``` bash
uvicorn app:app --reload
```

The server reads data from `../../data` (i.e. `Sprint_4/data/`) by default.

### Step 4: Open the interface

```         
http://127.0.0.1:8000
```

------------------------------------------------------------------------

# API Endpoints

| Endpoint | Method | Description |
|-----------------|-----------------|---------------------------------------|
| `/` | GET | Serves the HTML search interface |
| `/api/search` | GET | Search the corpus by keyword, with optional annotation-based filters |
| `/api/doc/{doc_id}` | GET | Fetch a single document with its merged annotation data |
| `/api/options` | GET | Return available dropdown options for fields, attributes, and sentiments |

### `/api/search` query parameters

| Parameter | Type | Default | Description |
|--------------|--------------|--------------|-----------------------------|
| `query` | str | `""` | Search keyword(s) |
| `q` | str | `""` | Backward-compatible alias for `query` |
| `field` | str | `"all"` | Field to search: `all`, `title`, `description`, `reviewText` |
| `annotated_only` | bool | `false` | If true, only return adjudicated documents |
| `attribute` | str | `""` | Filter results by attribute label |
| `sentiment` | str | `""` | Filter results by sentiment: `positive`, `negative`, `neutral`, `unknown` |

------------------------------------------------------------------------

# Data Sources

Data in `Sprint_4/data/` is copied from Sprint 3 final outputs:

-   `data/unannotated_corpus/full_corpus.jsonl` — full Coleman product review corpus
-   `data/annotation_final/` — adjudicated annotation files from Sprint 3

------------------------------------------------------------------------

# Backend implementation

The Sprint 4 backend is implemented as a FastAPI service that supports search and review-level annotation retrieval for the Coleman review corpus. The API supports keyword search over `title`, `description`, and `reviewText`, with optional filtering by `attribute` and `sentiment`, and can also restrict results to the adjudicated subset with `annotated_only=true`. Search is powered by a Whoosh index built from the corpus text fields, while annotation-based filtering is handled through preloaded adjudicated records so the backend does not need to rescan the full dataset on every request.

The backend integrates two data sources. The adjudicated files, `annotated_pair1_adjudicated.json` and `annotated_pair2_adjudicated.json`, are used as the main source for annotation content and review-level metadata such as `overall`. The full corpus file, `full_corpus.jsonl` (or `full_corpus.json` as fallback), is used to provide additional document fields such as `imageURL`, allowing the frontend to display product images in search results.

The API returns enriched search results that include `doc_id`, `title`, `snippet`, `overall`, `imageURL`, `reviewText`, and retrieval score (relevance). When a query is annotation-driven, such as `annotated_only=true` or when `attribute` or `sentiment` filters are used, the backend also returns parsed annotations and section-aware annotation payloads for `title`, `description`, and `review`. For the review section in particular, the backend returns the full `reviewText` together with review annotation spans, labels, and sentiments, so the frontend can render the complete review text and highlight attribute mentions inline.

The backend also provides a document-level endpoint for retrieving a merged annotated review record and its parsed annotations, as well as an options endpoint for frontend dropdowns. Data paths are configured through the `DATA_DIR` environment variable, which is set in Docker Compose and points to the mounted data directory. This keeps the service portable across local and containerized execution while maintaining a consistent project data layout.

---

# Team Report

### **Wei**
  
### **Yirui**  
  
### **Freya**  
  - Updated the backend to match the final interface contract, including keyword search, attribute and sentiment filtering, adjudicated-only search, and enriched search results with ratings and product images.
  - Reworked annotation handling so the API now returns full `reviewText` along with review annotation spans, labels, and sentiments for frontend highlighting.
  - Aligned the backend with the project data layout by using `DATA_DIR` and merging adjudicated annotation data with full-corpus metadata.

### **Leah (the scrum leader this week)**  
  
All major design decisions were discussed collaboratively.  
Pull requests were reviewed by team members prior to merging: 

