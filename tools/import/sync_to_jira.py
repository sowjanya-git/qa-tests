# tools/sync_to_jira.py
# Reads test-cases/**/*.md, extracts front-matter, groups by "Jira Keys",
# and creates/updates a single comment per Jira issue listing linked tests.

import os, re, json, pathlib, sys
from datetime import datetime
import requests
import yaml

REPO = os.environ.get("GITHUB_REPOSITORY", "")
SHA = os.environ.get("GITHUB_SHA", "main")

JIRA_BASE = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_TOKEN = os.environ["JIRA_API_TOKEN"]
ADD_REMOTE_LINKS = os.environ.get("ADD_REMOTE_LINKS", "false").lower() == "true"

ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root
TEST_ROOT = ROOT / "test-cases"

MARKER = "<!-- AUTO:qa-tests-sync -->"  # used to find/update our own comment

session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_TOKEN)
session.headers.update({"Accept":"application/json","Content-Type":"application/json"})

def parse_front_matter(text: str):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return {}
    try:
        end = text.find("\n---", 4)
        if end == -1:
            return {}
        fm = text[4:end]
        data = yaml.safe_load(fm) or {}
        return data
    except Exception:
        return {}

def permalink(rel_path: str) -> str:
    rel_path = rel_path.replace("\\", "/")
    return f"https://github.com/{REPO}/blob/{SHA}/{rel_path}"

def normalize_keys(raw):
    if raw is None:
        return []
    # split on comma/semicolon/whitespace; keep items that look like ABC-123
    parts = re.split(r"[,\s;]+", str(raw))
    keys = [p.strip().upper() for p in parts if re.match(r"^[A-Z][A-Z0-9_]+-\d+$", p.strip().upper())]
    return list(dict.fromkeys(keys))  # unique, keep order

def collect_tests():
    mapping = {}  # issue_key -> list of tests
    for md in TEST_ROOT.rglob("*.md"):
        rel = md.relative_to(ROOT).as_posix()
        text = md.read_text(encoding="utf-8", errors="ignore")
        fm = parse_front_matter(text)

        if not fm:
            continue

        keys = normalize_keys(fm.get("Jira Keys") or fm.get("Jira Key"))
        if not keys:
            continue

        item = {
            "path": rel,
            "url": permalink(rel),
            "feature": str(fm.get("Feature","")).strip(),
            "id": str(fm.get("Test Case ID","")).strip(),
            "scenario": str(fm.get("Test Scenario","")).strip(),
            "priority": str(fm.get("Priority","")).strip(),
            "type": str(fm.get("Test Type","")).strip(),
        }
        for k in keys:
            mapping.setdefault(k, []).append(item)
    return mapping

def find_existing_comment(issue_key):
    url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}/comment?maxResults=100"
    r = session.get(url, timeout=30)
    if r.status_code >= 300:
        print(f"[WARN] Cannot list comments for {issue_key}: {r.status_code} {r.text[:200]}")
        return None
    data = r.json()
    for c in data.get("comments", []):
        body = c.get("body") or ""
        if isinstance(body, dict):
            # New comment format could be an ADF doc; we keep plain text, so ignore
            continue
        if MARKER in str(body):
            return c["id"]
    return None

def build_body(issue_key, tests):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append(MARKER)
    lines.append(f"**🤖 Auto-synced test cases from GitHub** — commit `{SHA[:7]}` at _{ts}_.")
    lines.append("")
    lines.append("**Files mapped by `Jira Keys` in front-matter:**")
    for t in sorted(tests, key=lambda x: (x["feature"], x["id"])):
        title = f"{t['id']} — {t['scenario']}" if t["scenario"] else t["id"]
        lines.append(f"- **{title}**  \n  Feature: {t['feature']} | Priority: {t['priority']} | Type: {t['type']}  \n  [View in GitHub]({t['url']})")
    lines.append("")
    lines.append("_Edit the `Jira Keys` field in the test file to change the mapping._")
    return "\n".join(lines)

def ensure_comment(issue_key, tests):
    body = build_body(issue_key, tests)
    cid = find_existing_comment(issue_key)
    if cid:
        url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}/comment/{cid}"
        r = session.put(url, data=json.dumps({"body": body}), timeout=30)
        action = "updated"
    else:
        url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}/comment"
        r = session.post(url, data=json.dumps({"body": body}), timeout=30)
        action = "created"
    if r.status_code >= 300:
        print(f"[ERROR] Comment not {action} for {issue_key}: {r.status_code} {r.text[:300]}")
    else:
        print(f"[OK] Comment {action} on {issue_key}")

def add_remote_link(issue_key, test_item):
    payload = {
        "object": {
            "url": test_item["url"],
            "title": f"{test_item['id']} — {test_item['scenario']}" if test_item["scenario"] else test_item["id"],
            "icon": {"url16x16": "https://github.githubassets.com/favicons/favicon.png"},
        }
    }
    url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}/remotelink"
    r = session.post(url, data=json.dumps(payload), timeout=30)
    if r.status_code >= 300:
        print(f"[WARN] Could not add remote link to {issue_key}: {r.status_code} {r.text[:200]}")

def main():
    if not TEST_ROOT.exists():
        print(f"No test-cases/ folder found at: {TEST_ROOT}")
        sys.exit(0)

    mapping = collect_tests()
    if not mapping:
        print("No test files with 'Jira Keys' found. Nothing to sync.")
        return

    for key, tests in mapping.items():
        ensure_comment(key, tests)
        if ADD_REMOTE_LINKS:
            for t in tests:
                add_remote_link(key, t)

if __name__ == "__main__":
    main()
