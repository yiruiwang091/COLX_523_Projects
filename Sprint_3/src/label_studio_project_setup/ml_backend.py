#!/usr/bin/env python3
"""
Label Studio ML Backend — live pre-annotation via GPT-5 or Gemini.

Implements the Label Studio ML backend protocol so it can be connected
directly in Project Settings → Model → Add Model.

Endpoints:
    GET  /health   →  {"status": "UP"}
    POST /predict  →  {"results": [{"result": [...], "score": 0.8}]}

Environment variables:
    OPENAI_API_KEY   required
    MODEL_ID         model sent to the API  (default: gpt-5)
    MODEL_LABEL      human-readable name    (default: gpt-5)
    PORT             port to listen on      (default: 9090)

Label Studio connects to this service by the Docker Compose service name,
e.g. http://ml-backend-gpt5:9090  or  http://ml-backend-gemini:9091
"""

from __future__ import annotations

import json
import os
import re
import uuid

import uvicorn
from fastapi import FastAPI, Request
from openai import AsyncOpenAI

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_ID          = os.getenv("MODEL_ID",          "gpt-5-mini")
MODEL_LABEL       = os.getenv("MODEL_LABEL",       "gpt-5-mini")
REASONING_EFFORT  = os.getenv("REASONING_EFFORT",  "low")
PORT        = int(os.getenv("PORT", "9090"))

_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        _client = AsyncOpenAI(api_key=api_key, base_url="https://xingjiabiapi.com/v1")
    return _client

# ── Prompts ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert annotator for attribute-level sentiment analysis of Amazon product reviews.

Identify ATTRIBUTE MENTIONS: specific product features or qualities such as
battery_life, size, weight, price, durability, build_quality, performance,
ease_of_use, design, waterproofing, material, warranty, assembly, etc.

Return ONLY a JSON object in exactly this structure (no markdown fences, no extra keys):
{
  "title_annotations": [
    {"text": "<exact substring from TITLE>", "attribute": "<snake_case name>"}
  ],
  "description_annotations": [
    {"text": "<exact substring from DESCRIPTION>", "attribute": "<snake_case name>"}
  ],
  "review_annotations": [
    {
      "text": "<exact substring from REVIEW>",
      "attribute": "<snake_case name>",
      "sentiment": "<positive|negative|neutral|unknown>"
    }
  ]
}

Rules:
- "text" must be a verbatim substring of the corresponding field.
- Use snake_case attribute names (e.g. battery_life, build_quality).
- Sentiment for review_annotations: positive / negative / neutral / unknown.
- Empty lists are fine when nothing is found.
- Return ONLY the JSON object.\
"""


def _make_user_message(task_data: dict) -> str:
    cat = task_data.get("cat_chain") or "(no category)"
    return (
        f"Category: {cat}\n"
        f"Rating: {task_data.get('overall', '?')}/5\n\n"
        f"TITLE: {task_data.get('title', '')}\n\n"
        f"DESCRIPTION: {task_data.get('description', '')}\n\n"
        f"REVIEW: {task_data.get('reviewText', '')}"
    )


# ── Span helpers ──────────────────────────────────────────────────────────────
VALID_SENTIMENTS = {"positive", "negative", "neutral", "unknown"}


def _find_span(text: str, substring: str) -> tuple[int, int] | None:
    if not substring:
        return None
    idx = text.find(substring)
    if idx >= 0:
        return idx, idx + len(substring)
    idx = text.lower().find(substring.lower())
    if idx >= 0:
        return idx, idx + len(substring)
    return None


def _add_span(result, from_label, from_textarea, to_name,
              label_value, start, end, text, attribute):
    rid = str(uuid.uuid4())[:8]
    result.append({
        "id": rid,
        "type": "labels",
        "from_name": from_label,
        "to_name": to_name,
        "readonly": False,
        "hidden": False,
        "value": {"start": start, "end": end, "text": text, "labels": [label_value]},
    })
    result.append({
        "id": rid,
        "type": "textarea",
        "from_name": from_textarea,
        "to_name": to_name,
        "readonly": False,
        "hidden": False,
        "value": {"text": [attribute]},
    })
    return rid


def build_ls_result(annotations: dict, task_data: dict) -> list[dict]:
    result: list[dict] = []

    title = task_data.get("title", "")
    for ann in annotations.get("title_annotations", []):
        span = _find_span(title, ann.get("text", ""))
        if span:
            _add_span(result, "title_labels", "title_attr_name", "title_text",
                      "attribute_mention", span[0], span[1],
                      title[span[0]:span[1]], ann.get("attribute", ""))

    desc = task_data.get("description", "")
    for ann in annotations.get("description_annotations", []):
        span = _find_span(desc, ann.get("text", ""))
        if span:
            _add_span(result, "desc_labels", "desc_attr_name", "desc_text",
                      "attribute_mention", span[0], span[1],
                      desc[span[0]:span[1]], ann.get("attribute", ""))

    review = task_data.get("reviewText", "")
    for ann in annotations.get("review_annotations", []):
        span = _find_span(review, ann.get("text", ""))
        if not span:
            continue
        sentiment = ann.get("sentiment", "unknown")
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "unknown"
        rid = _add_span(result, "review_labels", "review_attr_name", "review_text",
                        "attribute_mention", span[0], span[1],
                        review[span[0]:span[1]], ann.get("attribute", ""))
        result.append({
            "id": rid,
            "type": "choices",
            "from_name": "sentiment",
            "to_name": "review_text",
            "readonly": False,
            "hidden": False,
            "value": {"choices": [sentiment]},
        })

    return result


# ── LLM call ──────────────────────────────────────────────────────────────────
async def call_model(task_data: dict) -> tuple[list[dict], str | None]:
    """Call the configured model. Returns (result, error_message)."""
    import traceback
    try:
        resp = await get_client().chat.completions.create(
            model=MODEL_ID,
            reasoning_effort=REASONING_EFFORT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _make_user_message(task_data)},
            ],
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        annotations = json.loads(raw)
        if not isinstance(annotations, dict):
            raise ValueError(f"LLM returned {type(annotations).__name__} instead of dict: {raw[:200]}")
        return build_ls_result(annotations, task_data), None
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[error] {MODEL_ID}:\n{tb}")
        return [], str(exc)


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title=f"COLX523 ML Backend — {MODEL_LABEL}")


@app.get("/health")
async def health():
    return {"status": "UP"}


@app.post("/setup")
async def setup(request: Request):
    """Called by Label Studio when connecting the backend."""
    return {"model_version": MODEL_LABEL, "status": "ok"}


@app.get("/test")
async def test():
    """Returns a hardcoded sample prediction — use to verify LS can parse the format."""
    sample_result = []
    _add_span(sample_result, "review_labels", "review_attr_name", "review_text",
              "positive", 0, 11, "Great value", "price")
    _add_span(sample_result, "title_labels", "title_attr_name", "title_text",
              "attribute_mention", 0, 6, "Cooler", "design")
    return {"results": [{"result": sample_result, "score": 0.9, "model_version": MODEL_LABEL}]}


@app.post("/predict")
async def predict(request: Request):
    body = await request.json()
    tasks = body if isinstance(body, list) else body.get("tasks", [])

    results = []
    for task in tasks:
        task_data = task.get("data", {})
        if not task_data.get("cat_chain"):
            parts = [task_data.get(f"cat_l{i}", "")
                     for i in range(1, 4) if task_data.get(f"cat_l{i}", "")]
            task_data["cat_chain"] = " → ".join(parts) if parts else "(no category)"

        result, error = await call_model(task_data)
        entry = {"result": result, "score": 0.8, "model_version": MODEL_LABEL}
        if error:
            entry["error"] = error
        results.append(entry)

    return {"results": results}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
