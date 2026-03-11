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

This will: - Build the Docker image from `Dockerfile` - Mount `Sprint_4/data/` into the container at `/data` (read-only) - Start the FastAPI server on port 8000

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

| Endpoint            | Method | Description                                  |
|-----------------------|-------------------|------------------------------|
| `/`                 | GET    | Serves the HTML search interface             |
| `/api/search`       | GET    | Full-text search over the corpus             |
| `/api/doc/{doc_id}` | GET    | Fetch a single document with its annotations |

### `/api/search` query parameters

| Parameter | Type | Default | Description |
|------------------|------------------|------------------|-------------------|
| `q` | str | `""` | Search keyword(s) |
| `field` | str | `"all"` | Field to search: `all`, `title`, `description`, `reviewText` |
| `annotated_only` | bool | `false` | If true, only return annotated documents |
| `include_annotations` | bool | `false` | If true, include annotation records in results |

------------------------------------------------------------------------

# Data Sources

Data in `Sprint_4/data/` is copied from Sprint 3 final outputs:

-   `data/unannotated_corpus/full_corpus.jsonl` — full Coleman product review corpus
-   `data/annotation_final/` — adjudicated annotation files from Sprint 3

------------------------------------------------------------------------

# Notes for Frontend Teammates

-   The backend and frontend are served from the **same container** on port `8000`. You do not need a separate frontend server.
-   The `index.html` template is in `src/interface/templates/`. Edit it there and rebuild the image with `docker compose up --build`.
-   The data directory is mounted as **read-only** inside the container — the container cannot modify the data files.
-   The `DATA_DIR` environment variable controls where the app looks for data. Inside Docker it is set to `/data`. Locally it defaults to `../../data`.

# Front-end Documentation

## Overview

This front end is a browser-based interface for searching the Coleman Amazon Product Reviews corpus and viewing annotation results returned by the Python back end.

The interface allows users to:

-   enter a keyword query
-   choose which field to search (`all`, `title`, `description`, or `reviewText`)
-   restrict results to annotated documents only
-   filter results by annotation attribute
-   optionally filter review annotations by sentiment
-   sort returned results
-   inspect annotation results for title, description, and review text
-   view full document details for a selected result

## Technical Structure

The front end is implemented with HTML, CSS, and JavaScript.

### HTML

The HTML defines the page structure, including:

-   a top search bar
-   a left filter sidebar
-   a results panel
-   a document details panel

### CSS

The CSS controls:

-   page layout
-   panel styling
-   spacing and alignment
-   search/result card appearance
-   annotation chip styles
-   review span highlighting
-   query-match highlighting
-   transparent background styling

### JavaScript

The JavaScript is responsible for:

-   reading the current query and filter settings from the page
-   sending requests to the back end
-   receiving JSON results
-   rendering search results dynamically
-   sorting returned results on the client side
-   displaying annotation sections
-   highlighting query matches
-   rendering review spans with sentiment-based color coding
-   fetching and displaying detailed document JSON for a selected result

## Backend Interaction

The front end communicates with the FastAPI back end using HTTP GET requests.

### Search endpoint

The main search request is sent to: `/api/search`

The front end sends:

-   `q` for the query text
-   `field` for the selected search field
-   `annotated_only` for annotated-only filtering
-   one or more `attribute` values when attribute filters are selected
-   one or more `sentiment` values when sentiment filtering is enabled

### Document details endpoint

When the user clicks **View Details**, the front end sends a request to: `/api/doc/{doc_id}`

The returned JSON is then displayed in the document details panel.

## Annotation Display

If annotation data is available, the front end groups it into:

-   title annotations
-   description annotations
-   review annotations

Title and description annotations are displayed as chips.

Review annotations are displayed by:

1.  reading span boundaries from the annotation metadata
2.  splitting the review text into segments
3.  checking which annotations cover each segment
4.  applying sentiment-based highlighting
5.  showing hover information for label/sentiment
6.  displaying a legend under the review text

This was important because the adjudicated annotation data contains overlapping spans in some cases, so the review view needs more than a simple one-pass highlighter.

## Extra Interface Features

In addition to the basic search/filter functionality, the interface includes:

-   sentiment legend
-   query-term highlighting in titles, snippets, and review text
-   client-side sorting
-   placeholder image fallback for products without images
-   translucent themed background styling
-   hover information for annotated review spans

## Restrictions / Limitations

The current front end has the following restrictions:

1.  It depends on the FastAPI back end running locally and responding correctly.
2.  It depends on the corpus and annotation data being available in the expected directories.
3.  It is designed primarily for desktop/laptop browsers.
4.  Static assets such as the background image and placeholder image must be served correctly.
5.  Multi-select attribute/sentiment filtering depends on the backend handling repeated query parameters correctly.
6.  Review annotation overlap is handled visually, but highly dense overlap may still be hard to read.

## Testing

We tested the front end by:

-   running the app locally through FastAPI/Docker
-   trying multiple search terms
-   testing annotated vs non-annotated searches
-   testing attribute and sentiment filters
-   testing different sort options
-   checking placeholder image fallback
-   checking query highlighting in title, snippet, and review text
-   checking document detail retrieval
