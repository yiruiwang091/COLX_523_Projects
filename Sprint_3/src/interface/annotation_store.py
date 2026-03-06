import json
import os


class AnnotationStore:

    def __init__(self, folder):
        self.annotations = {}

        files = [
            "annotated_pair1_adjudicated.json",
            "annotated_pair2_adjudicated.json"
        ]

        for f in files:
            path = os.path.join(folder, f)

            if not os.path.exists(path):
                print(f"Annotation file not found: {path}")
                continue

            with open(path, encoding="utf-8") as infile:
                data = json.load(infile)

            for rec in data:
                doc_id = str(rec["review_id"])
                parsed = self._parse_record(rec)
                self.annotations.setdefault(doc_id, []).extend(parsed)

    def _parse_record(self, rec):
        parsed = []

        title_spans = rec.get("title_attr_span", [])
        title_names = rec.get("title_attr_name", [])
        for span, name in zip(title_spans, title_names):
            parsed.append({
                "section": "title",
                "text": span.get("text", ""),
                "label": name,
                "sentiment": ""
            })

        desc_spans = rec.get("desc_attr_span", [])
        desc_names = rec.get("desc_attr_name", [])
        for span, name in zip(desc_spans, desc_names):
            parsed.append({
                "section": "description",
                "text": span.get("text", ""),
                "label": name,
                "sentiment": ""
            })

        review_spans = rec.get("review_attr_span", [])
        review_names = rec.get("review_attr_name", [])
        review_sentiments = rec.get("sentiment", [])

        for i, (span, name) in enumerate(zip(review_spans, review_names)):
            sent = review_sentiments[i] if i < len(review_sentiments) else ""
            parsed.append({
                "section": "review",
                "text": span.get("text", ""),
                "label": name,
                "sentiment": sent
            })

        return parsed

    def get_annotations(self, doc_id):
        return self.annotations.get(str(doc_id), [])

    def annotated_doc_ids(self):
        return set(self.annotations.keys())