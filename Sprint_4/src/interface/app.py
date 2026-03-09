import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from corpus_store import CorpusStore
from annotation_store import AnnotationStore
from search_service import SearchService

app = FastAPI()

templates = Jinja2Templates(directory="templates")

DATA_DIR = os.environ.get("DATA_DIR", "../../data")

corpus = CorpusStore(f"{DATA_DIR}/unannotated_corpus/full_corpus.jsonl")
annotations = AnnotationStore(f"{DATA_DIR}/annotation_final")
searcher = SearchService(corpus)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/search")
def search(
    q: str = "",
    field: str = "all",
    annotated_only: bool = False,
    include_annotations: bool = False
):
    results = searcher.search(q, field=field)

    if annotated_only:
        annotated_ids = annotations.annotated_doc_ids()
        results = [r for r in results if str(r["doc_id"]) in annotated_ids]

    if include_annotations:
        for r in results:
            r["annotations"] = annotations.get_annotations(str(r["doc_id"]))

    return {
        "query": q,
        "field": field,
        "annotated_only": annotated_only,
        "include_annotations": include_annotations,
        "results": results
    }

@app.get("/api/doc/{doc_id}")
def get_doc(doc_id: str):
    doc = corpus.get_doc(doc_id)
    ann = annotations.get_annotations(doc_id)

    return {
        "doc": doc,
        "annotations": ann
    }
