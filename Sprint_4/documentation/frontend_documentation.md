# Frontend Documentation

## 1. Overview

This front end is a browser-based interface for searching the Coleman Amazon Product Reviews corpus and viewing annotation results returned by the Python back end.

The interface supports both a branded landing experience and an interactive corpus exploration interface. When the page first loads, users see a full-screen hero video section with a Coleman-themed introduction. After clicking **Explore the review corpus**, the main corpus search interface is revealed.

The interface allows users to:

- enter a keyword query
- choose which field to search (`all`, `title`, `description`, or `reviewText`)
- restrict results to annotated documents only
- filter results by annotation attribute
- optionally enable sentiment filtering for **review annotations only**
- sort returned results
- change the number of results shown per page
- navigate results using pagination controls
- jump directly to a target results page
- inspect annotation results for title, description, and review text
- view full document details for a selected result
- return to the top of the page using a back-to-top button

The front end is designed to support interactive exploration of the corpus while also providing a more polished and visually engaging user experience.

---

## 2. Frontend Files

The frontend implementation consists of the following files:

- `./src/interface/frontend/index.html`  
  Main interface page containing the hero video section, corpus search form, filter sidebar, results panel, pagination controls, and document details panel.

- `./src/interface/frontend/styles.css`  
  Provides layout and visual styling for the interface, including the hero section, search bar, sidebar filters, sticky results header, result cards, annotation chips, review highlighting, pagination UI, and floating back-to-top button.

- `./src/interface/frontend/app.js`  
  Implements the client-side logic and communication with the backend. Handles query submission, filter processing, pagination, sorting, annotation rendering, page transitions, hero video controls, and document detail retrieval.

- `./documentation/frontend_documentation.md`  
  This document describing the architecture and functionality of the front end.

In addition, the interface depends on the following static assets served by the backend:

- `forest.jpg` – background image for the corpus interface
- `placeholder.svg` – fallback image when a product image is missing
- `video.mp4` – hero video displayed on the landing screen

---

## 3. Technical Structure

The front end is implemented with **HTML, CSS, and JavaScript**.

### 3.1 HTML

The HTML defines two major interface layers:

1. **Hero landing section**
2. **Corpus exploration section**

#### Hero section

The page initially displays a full-screen video banner with:

- a background video
- a dark overlay for readability
- the Coleman brand title
- a short tagline
- an **Explore the review corpus** button
- a video play/pause toggle button

This section provides a branded entry point before the user enters the search interface.

#### Corpus section

After the user clicks the enter button, the corpus interface becomes visible. It includes:

- a large title banner
- a top search bar
- a left filter sidebar
- a results panel
- pagination controls
- a document details panel

The search bar is implemented using an HTML `<form>` element. Users can submit a query by pressing **Enter** or by clicking the **Search** button.

The sidebar contains:

- search field selection
- annotation-only toggle
- attribute filters
- sentiment filter toggle
- review sentiment options
- apply / clear buttons

The results area contains:

- a sticky results header
- results summary text
- results-per-page selector
- sort selector
- annotation legend
- result cards
- pagination controls
- document details output

Static assets are loaded using FastAPI-generated paths such as:

- `{{ url_for('frontend', path='styles.css') }}`
- `{{ url_for('frontend', path='app.js') }}`
- `{{ url_for('frontend', path='video.mp4') }}`

This ensures that frontend assets are served correctly by the backend.

---

### 3.2 CSS

The CSS controls the visual appearance and layout of the interface, including:

- full-page background styling
- hero video layout and overlay
- animated transition between hero section and corpus section
- page title banner styling
- search bar styling
- sidebar layout and sticky positioning
- results panel styling
- sticky results header
- result card layout
- annotation chip styles
- review span highlighting
- query-match highlighting
- legend styling
- tooltip display
- pagination styling
- document details panel styling
- floating back-to-top button
- responsive behavior for smaller screens

Special CSS classes are used to visually distinguish:

- query matches
- positive / negative / neutral review spans
- overlapping annotation spans
- muted system messages
- error messages

The styling also uses:

- translucent panels
- blurred backgrounds
- rounded card layouts
- responsive grid-based result card layout

This creates a cleaner and more polished presentation while preserving readability.

---

### 3.3 JavaScript

The JavaScript file (`app.js`) handles all client-side interaction and communication with the backend.

Key responsibilities include:

- waiting for `DOMContentLoaded` before initializing the interface
- reading the current query and filter settings from the page
- intercepting form submission and preventing page reload
- sending asynchronous requests to the backend using the **Fetch API**
- receiving JSON search results
- storing all returned results in memory
- sorting results on the client side
- paginating results on the client side
- rendering the current page of results
- updating pagination controls
- allowing page jump via number input
- showing and hiding filter groups dynamically
- managing the “select all attributes” checkbox state
- rendering annotation sections
- highlighting query matches
- rendering review spans with sentiment-based color coding
- handling overlapping review annotations
- displaying tooltips and review legends
- fetching and displaying detailed document JSON for a selected result
- managing the hero video play/pause control
- animating the transition from hero section to corpus section
- showing or hiding the back-to-top button based on scroll position

Event listeners are used for:

- form submission
- checkbox and radio selection changes
- sorting changes
- page-size changes
- previous / next page buttons
- page jump input
- scroll events
- hero video toggle
- enter corpus button
- back-to-top button

---

## 4. Interface Flow

### 4.1 Initial page load

When the page first loads, the user sees the hero video section instead of the corpus interface.

The hero section includes:

- autoplaying muted looped video
- a pause/play control
- branding and tagline
- a button to enter the corpus interface

### 4.2 Entering the corpus interface

When the user clicks **Explore the review corpus**:

1. the hidden corpus section is revealed
2. a transition animation is triggered
3. the hero section fades/slides out
4. the page scroll is reset to the top

This creates a more polished transition into the search environment.

### 4.3 Searching the corpus

Users can enter a query and submit it through the search form. The front end collects the current filter settings, sends them to the backend, and renders the returned results.

### 4.4 Exploring results

Users can then:

- sort the results
- change results per page
- move to the next or previous page
- jump directly to a page number
- inspect annotation results
- open full document details

---

## 5. Backend Interaction

The front end communicates with the **FastAPI backend** using HTTP GET requests.

### 5.1 Search endpoint

The main search request is sent to: `/api/search`

The front end sends the following parameters:

- `q` – the query text  
- `field` – the selected search field  
- `annotated_only` – whether results must contain annotations  
- `attribute` – one or more attribute filters  
- `sentiment` – one or more sentiment filters, only when the review sentiment filter is enabled  

Multiple attributes or sentiments are transmitted as **repeated query parameters**, which the backend interprets as lists.

Example request:

```text
/api/search?q=tent&field=reviewText&attribute=durability&attribute=waterproofing
```

The backend returns a JSON response containing matching documents, which the front end stores in `allResults`.

### 5.2 Document details endpoint

When the user clicks **View Details**, the front end sends a request to: `/api/doc/{doc_id}`

The returned JSON document is displayed in the **document details panel** for inspection.

---

### 5.3 Static asset serving

Frontend assets are served through FastAPI routes generated with `url_for('frontend', path=...)`. This is used for:

- stylesheet loading  
- JavaScript loading  
- hero video loading  

The placeholder image fallback is referenced as: `/frontend/placeholder.svg`


---

## 6. Search and Filter Logic

### 6.1 Search fields

Users can choose one of four search fields:

- `all`
- `title`
- `description`
- `reviewText`

These values are sent directly to the backend.

### 6.2 Annotated-only toggle

When **Annotated data only** is selected:

- the attribute filter group becomes visible  
- the optional sentiment filter toggle becomes available  

When it is unchecked:

- attribute selections are cleared  
- sentiment filtering is disabled  
- hidden filter groups are reset  

### 6.3 Attribute filtering

Users can select one or more annotation attributes.

A **Select all** checkbox is provided for convenience.

The front end also maintains the correct checked or indeterminate state for the select-all control.

### 6.4 Sentiment filtering

The sentiment filter is applied only to **review annotations**.

Users must first enable **Enable sentiment filter**. Once enabled, the following options become visible:

- `positive`
- `negative`
- `neutral`

If sentiment filtering is disabled, all selected sentiment values are cleared automatically.

### 6.5 Clear filters

The **Clear Filters** button resets:

- query text  
- search field  
- annotated-only toggle  
- attribute filters  
- sentiment filter toggle  
- sentiment selections  
- sort option  
- page size  
- current results  
- details panel  

After clearing, the interface displays a short system message indicating that filters were cleared.

---

## 7. Result Rendering

### 7.1 Client-side sorting

After search results are returned, the front end sorts them on the client side.

Supported sort options include:

- relevance: high to low  
- relevance: low to high  
- rating: high to low  
- rating: low to high  
- doc ID: high to low  
- doc ID: low to high  

If no explicit option is selected, the default is **relevance descending**.

### 7.2 Client-side pagination

Pagination is handled on the client side after results are loaded.

The interface supports:

- configurable results per page  
- previous / next buttons  
- direct page jump input  
- result range text such as:

```text
Showing 1–20 of 83 results
```

When the current page changes, the page is re-rendered without making another backend request.

### 7.3 Results summary

The results header displays a short summary such as:

```text
83 results found for "tent"
```

If no results are returned, the summary is hidden.

---

### 7.4 Result card structure

Each result card displays:

- product image or placeholder image  
- title  
- document ID  
- rating  
- snippet  
- retrieval relevance score  
- annotation result block  
- **View Details** button  

If an image URL is missing or fails to load, the card falls back to the placeholder image automatically.

---

### 7.5 Query highlighting

Query terms are highlighted in:

- titles  
- snippets  
- review text  

The highlighting logic:

1. escapes HTML safely  
2. splits the query into whitespace-separated terms  
3. builds a regular expression  
4. wraps matching spans in a `query-match` class  

---

## 8. Annotation Display

If annotation data is available, the front end groups it into three categories:

- title annotations  
- description annotations  
- review annotations  

### 8.1 Title and Description

Annotations for titles and descriptions are displayed as **annotation chips** showing:

- the annotated text span  
- the attribute label  
- sentiment (when available)  

If no matching annotations exist for a section, the interface shows a muted fallback message.

### 8.2 Review Text

Review annotations require more complex rendering because spans may overlap.

The front end performs the following steps:

1. read span boundaries from the annotation metadata  
2. split the review text into segments  
3. determine which annotations cover each segment  
4. apply sentiment-based highlighting  
5. attach tooltip information  
6. highlight query matches within the review text  
7. render a legend explaining the annotations  

This segmentation approach is necessary because overlapping annotations cannot be rendered correctly using a simple single-pass highlighter.

### 8.3 Sentiment rendering

Review spans are visually distinguished using CSS classes:

- `sentiment-positive`
- `sentiment-negative`
- `sentiment-neutral`

If multiple annotations overlap on the same segment, an additional `overlap` class is added.

### 8.4 Annotation filtering for display

The front end filters annotation display based on the current UI state:

- attribute filters apply to all annotation sections  
- sentiment filters apply only to review annotations when enabled  

If annotations exist in the raw result but do not match the current display filters, the interface shows:

```text
No matching annotations for current filters.
```
---

## 9. Extra Interface Features

In addition to the basic search and filtering functionality, the interface includes several usability features:

- hero video landing page  
- play/pause button for the hero video  
- animated transition into the corpus interface  
- sticky filter sidebar on desktop  
- sticky results header for easier navigation  
- query-term highlighting  
- annotation legend explaining color coding  
- client-side sorting  
- client-side pagination  
- page jump input  
- placeholder image fallback for missing product images  
- tooltip explanation for retrieval relevance  
- hover tooltips for annotated review spans  
- floating back-to-top button  
- responsive layout adjustments for smaller screens  

These features improve usability and make the corpus easier to explore interactively.

---

## 10. Restrictions / Limitations

The current front end has the following limitations:

1. The interface depends on the FastAPI backend running and responding correctly.  
2. The corpus and annotation files must be located in the expected backend directories.  
3. Static assets such as background images, placeholder images, and the hero video must be served correctly.  
4. The interface is optimized primarily for desktop or laptop browsers.  
5. Sorting and pagination are performed on the client side after the full result set is returned.  
6. The sentiment filter applies only to review annotations.  
7. Review annotation overlap is handled visually, but very dense overlap may still be difficult to read.  
8. The document details panel currently displays raw JSON rather than a formatted detail view.  

---

## 11. Testing

The front end was tested through the following procedures:

- loading the page and verifying hero video playback  
- testing the hero video pause/play toggle  
- testing the transition from the hero section to the corpus section  
- issuing multiple keyword queries  
- testing annotated vs non-annotated searches  
- testing attribute filters  
- testing sentiment filters  
- testing different sort options  
- testing results-per-page options  
- testing pagination navigation  
- testing page jump functionality  
- verifying placeholder image fallback  
- verifying query highlighting in titles, snippets, and review text  
- testing document detail retrieval  
- checking behavior when no results are returned  
- verifying error messages when backend requests fail  
- testing the back-to-top button  
- testing the interface in different browsers (Google Chrome and Safari)

These tests ensured that the interface functions correctly and that front-end/back-end integration works as expected.