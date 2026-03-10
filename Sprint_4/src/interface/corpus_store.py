import json
import os
from typing import Dict, Iterable, List, Optional


class CorpusStore:
    """Load the full corpus from either JSONL or JSON array format."""

    def __init__(self, path: str):
        self.path = path
        self.docs: Dict[str, dict] = {}
        self.load(path)

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Corpus file not found: {path}")

        if path.endswith(".jsonl"):
            self._load_jsonl(path)
        elif path.endswith(".json"):
            self._load_json(path)
        else:
            raise ValueError(
                "CorpusStore only supports .jsonl or .json files. "
                f"Received: {path}"
            )

    def _load_jsonl(self, path: str) -> None:
        with open(path, encoding="utf-8") as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                doc_id = str(doc.get("review_id", ""))
                if doc_id:
                    self.docs[doc_id] = doc

    def _load_json(self, path: str) -> None:
        with open(path, encoding="utf-8") as infile:
            data = json.load(infile)

        if not isinstance(data, list):
            raise ValueError("Expected full_corpus.json to contain a list of document objects.")

        for doc in data:
            doc_id = str(doc.get("review_id", ""))
            if doc_id:
                self.docs[doc_id] = doc

    def get_doc(self, doc_id: str) -> Optional[dict]:
        return self.docs.get(str(doc_id))

    def iter_docs(self) -> Iterable[dict]:
        return self.docs.values()

    def iter_doc_ids(self) -> List[str]:
        return list(self.docs.keys())
