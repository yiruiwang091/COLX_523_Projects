import os
import shutil
from typing import Dict, Iterable, Optional, Set

from whoosh.fields import ID, Schema, TEXT
from whoosh.index import create_in
from whoosh.qparser import MultifieldParser, QueryParser


class SearchService:
    """Whoosh-backed text search over title, description, and review text."""

    def __init__(self, corpus, index_dir: str = "index"):
        self.corpus = corpus
        self.index_dir = index_dir

        schema = Schema(
            doc_id=ID(stored=True),
            title=TEXT(stored=True),
            description=TEXT(stored=True),
            reviewText=TEXT(stored=True),
        )

        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)
        os.mkdir(index_dir)

        self.ix = create_in(index_dir, schema)
        writer = self.ix.writer()

        for doc in corpus.iter_docs():
            writer.add_document(
                doc_id=str(doc.get("review_id", "")),
                title=str(doc.get("title", "") or ""),
                description=str(doc.get("description", "") or ""),
                reviewText=str(doc.get("reviewText", "") or ""),
            )

        writer.commit()

    def search(
        self,
        query_text: str,
        field: str = "all",
        allowed_doc_ids: Optional[Set[str]] = None,
        limit: int = 20,
    ):
        query_text = (query_text or "").strip()

        if not query_text:
            return self.browse(allowed_doc_ids=allowed_doc_ids, limit=limit)

        if field not in {"all", "title", "description", "reviewText"}:
            field = "all"

        if field == "all":
            parser = MultifieldParser(
                ["title", "description", "reviewText"], schema=self.ix.schema
            )
        else:
            parser = QueryParser(field, schema=self.ix.schema)

        query = parser.parse(query_text)
        results = []

        with self.ix.searcher() as searcher:
            search_limit = None if allowed_doc_ids is not None else limit
            hits = searcher.search(query, limit=search_limit)

            for hit in hits:
                doc_id = hit["doc_id"]
                if allowed_doc_ids is not None and doc_id not in allowed_doc_ids:
                    continue

                doc = self.corpus.get_doc(doc_id) or {}
                results.append(
                    {
                        "doc_id": doc_id,
                        "title": hit.get("title", "") or doc.get("title", "") or "",
                        "snippet": self._make_snippet(doc, field=field),
                        "score": float(hit.score),
                    }
                )

                if len(results) >= limit:
                    break

        return results

    def browse(self, allowed_doc_ids: Optional[Set[str]] = None, limit: int = 20):
        doc_ids = allowed_doc_ids if allowed_doc_ids is not None else set(self.corpus.iter_doc_ids())

        def sort_key(doc_id: str):
            return (0, int(doc_id)) if str(doc_id).isdigit() else (1, str(doc_id))

        results = []
        for doc_id in sorted(doc_ids, key=sort_key)[:limit]:
            doc = self.corpus.get_doc(doc_id) or {}
            results.append(
                {
                    "doc_id": str(doc_id),
                    "title": doc.get("title", "") or "",
                    "snippet": self._make_snippet(doc, field="all"),
                    "score": 0.0,
                }
            )
        return results

    def _make_snippet(self, doc: Dict, field: str = "all", max_len: int = 180) -> str:
        ordered_fields = []
        if field in {"title", "description", "reviewText"}:
            ordered_fields.append(field)
        ordered_fields.extend(["reviewText", "description", "title"])

        seen = set()
        for name in ordered_fields:
            if name in seen:
                continue
            seen.add(name)
            value = str(doc.get(name, "") or "").strip()
            if value:
                return value[:max_len]
        return ""
