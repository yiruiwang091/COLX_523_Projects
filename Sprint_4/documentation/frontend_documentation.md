# Frontend Documentation

## 1. Overview

This front end is a browser-based interface for searching the Coleman Amazon Product Reviews corpus and viewing annotation results returned by the Python back end.

The interface allows users to:

- enter a keyword query
- choose which field to search (`all`, `title`, `description`, or `reviewText`)
- restrict results to annotated documents only
- filter results by annotation attribute
- optionally filter review annotations by sentiment
- sort returned results
- inspect annotation results for title, description, and review text
- view full document details for a selected result

The interface is designed to support interactive exploration of the corpus and to make annotation results easy to inspect visually.

---

## 2. Frontend Files

The frontend implementation consists of the following files:

- `./src/interface/frontend/index.html`
Main interface page containing the search form, filter sidebar, results panel, and document details panel.

- `./src/interface/frontend/styles.css`
Provides layout and visual styling for the interface, including the search bar, filter sidebar, result cards, annotation chips, and highlighted review spans.

- `./src/interface/frontend/app.js`
Implements the client-side logic and communication with the backend. Handles query submission, filter processing, API requests, and result rendering.

- `./ducumentation/frontend_documentation.md`
This document describing the architecture and functionality of the front end.

---

## 3. Technical Structure

The front end is implemented with **HTML, CSS, and JavaScript**.

### 3.1 HTML

The HTML defines the page structure and user interface components, including:

- a **top search bar**
- a **left filter sidebar**
- a **results panel**
- a **document details panel**

The search bar is implemented using an HTML `<form>` element.  
Users can submit queries either by pressing **Enter** or by clicking the **Search** button.

The layout is divided into two main sections:

- **Filter sidebar** – allows users to refine search results
- **Results panel** – displays retrieved documents and annotation information

### 3.2 CSS

The CSS controls the visual appearance and layout of the interface, including:

- page layout and responsive structure
- panel styling
- spacing and alignment
- search/result card appearance
- annotation chip styles
- review span highlighting
- query-match highlighting
- legend styling
- tooltip display
- translucent background styling

Special CSS classes are used to visually distinguish:

- query matches
- sentiment labels (positive / negative / neutral)
- overlapping annotation spans

---

### 3.3 JavaScript

The JavaScript file (`app.js`) handles all client-side interaction and communication with the backend.

Key responsibilities include:

- reading the current query and filter settings from the page
- intercepting form submission and preventing page reload
- sending asynchronous requests to the backend using the **Fetch API**
- receiving JSON results
- dynamically rendering search results
- sorting returned results on the client side
- displaying annotation sections
- highlighting query matches
- rendering review spans with sentiment-based color coding
- fetching and displaying detailed document JSON for a selected result

Event listeners are used to detect changes in filters, sorting options, and form submission.

---

## 4. Backend Interaction

The front end communicates with the **FastAPI backend** using HTTP GET requests.

### 4.1 Search endpoint

The main search request is sent to: `/api/search`

The front end sends the following parameters:

- `q` – the query text
- `field` – the selected search field
- `annotated_only` – whether results must contain annotations
- `attribute` – one or more attribute filters
- `sentiment` – one or more sentiment filters (when enabled)

Multiple attributes or sentiments are transmitted as **repeated query parameters**, which the backend interprets as lists.

Example request:

```text
/api/search?q=tent&field=reviewText&attribute=durability&attribute=waterproofing
```

The backend returns a JSON response containing a list of matching documents.

### 4.2 Document details endpoint

When the user clicks **View Details**, the front end sends a request to: `/api/doc/{doc_id}`

The returned JSON document is displayed in the **document details panel** for inspection.

---

## 5. Annotation Display

If annotation data is available, the front end groups it into three categories:

- title annotations
- description annotations
- review annotations

### 5.1 Title and Description

Annotations for titles and descriptions are displayed as **annotation chips** showing:

- the annotated text span
- the attribute label
- sentiment (when available)

### 5.2 Review Text

Review annotations require more complex rendering.

The front end performs the following steps:

1. read span boundaries from the annotation metadata
2. split the review text into segments
3. check which annotations cover each segment
4. apply sentiment-based highlighting
5. display label and sentiment information on hover
6. render a legend explaining color meanings

Query terms are also highlighted within the review text to help users locate relevant passages.

This approach is necessary because the adjudicated annotation dataset may contain **overlapping spans**, which cannot be rendered correctly using a simple single-pass highlighter.

---

## 6. Extra Interface Features

In addition to the basic search and filtering functionality, the interface includes several usability features:

- sentiment legend explaining color coding
- query-term highlighting in titles, snippets, and review text
- client-side result sorting
- placeholder image fallback for products without images
- translucent themed background styling
- hover tooltips for annotated review spans
- sticky headers for improved navigation
- dynamic filter panels that appear only when needed

These features improve usability and make the corpus easier to explore interactively.

---

## 7. Restrictions / Limitations

The current front end has the following limitations:

1. The interface depends on the FastAPI backend running and responding correctly.
2. The corpus and annotation files must be located in the expected backend directories.
3. The interface is optimized primarily for desktop or laptop browsers.
4. Static assets such as background images and placeholder images must be served correctly.
5. Multi-select attribute and sentiment filtering requires the backend to support repeated query parameters.
6. Review annotation overlap is handled visually, but extremely dense overlap may still be difficult to read.

---

## 8. Testing

The front end was tested through the following procedures:

- running the application locally using FastAPI and Docker
- issuing multiple keyword queries
- testing annotated vs non-annotated searches
- testing attribute and sentiment filters
- testing different sort options
- verifying placeholder image fallback
- verifying query highlighting in titles, snippets, and review text
- testing document detail retrieval
- checking behavior when no results are returned
- verifying error messages when backend requests fail
- testing the interface in different browsers (Google Chrome and Safari)

These tests ensured that the interface functions correctly and that front-end/back-end integration works as expected.