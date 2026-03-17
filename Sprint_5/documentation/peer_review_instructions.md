# Overview

Thank you for testing our project. This interface allows users to explore the Coleman Amazon product review corpus through keyword search, field-specific search, annotation filtering, sentiment filtering, sorting, pagination, document detail viewing, and the new **About the Corpus** page for project and corpus information.

# Running the Service

## Option A: Docker Compose (recommended)

This is the easiest and most reproducible way. All you need is Docker Desktop installed.

### Step 1: Navigate to the interface directory

``` bash
cd Sprint_5/src/interface
```

### Step 2: Build and start the container

``` bash
docker compose up --build
```

This will:

-   Build the Docker image from `Dockerfile`
-   Mount `Sprint_5/data/` into the container at `/data` (read-only)
-   Start the FastAPI server on port 8000

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
pip install -r Sprint_5/src/interface/requirements.txt
```

### Step 2: Navigate to the interface directory

``` bash
cd Sprint_5/src/interface
```

### Step 3: Start the server

``` bash
uvicorn app:app --reload
```

The server reads data from `../../data` (i.e. `Sprint_5/data/`) by default.

### Step 4: Open the interface

```         
http://127.0.0.1:8000
```

------------------------------------------------------------------------

# What peer reviewers should try

Please test the following parts of the interface:

1.  Open the app in the browser using the URL and port listed above.
    -   Confirm that the landing page loads successfully.
2.  Test the landing page video.
    -   Verify that the hero video appears on the first page.
    -   Click the play/pause button in the lower-right corner and confirm that the video can be paused and resumed.
3.  Enter the corpus interface.
    -   Click **Explore the review corpus**.
    -   Confirm that the app transitions from the landing page to the main corpus search page.
4.  Test the **About the Corpus** page.
    -   Open the page and confirm that the corpus information sections are displayed correctly, including **Project Overview**, **Data Source**, **Corpus Scope**, **Annotation Layer**, **Reproducibility**, and **Project Information**.
5.  Run a basic keyword search.
    -   Enter a keyword in the search bar and click **Search**.
    -   Confirm that results are returned.
    -   Verify that each result shows a title, snippet, document ID, rating, and relevance score.
6.  Test search-field filtering.
    -   Run the same query using different search fields:
        -   all
        -   title
        -   description
        -   reviewText
    -   Check whether the returned results or rankings change appropriately.
7.  Test annotated-only mode.
    -   Check **Annotated data only**.
    -   Confirm that the attribute filter section becomes visible.
8.  Test attribute filtering.
    -   Select one or more attributes.
    -   Click **Apply Filters**.
    -   Confirm that the annotation results shown in each result match the selected attribute(s).
9.  Test “Select all” for attributes.
    -   Click **Select all** under attributes.
    -   Confirm that all attribute checkboxes become selected.
    -   Uncheck one attribute and verify that the select-all state updates correctly.
10. Test sentiment filtering for review annotations.
    -   Enable **Enable sentiment filter**.
    -   Select positive, negative, or neutral.
    -   Apply filters and confirm that the review annotation display changes accordingly.
11. Test annotation display.
    -   In the results, verify that annotation output is grouped into:
        -   Title
        -   Description
        -   Review
    -   Confirm that highlighted review spans and annotation labels are displayed, and that the mouse cursor changes to a question mark when hovering over the annotated review text.
12. Test the legend.
    -   Confirm that the legend explains:
        -   positive
        -   negative
        -   neutral
        -   overlap
        -   query match
13. Test sorting.
    -   Change sorting to:
        -   Relevance: high to low
        -   Relevance: low to high
        -   Rating: high to low
        -   Rating: low to high
        -   Doc ID: high to low
        -   Doc ID: low to high
    -   Confirm that result ordering changes.
14. Test pagination size.
    -   Change **Results per page** to 10, 20, and 50.
    -   Confirm that the number of displayed results changes.
15. Test page navigation.
    -   Use **Previous** and **Next** buttons.
    -   Enter a page number manually in the page input box.
    -   Confirm that the displayed page changes correctly.
16. Test result details.
    -   Click **View Details** on a result.
    -   Confirm that document details load below the results section.
17. Test clearing filters.
    -   Click **Clear Filters**.
    -   Confirm that the query, filters, sort option, and page size reset to default values.
18. Test scrolling helpers.
    -   Scroll down the page.
    -   Confirm that the **Back to top** button appears.
    -   Click it and verify that it scrolls back to the top.
19. Report any bugs.
    -   Note any broken buttons, missing assets, incorrect filtering behavior, or display issues.
