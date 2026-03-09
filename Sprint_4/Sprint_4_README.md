# Sprint 4 Project Overview

In Sprint 4, the goal is to:

* Deploy the corpus search interface built in Sprint 3 as a reproducible Docker service.
* Enable teammates working on frontend development to spin up a local backend environment with a single command.
* Provide a stable, containerized backend that serves the corpus and annotation data via a FastAPI REST API.

This sprint delivers:

* A Dockerized FastAPI backend serving the corpus search interface.
* A `docker-compose.yml` for one-command startup, with data mounted as a read-only volume.
* A pinned `requirements.txt` for reproducible dependency installation.
* A `DATA_DIR` environment variable in `app.py` so the service works both inside Docker and in local development.

---

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

---

# Running the Service

## Option A: Docker Compose (recommended for teammates)

This is the easiest and most reproducible way. All you need is Docker Desktop installed.

### Step 1: Navigate to the interface directory

```bash
cd Sprint_4/src/interface
```

### Step 2: Build and start the container

```bash
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

```bash
docker compose down
```

---

## Option B: Local development (no Docker)

Use this if you want to run the backend without Docker, e.g. for fast iteration.

### Step 1: Install dependencies

```bash
pip install -r Sprint_4/src/interface/requirements.txt
```

### Step 2: Navigate to the interface directory

```bash
cd Sprint_4/src/interface
```

### Step 3: Start the server

```bash
uvicorn app:app --reload
```

The server reads data from `../../data` (i.e. `Sprint_4/data/`) by default.

### Step 4: Open the interface

```
http://127.0.0.1:8000
```

---

# API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the HTML search interface |
| `/api/search` | GET | Full-text search over the corpus |
| `/api/doc/{doc_id}` | GET | Fetch a single document with its annotations |

### `/api/search` query parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | str | `""` | Search keyword(s) |
| `field` | str | `"all"` | Field to search: `all`, `title`, `description`, `reviewText` |
| `annotated_only` | bool | `false` | If true, only return annotated documents |
| `include_annotations` | bool | `false` | If true, include annotation records in results |

---

# Data Sources

Data in `Sprint_4/data/` is copied from Sprint 3 final outputs:

* `data/unannotated_corpus/full_corpus.jsonl` — full Coleman product review corpus
* `data/annotation_final/` — adjudicated annotation files from Sprint 3

---

# Notes for Frontend Teammates

- The backend and frontend are served from the **same container** on port `8000`. You do not need a separate frontend server.
- The `index.html` template is in `src/interface/templates/`. Edit it there and rebuild the image with `docker compose up --build`.
- The data directory is mounted as **read-only** inside the container — the container cannot modify the data files.
- The `DATA_DIR` environment variable controls where the app looks for data. Inside Docker it is set to `/data`. Locally it defaults to `../../data`.
