# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python [conda env:base] *
#     language: python
#     name: conda-base-py
# ---

# %%
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
import os
import shutil


class SearchService:

    def __init__(self, corpus):

        self.corpus = corpus

        schema = Schema(
            doc_id=ID(stored=True),
            title=TEXT(stored=True),
            description=TEXT(stored=True),
            reviewText=TEXT(stored=True)
        )

        index_dir = "index"

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
                reviewText=str(doc.get("reviewText", "") or "")
            )

        writer.commit()

    def search(self, q, field="all"):
        from whoosh.qparser import QueryParser, MultifieldParser

        if field == "all":
            parser = MultifieldParser(
                ["title", "description", "reviewText"],
                schema=self.ix.schema
            )
        else:
            parser = QueryParser(field, schema=self.ix.schema)

        query = parser.parse(q)

        results = []

        with self.ix.searcher() as searcher:
            hits = searcher.search(query, limit=20)

            for hit in hits:
                snippet = (
                    hit.get("reviewText", "")[:120]
                    or hit.get("description", "")[:120]
                    or hit.get("title", "")
                )

                results.append({
                    "doc_id": hit["doc_id"],
                    "title": hit.get("title", ""),
                    "snippet": snippet,
                    "score": float(hit.score)
                })
                
        return results