import json
import os
from typing import Dict, Iterable, List, Optional, Set


class AnnotationStore:
    """Load adjudicated annotation records and expose normalized helpers.

    The adjudicated JSON files contain one record per annotated review. Each
    record stores the raw review text fields plus span-level attribute and
    sentiment annotations. This class keeps both the original record and a
    normalized list of annotations so the API can support:

    - returning a merged document record for detail views
    - filtering search results by attribute and sentiment
    - returning parsed annotations for annotated search results and detail views
    """

    def __init__(self, folder: str):
        self.records: Dict[str, dict] = {}
        self.annotations: Dict[str, List[dict]] = {}
        self.attribute_labels_by_doc: Dict[str, Set[str]] = {}
        self.sentiments_by_doc: Dict[str, Set[str]] = {}
        self.available_sentiments = ["positive", "negative", "neutral", "unknown"]

        files = [
            "annotated_pair1_adjudicated.json",
            "annotated_pair2_adjudicated.json",
        ]

        for filename in files:
            path = os.path.join(folder, filename)
            if not os.path.exists(path):
                print(f"Annotation file not found: {path}")
                continue

            with open(path, encoding="utf-8") as infile:
                data = json.load(infile)

            for rec in data:
                doc_id = str(rec.get("review_id", ""))
                if not doc_id:
                    continue

                self.records[doc_id] = rec
                parsed = self._parse_record(rec)
                self.annotations[doc_id] = parsed
                self.attribute_labels_by_doc[doc_id] = {
                    item["label"] for item in parsed if item.get("label")
                }
                self.sentiments_by_doc[doc_id] = {
                    item["sentiment"]
                    for item in parsed
                    if item.get("sentiment")
                }

    def _parse_record(self, rec: dict) -> List[dict]:
        parsed: List[dict] = []

        title_spans = rec.get("title_attr_span", []) or []
        title_names = rec.get("title_attr_name", []) or []
        for span, name in zip(title_spans, title_names):
            parsed.append(
                {
                    "section": "title",
                    "text": span.get("text", "") if isinstance(span, dict) else "",
                    "label": name or "",
                    "sentiment": "",
                }
            )

        desc_spans = rec.get("desc_attr_span", []) or []
        desc_names = rec.get("desc_attr_name", []) or []
        for span, name in zip(desc_spans, desc_names):
            parsed.append(
                {
                    "section": "description",
                    "text": span.get("text", "") if isinstance(span, dict) else "",
                    "label": name or "",
                    "sentiment": "",
                }
            )

        review_spans = rec.get("review_attr_span", []) or []
        review_names = rec.get("review_attr_name", []) or []
        review_sentiments = rec.get("sentiment", []) or []

        for i, (span, name) in enumerate(zip(review_spans, review_names)):
            sent = review_sentiments[i] if i < len(review_sentiments) else ""
            parsed.append(
                {
                    "section": "review",
                    "text": span.get("text", "") if isinstance(span, dict) else "",
                    "label": name or "",
                    "sentiment": sent or "",
                }
            )

        return parsed

    def get_annotations(self, doc_id: str) -> List[dict]:
        return self.annotations.get(str(doc_id), [])

    def get_record(self, doc_id: str) -> Optional[dict]:
        return self.records.get(str(doc_id))

    def annotated_doc_ids(self) -> Set[str]:
        return set(self.records.keys())

    def doc_matches(self, doc_id: str, attribute: str = "", sentiment: str = "") -> bool:
        doc_id = str(doc_id)

        if attribute:
            if attribute not in self.attribute_labels_by_doc.get(doc_id, set()):
                return False

        if sentiment:
            if sentiment not in self.sentiments_by_doc.get(doc_id, set()):
                return False

        return True

    def filter_doc_ids(self, attribute: str = "", sentiment: str = "") -> Set[str]:
        candidate_ids = self.annotated_doc_ids()
        return {
            doc_id
            for doc_id in candidate_ids
            if self.doc_matches(doc_id, attribute=attribute, sentiment=sentiment)
        }

    def all_labels(self) -> List[str]:
        labels: Set[str] = set()
        for doc_labels in self.attribute_labels_by_doc.values():
            labels.update(doc_labels)
        return sorted(labels)

    def all_sentiments(self) -> List[str]:
        sentiments: Set[str] = set(self.available_sentiments)
        for doc_sents in self.sentiments_by_doc.values():
            sentiments.update(doc_sents)
        ordered = [sent for sent in self.available_sentiments if sent in sentiments]
        remaining = sorted(sent for sent in sentiments if sent not in set(ordered))
        return ordered + remaining
