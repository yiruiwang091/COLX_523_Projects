# Sprint 5 README

## Project title

Amazon Product Reviews Corpus: Coleman

## Sprint overview

In Sprint 5, we prepared our annotated corpus and interface for distribution and peer review.\
Our goal was to package the backend, frontend, and corpus files so that reviewers can run the project locally and test the interface in a consistent way.

This sprint focuses on:

-   organizing the repository for submission,
-   preparing Docker-based distribution,
-   writing reviewer instructions,
-   and making sure the interface is ready for peer testing.

## Repository structure

```         
Sprint_5/
├── data/
│   ├── annotation_final/
│   └── unannotated_corpus/
├── documentation/
│   └── instructor_instructions.md
│   └── Team_Freya_Leah_Yirui_Wei_peer_review_instructions.md
├── src/
│   └── interface/
│       ├── app.py
│       ├── annotation_store.py
│       ├── corpus_store.py
│       ├── search_service.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── templates/
│       └── frontend/
│           ├── index.html
│           ├── app.js
│           ├── styles.css
│           ├── video.mp4
│           ├── forest.jpg
│           └── placeholder.svg
├── Sprint_5_README.md
└── .gitignore
```
