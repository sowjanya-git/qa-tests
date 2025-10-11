import os
import requests
from pathlib import Path

# Load environment variables from GitHub workflow
jira_base = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
add_links = os.getenv("ADD_REMOTE_LINKS", "false").lower() == "true"

# Get GitHub repo/branch dynamically (from workflow env)
github_repo = os.getenv("GITHUB_REPO", "sowjanya-git/qa-tests")
github_branch = os.getenv("GITHUB_BRANCH", "main")

# Base folder for test cases
test_cases_dir = Path("test-cases")

def extract_jira_key(file_path):
    """Reads file and extracts Jira Keys: value if present"""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().lower().startswith("jira keys:"):
                return line.split(":", 1)[1].strip()
    return None

def create_remote_link(issue_key, github_url, title):
    """Creates remote link in Jira for a given issue"""
    payload = {
        "object": {
            "url": github_url,
            "title": title
        }
    }
    r = requests.post(
        f"{jira_base}/rest/api/3/issue/{issue_key}/remotelink",
        json=payload,
        auth=(jira_email, jira_token),
        headers={"Content-Type": "application/json"}
    )
    if r.status_code == 201:
        print(f"✅ Linked {title} to {issue_key}")
    else:
        print(f"❌ Failed to link {title} to {issue_key}: {r.status_code} {r.text}")

def main():
    if not add_links:
        print("Skipping remote links (ADD_REMOTE_LINKS=false)")
        return

    print(f"🔍 Scanning folder: {test_cases_dir.resolve()}")

    # Find all markdown files in test-cases/
    for md_file in test_cases_dir.rglob("*.md"):
        print(f"📄 Processing file: {md_file}")
        jira_key = extract_jira_key(md_file)
        if not jira_key:
            print(f"⚠️ No Jira key found in {md_file}")
            continue

        # Build GitHub file URL
        relative_path = md_file.as_posix()
        github_url = f"https://github.com/{github_repo}/blob/{github_branch}/{relative_path}"

        print(f"🔗 Preparing to link {md_file.name} → Jira issue {jira_key}")
        create_remote_link(jira_key, github_url, md_file.name)

if __name__ == "__main__":
    main()
