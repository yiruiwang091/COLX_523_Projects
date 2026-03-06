#!/usr/bin/env python3
"""
Set up Label Studio projects for COLX523 Sprint 3 annotation.

Creates one project per (person, round) combination:
  leah_round1, leah_round2, freya_round1, freya_round2,
  wei_round1,  wei_round2,  yirui_round1, yirui_round2

Each project gets the annotation config from label_config.xml
and its corresponding JSON tasks imported.

Usage:
    python Sprint_3/src/setup_labelstudio.py

Requirements:
    pip install requests
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: run  pip install requests  then retry.")

# ── Config ────────────────────────────────────────────────────────────────────
LS_URL = "http://localhost:8080"
LS_EMAIL = "admin@colx523.com"
LS_PASSWORD = "colx523admin"

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "annotation_intermediary" / "annotation_input_sets"
LABEL_CONFIG_PATH = SCRIPT_DIR / "label_config.xml"

PERSONS = ["leah", "freya", "wei", "yirui"]
ROUNDS = ["round1", "round2"]
# ──────────────────────────────────────────────────────────────────────────────


def wait_for_labelstudio(timeout: int = 120) -> None:
    """Poll until Label Studio is accepting connections."""
    print(f"Waiting for Label Studio at {LS_URL} ...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{LS_URL}/health", timeout=3)
            if r.status_code == 200:
                print(" ready!")
                return
        except requests.exceptions.ConnectionError:
            pass
        print(".", end="", flush=True)
        time.sleep(3)
    sys.exit(f"\nLabel Studio did not start within {timeout}s. Check `docker-compose logs`.")


def get_token(session: requests.Session) -> None:
    """Authenticate using CSRF-aware login (stores session cookies in-place)."""
    # Step 1: GET the login page to receive the CSRF cookie
    login_page = session.get(f"{LS_URL}/user/login/")
    if login_page.status_code != 200:
        sys.exit(f"Could not reach login page ({login_page.status_code}). Is Label Studio running?")

    # Step 2: Extract CSRF token from the cookie jar
    csrf_token = session.cookies.get("csrftoken", "")
    if not csrf_token:
        # Try scraping it from the HTML as fallback
        import re
        match = re.search(r'csrfmiddlewaretoken["\s]+value=["\']([^"\']+)', login_page.text)
        csrf_token = match.group(1) if match else ""

    if not csrf_token:
        sys.exit("Could not find CSRF token. Check that Label Studio is fully initialized.")

    # Step 3: POST login with CSRF token
    r = session.post(
        f"{LS_URL}/user/login/",
        data={
            "email": LS_EMAIL,
            "password": LS_PASSWORD,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={"Referer": f"{LS_URL}/user/login/"},
        allow_redirects=True,
    )
    # A successful login redirects to "/" or "/projects" (200 after redirect)
    if r.status_code not in (200, 302) or "login" in r.url:
        sys.exit(
            f"Login failed ({r.status_code}). "
            "Make sure the container is up and credentials match docker-compose.yml.\n"
            f"Final URL: {r.url}"
        )

    # Session cookies are now set; subsequent requests use cookie-based auth


def project_exists(session: requests.Session, title: str) -> int | None:
    """Return project id if a project with this title already exists, else None."""
    r = session.get(f"{LS_URL}/api/projects")
    if r.status_code != 200:
        return None
    for proj in r.json().get("results", r.json() if isinstance(r.json(), list) else []):
        if proj.get("title") == title:
            return proj["id"]
    return None


def create_project(session: requests.Session, title: str, label_config: str) -> int:
    """Create a Label Studio project and return its id."""
    existing_id = project_exists(session, title)
    if existing_id:
        print(f"  [skip] Project '{title}' already exists (id={existing_id})")
        return existing_id

    r = session.post(
        f"{LS_URL}/api/projects",
        json={
            "title": title,
            "label_config": label_config,
            "description": (
                "COLX523 Sprint 3 — Attribute-Level Sentiment Annotation\n"
                "Highlight attribute mentions in Title/Description (mention only) "
                "and in Review Text (with sentiment: positive / negative / neutral / unknown).\n"
                "Enter the attribute name for each highlighted span."
            ),
        },
    )
    if r.status_code not in (200, 201):
        sys.exit(f"Failed to create project '{title}': {r.status_code} {r.text[:300]}")
    pid = r.json()["id"]
    print(f"  [created] Project '{title}' (id={pid})")
    return pid


def flatten_task(task: dict) -> dict:
    """Merge meta fields into data so they're accessible in the label config.

    None values are replaced with "" so Label Studio's Text tags don't reject them.
    A pre-computed 'cat_chain' field is added for easy category display.
    """
    data = dict(task.get("data", {}))
    meta = task.get("meta", {})
    for k, v in meta.items():
        data[k] = v if v is not None else ""
    # Pre-build the category breadcrumb so the label config can use $cat_chain directly
    parts = [data.get(f"cat_l{i}", "") for i in range(1, 4) if data.get(f"cat_l{i}", "")]
    data["cat_chain"] = " → ".join(parts) if parts else "(no category)"
    return {"data": data}


def import_tasks(session: requests.Session, project_id: int, json_path: Path) -> None:
    """Import tasks from a JSON file into a project."""
    raw_tasks = json.loads(json_path.read_text(encoding="utf-8"))
    tasks = [flatten_task(t) for t in raw_tasks]

    r = session.post(
        f"{LS_URL}/api/projects/{project_id}/import",
        json=tasks,
    )
    if r.status_code not in (200, 201):
        print(f"  [warn] Import returned {r.status_code}: {r.text[:200]}")
    else:
        result = r.json()
        imported = result.get("task_count", result.get("imported_task_count", "?"))
        print(f"  [imported] {imported} tasks → project id={project_id}")


def main() -> None:
    label_config = LABEL_CONFIG_PATH.read_text(encoding="utf-8")

    wait_for_labelstudio()

    session = requests.Session()
    get_token(session)   # authenticates; CSRF + session cookies now in session
    # Label Studio 1.22+ disables legacy token auth; use session cookies for all API calls.
    # Always send the updated CSRF token header.
    csrf = session.cookies.get("csrftoken", "")
    session.headers.update({"X-CSRFToken": csrf, "Referer": LS_URL})
    print("Authenticated via session.")

    print("\nSetting up projects:")
    project_urls: list[str] = []

    for person in PERSONS:
        for rnd in ROUNDS:
            title = f"COLX523_S3 — {person} {rnd}"
            json_path = DATA_DIR / f"{person}_{rnd}_labelstudio.json"

            if not json_path.exists():
                print(f"  [skip] Missing data file: {json_path}")
                continue

            print(f"\n{person} / {rnd}")
            pid = create_project(session, title, label_config)
            import_tasks(session, pid, json_path)
            project_urls.append(f"  {title:40s} → {LS_URL}/projects/{pid}/")

    print("\n" + "=" * 60)
    print("All projects ready. Project URLs (local):")
    for url in project_urls:
        print(url)
    print("\nAdmin UI:   ", LS_URL)
    print("Login:      ", LS_EMAIL)
    print("Password:   ", LS_PASSWORD)
    print("\nTo share with teammates, replace 'localhost' with your WiFi IP.")
    print("Find your Windows WiFi IP: run  ipconfig  in Windows CMD.")
    print("=" * 60)


if __name__ == "__main__":
    main()
