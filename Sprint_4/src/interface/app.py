import os
from typing import Dict, Optional, Set

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from corpus_store import CorpusStore
from annotation_store import AnnotationStore
from search_service import SearchService


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DATA_DIR = os.environ.get("DATA_DIR", "../../data")


def resolve_corpus_path(data_dir: str) -> str:
    """Find the full corpus file, preferring JSONL but allowing JSON fallback."""
    candidates = [
        os.path.join(data_dir, "unannotated_corpus", "full_corpus.jsonl"),
        os.path.join(data_dir, "unannotated_corpus", "full_corpus.json"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "Could not find full_corpus.jsonl or full_corpus.json under "
        f"{os.path.join(data_dir, 'unannotated_corpus')}"
    )


def build_services(data_dir: str):
    corpus = CorpusStore(resolve_corpus_path(data_dir))
    annotations = AnnotationStore(os.path.join(data_dir, "annotation_final"))
    searcher = SearchService(corpus)
    return corpus, annotations, searcher


corpus, annotations, searcher = build_services(DATA_DIR)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/options")
def get_options():
    return {
        "attributes": annotations.all_labels(),
        "sentiments": annotations.all_sentiments(),
        "fields": ["all", "title", "description", "reviewText"],
    }


@app.get("/api/search")
def search(
    query: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    field: str = "all",
    annotated_only: bool = False,
    attribute: str = "",
    sentiment: str = "",
):
    query_text = (query if query is not None else q) or ""
    attribute = (attribute or "").strip()
    sentiment = (sentiment or "").strip()

    allowed_doc_ids = _build_allowed_doc_ids(
        annotated_only=annotated_only,
        attribute=attribute,
        sentiment=sentiment,
    )

    results = searcher.search(
        query_text=query_text,
        field=field,
        allowed_doc_ids=allowed_doc_ids,
        limit=20,
    )

    attach_annotations = bool(annotated_only or attribute or sentiment)

    enriched_results = []
    for result in results:
        doc_id = str(result["doc_id"])
        merged_doc = _merge_doc(doc_id)

        payload = {
            **result,
            "description": merged_doc.get("description", ""),
            "reviewText": merged_doc.get("reviewText", ""),
            "overall": merged_doc.get("overall"),
            "imageURL": merged_doc.get("imageURL"),
        }

        if attach_annotations:
            payload["annotations"] = annotations.get_annotations(doc_id)
            payload["annotation_sections"] = annotations.get_annotation_sections(doc_id)

        enriched_results.append(payload)

    return {
        "query": query_text,
        "field": field,
        "annotated_only": annotated_only,
        "attribute": attribute,
        "sentiment": sentiment,
        "results": enriched_results,
    }


@app.get("/api/doc/{doc_id}")
def get_doc(doc_id: str):
    merged_doc = _merge_doc(doc_id)
    if merged_doc is None:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return {
        "doc": merged_doc,
        "annotations": annotations.get_annotations(doc_id),
        "annotation_sections": annotations.get_annotation_sections(doc_id),
    }


def _build_allowed_doc_ids(
    annotated_only: bool = False,
    attribute: str = "",
    sentiment: str = "",
) -> Optional[Set[str]]:
    needs_annotation_filter = bool(annotated_only or attribute or sentiment)
    if not needs_annotation_filter:
        return None

    if attribute or sentiment:
        doc_ids = annotations.filter_doc_ids(attribute=attribute, sentiment=sentiment)
    else:
        doc_ids = annotations.annotated_doc_ids()

    return set(doc_ids)


def _merge_doc(doc_id: str) -> Optional[Dict]:
    doc_id = str(doc_id)
    corpus_doc = corpus.get_doc(doc_id)
    annotation_doc = annotations.get_record(doc_id)

    if corpus_doc is None and annotation_doc is None:
        return None

    merged = {}
    if corpus_doc:
        merged.update(corpus_doc)
    if annotation_doc:
        merged.update(annotation_doc)
        if corpus_doc and "imageURL" in corpus_doc:
            merged["imageURL"] = corpus_doc.get("imageURL")

    return merged
