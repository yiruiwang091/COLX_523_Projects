import json
import os
from typing import Dict, List, Union, Optional, Set

SECTION_TO_TEXT_FIELD = {
    "title": "title",
    "description": "description",
    "review": "reviewText",
}


class AnnotationStore:
    """Load adjudicated annotation records and expose normalized helpers.

    The adjudicated JSON files contain one record per annotated review. Each
    record stores the raw review text fields plus span-level attribute and
    sentiment annotations. This class keeps both the original record and a
    normalized list of annotations so the API can support:

    - returning a merged document record for detail views
    - filtering search results by attribute and sentiment
    - returning parsed annotations for annotated search results and detail views
    - returning section-aware annotation payloads with full text plus spans
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
        parsed.extend(
            self._parse_section(
                section="title",
                spans=rec.get("title_attr_span", []) or [],
                labels=rec.get("title_attr_name", []) or [],
                sentiments=[],
            )
        )
        parsed.extend(
            self._parse_section(
                section="description",
                spans=rec.get("desc_attr_span", []) or [],
                labels=rec.get("desc_attr_name", []) or [],
                sentiments=[],
            )
        )
        parsed.extend(
            self._parse_section(
                section="review",
                spans=rec.get("review_attr_span", []) or [],
                labels=rec.get("review_attr_name", []) or [],
                sentiments=rec.get("sentiment", []) or [],
            )
        )
        return parsed

    def _parse_section(
        self,
        section: str,
        spans: List[dict],
        labels: List[str],
        sentiments: List[str],
    ) -> List[dict]:
        items: List[dict] = []
        for i, (span, label) in enumerate(zip(spans, labels)):
            span = span if isinstance(span, dict) else {}
            items.append(
                {
                    "section": section,
                    "start": span.get("start"),
                    "end": span.get("end"),
                    "text": span.get("text", "") or "",
                    "label": label or "",
                    "sentiment": sentiments[i] if i < len(sentiments) else "",
                }
            )
        return items

    def get_annotations(self, doc_id: str, section: Optional[str] = None) -> List[dict]:
        doc_annotations = self.annotations.get(str(doc_id), [])
        if section is None:
            return doc_annotations
        return [item for item in doc_annotations if item.get("section") == section]

    def get_record(self, doc_id: str) -> Optional[dict]:
        return self.records.get(str(doc_id))

    def get_section_text(self, doc_id: str, section: str) -> str:
        rec = self.get_record(doc_id) or {}
        text_field = SECTION_TO_TEXT_FIELD.get(section, "")
        return str(rec.get(text_field, "") or "")

    def get_annotation_sections(self, doc_id: str) -> Dict[str, dict]:
        doc_id = str(doc_id)
        return {
            section: {
                "text": self.get_section_text(doc_id, section),
                "annotations": self.get_annotations(doc_id, section=section),
            }
            for section in ["title", "description", "review"]
        }

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

    def filter_doc_ids(
        self,
        attribute: Union[str, List[str]] = "",
        sentiment: Union[str, List[str]] = ""
    ) -> Set[str]:
    
        if isinstance(attribute, str):
            attribute = [attribute] if attribute else []
    
        if isinstance(sentiment, str):
            sentiment = [sentiment] if sentiment else []
    
        candidate_ids = self.annotated_doc_ids()
    
        return {
            doc_id
            for doc_id in candidate_ids
            if any(
                self.doc_matches(doc_id, attribute=a, sentiment=s)
                for a in (attribute or [""])
                for s in (sentiment or [""])
            )
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
