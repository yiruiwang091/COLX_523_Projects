#!/usr/bin/env python3
"""
Pre-annotate all Label Studio tasks using GPT-5 and Gemini.

Reads the same local annotation_input_sets/*.json files that
setup_labelstudio.py uses, calls both models for every task,
then creates each project (if it doesn't exist yet) and imports
the tasks with predictions already embedded — so annotators see
model suggestions the moment they open any task.

Usage:
    export OPENAI_API_KEY=sk-...
    python Sprint_3/src/preannotate.py

    # Point at public IP instead of localhost:
    python Sprint_3/src/preannotate.py --ls-url http://206.87.233.174:8080

    # Preview LLM output without touching Label Studio:
    python Sprint_3/src/preannotate.py --dry-run

Requirements:
    pip install openai requests
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from pathlib import Path

try:
    import requests
    from openai import AsyncOpenAI
except ImportError:
    sys.exit("Missing deps: pip install openai requests")

# ── Paths (relative to this file) ─────────────────────────────────────────────
SCRIPT_DIR        = Path(__file__).parent
LABEL_CONFIG_PATH = SCRIPT_DIR / "label_config.xml"
DATA_DIR          = SCRIPT_DIR.parent / "data" / "annotation_intermediary" / "annotation_input_sets"

# ── Label Studio credentials ───────────────────────────────────────────────────
LS_URL      = "http://localhost:8080"
LS_EMAIL    = "admin@colx523.com"
LS_PASSWORD = "colx523admin"

PERSONS = ["leah", "freya", "wei", "yirui"]
ROUNDS  = ["round1", "round2"]

# ── Models ─────────────────────────────────────────────────────────────────────
MODELS: dict[str, str] = {
    "gpt-5-mini": "gpt-5-mini",
    "gemini":     "gemini-3-flash-preview",
}

CONCURRENCY = 4   # parallel LLM calls

# ── Prompts ────────────────────────────────────────────────────────────────────
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
- "text" must be a verbatim substring of the corresponding field (title / description / reviewText).
- Use snake_case attribute names (e.g. battery_life, build_quality, water_resistance).
- Sentiment for review_annotations: positive / negative / neutral / unknown.
- Empty lists are fine when nothing is found in a field.
- Return ONLY the JSON object — no prose, no explanation.\
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


# ── Task flattening (mirrors setup_labelstudio.py) ────────────────────────────
def flatten_task(task: dict) -> dict:
    """Merge meta fields into data, add cat_chain, replace None → ''."""
    data = dict(task.get("data", {}))
    for k, v in (task.get("meta") or {}).items():
        data[k] = v if v is not None else ""
    parts = [data.get(f"cat_l{i}", "") for i in range(1, 4) if data.get(f"cat_l{i}", "")]
    data["cat_chain"] = " → ".join(parts) if parts else "(no category)"
    return data   # return just the data dict; predictions are added separately


# ── Span localisation ──────────────────────────────────────────────────────────
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


# ── Label Studio result builder ────────────────────────────────────────────────
VALID_SENTIMENTS = {"positive", "negative", "neutral", "unknown"}


def _add_span(
    result: list[dict],
    from_name_label: str,
    from_name_textarea: str,
    to_name: str,
    label_value: str,
    start: int,
    end: int,
    text: str,
    attribute: str,
) -> None:
    """Append a linked (labels + perRegion textarea) pair to result."""
    rid = str(uuid.uuid4())[:8]
    result.append({
        "id": rid, "type": "labels",
        "from_name": from_name_label, "to_name": to_name,
        "value": {"start": start, "end": end, "text": text, "labels": [label_value]},
    })
    result.append({
        "id": rid, "type": "textarea",
        "from_name": from_name_textarea, "to_name": to_name,
        "value": {"text": [attribute]},
    })


def build_ls_result(annotations: dict, task_data: dict) -> list[dict]:
    """Convert LLM annotation dict → Label Studio result list."""
    result: list[dict] = []

    title = task_data.get("title", "")
    for ann in annotations.get("title_annotations", []):
        span = _find_span(title, ann.get("text", ""))
        if span:
            _add_span(result, "title_labels", "title_attr_name", "title_text",
                      "attribute_mention", span[0], span[1], title[span[0]:span[1]],
                      ann.get("attribute", ""))

    desc = task_data.get("description", "")
    for ann in annotations.get("description_annotations", []):
        span = _find_span(desc, ann.get("text", ""))
        if span:
            _add_span(result, "desc_labels", "desc_attr_name", "desc_text",
                      "attribute_mention", span[0], span[1], desc[span[0]:span[1]],
                      ann.get("attribute", ""))

    review = task_data.get("reviewText", "")
    for ann in annotations.get("review_annotations", []):
        span = _find_span(review, ann.get("text", ""))
        if not span:
            continue
        sentiment = ann.get("sentiment", "unknown")
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "unknown"
        _add_span(result, "review_labels", "review_attr_name", "review_text",
                  sentiment, span[0], span[1], review[span[0]:span[1]],
                  ann.get("attribute", ""))

    return result


# ── LLM call ──────────────────────────────────────────────────────────────────
async def call_model(client: AsyncOpenAI, model_id: str, task_data: dict) -> dict:
    """Call one model; return parsed annotation dict or {} on failure."""
    try:
        resp = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _make_user_message(task_data)},
            ],
            reasoning_effort="low",
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as exc:
        print(f"    [warn] {model_id}: {exc}", file=sys.stderr)
        return {}


# ── Per-task async worker ──────────────────────────────────────────────────────
async def annotate_one(
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    task_data: dict,
) -> list[dict]:
    """Return a list of LS prediction dicts (one per model) for this task."""
    predictions = []
    async with sem:
        for label, model_id in MODELS.items():
            annotations = await call_model(client, model_id, task_data)
            result = build_ls_result(annotations, task_data)
            if result:
                predictions.append({
                    "model_version": f"{label}-preannotation",
                    "result": result,
                    "score": 0.8,
                })
    return predictions


# ── Label Studio helpers ───────────────────────────────────────────────────────
def ls_login(ls_url: str) -> requests.Session:
    sess = requests.Session()
    page = sess.get(f"{ls_url}/user/login/")
    csrf = sess.cookies.get("csrftoken", "")
    if not csrf:
        m = re.search(r'csrfmiddlewaretoken["\s]+value=["\']([^"\']+)', page.text)
        csrf = m.group(1) if m else ""
    sess.post(
        f"{ls_url}/user/login/",
        data={"email": LS_EMAIL, "password": LS_PASSWORD, "csrfmiddlewaretoken": csrf},
        headers={"Referer": f"{ls_url}/user/login/"},
        allow_redirects=True,
    )
    sess.headers.update({
        "X-CSRFToken": sess.cookies.get("csrftoken", ""),
        "Referer": ls_url,
    })
    return sess


def get_or_create_project(sess: requests.Session, ls_url: str,
                           title: str, label_config: str) -> int:
    """Return existing project id, or create one and return the new id."""
    r = sess.get(f"{ls_url}/api/projects?page_size=100")
    r.raise_for_status()
    data = r.json()
    for p in data.get("results", data if isinstance(data, list) else []):
        if p["title"] == title:
            print(f"  [exists] '{title}' (id={p['id']})")
            return p["id"]

    r = sess.post(f"{ls_url}/api/projects", json={
        "title": title,
        "label_config": label_config,
        "description": (
            "COLX523 Sprint 3 — Attribute-Level Sentiment Annotation. "
            "Highlight attribute mentions in Title/Description (mention only) "
            "and in Review Text (with sentiment). "
            "Pre-annotations from GPT-5 and Gemini are available in the Predictions panel."
        ),
    })
    if r.status_code not in (200, 201):
        sys.exit(f"Failed to create project '{title}': {r.status_code} {r.text[:300]}")
    pid = r.json()["id"]
    print(f"  [created] '{title}' (id={pid})")
    return pid


def import_tasks(sess: requests.Session, ls_url: str,
                 pid: int, tasks: list[dict]) -> None:
    """POST tasks (with embedded predictions) to Label Studio."""
    r = sess.post(f"{ls_url}/api/projects/{pid}/import", json=tasks)
    if r.status_code not in (200, 201):
        print(f"  [warn] import returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return
    result = r.json()
    n = result.get("task_count", result.get("imported_task_count", "?"))
    print(f"  [imported] {n} tasks with pre-annotations")


# ── Main ───────────────────────────────────────────────────────────────────────
async def main(ls_url: str, concurrency: int, dry_run: bool) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set.\nRun:  export OPENAI_API_KEY=sk-...  then retry.")

    client = AsyncOpenAI(api_key=api_key, base_url="https://xingjiabiapi.com/v1")

    label_config = LABEL_CONFIG_PATH.read_text(encoding="utf-8")

    print(f"Authenticating with Label Studio at {ls_url} ...")
    sess = ls_login(ls_url)
    print("  OK\n")

    sem = asyncio.Semaphore(concurrency)

    for person in PERSONS:
        for rnd in ROUNDS:
            json_path = DATA_DIR / f"{person}_{rnd}_labelstudio.json"
            if not json_path.exists():
                print(f"[skip] missing file: {json_path.name}")
                continue

            title = f"COLX523_S3 — {person} {rnd}"
            print(f"\n{'='*55}")
            print(f"  {person} / {rnd}")

            # Load and flatten tasks (same as setup_labelstudio.py)
            raw_tasks = json.loads(json_path.read_text(encoding="utf-8"))
            flat_data = [flatten_task(t) for t in raw_tasks]
            print(f"  {len(flat_data)} tasks — calling {list(MODELS.keys())} ...")

            # Call LLMs for all tasks concurrently
            predictions_per_task = await asyncio.gather(*[
                annotate_one(sem, client, td) for td in flat_data
            ])

            if dry_run:
                total_regions = sum(
                    sum(len(p["result"]) // 2 for p in preds)
                    for preds in predictions_per_task
                )
                print(f"  [dry-run] would upload {total_regions} regions across "
                      f"{len(flat_data)} tasks")
                continue

            # Build LS import payload: tasks with inline predictions
            ls_tasks = [
                {"data": td, "predictions": preds}
                for td, preds in zip(flat_data, predictions_per_task)
            ]

            pid = get_or_create_project(sess, ls_url, title, label_config)
            import_tasks(sess, ls_url, pid, ls_tasks)

    if not dry_run:
        print(f"\n{'='*55}")
        print(f"Done. Open {ls_url} to start annotating.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pre-annotate Label Studio tasks using GPT-5 and Gemini."
    )
    parser.add_argument("--ls-url", default=LS_URL,
                        help=f"Label Studio URL (default: {LS_URL})")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY,
                        help=f"Parallel LLM calls (default: {CONCURRENCY})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Call LLMs and print stats but do not touch Label Studio")
    args = parser.parse_args()
    asyncio.run(main(args.ls_url, args.concurrency, args.dry_run))
