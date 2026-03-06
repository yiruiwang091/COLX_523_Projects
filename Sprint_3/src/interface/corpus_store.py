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
import json


class CorpusStore:

    def __init__(self, path):
        self.docs = {}

        with open(path, encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                doc_id = str(doc.get("review_id", ""))
                self.docs[doc_id] = doc

    def get_doc(self, doc_id):
        return self.docs.get(str(doc_id))

    def iter_docs(self):
        return self.docs.values()
