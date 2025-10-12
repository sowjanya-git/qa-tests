import os
import requests
from pathlib import Path

# Jira environment variables from GitHub workflow
jira_base = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
jira_project = os.getenv("JIRA_PROJECT_KEY", "SCRUM")  # Example: your project key

# Base folder for test cases
test_cases_dir = Path("test-cases")

def parse_md(file_path):
    """Reads markdown file and extracts test case fields"""
    fields = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
    return fields

def create_jira_testcase(fields):
    """Creates a Jira Test Case issue from parsed fields"""

    payload = {
        "fields": {
            "project": {"key": jira_project},
            "issuetype": {"name": "Test Case"},
            "summary": f"{fields.get('Test Case ID')} - {fields.get('Test Scenario')}",
            "description": fields.get("Test Description", ""),
            "priority": {"name": fields.get("Priority", "Medium")},

            # Custom fields mapping
            "customfield_10130": fields.get("Expected Result", ""),
            "customfield_10131": fields.get("Actual Result", ""),
            "customfield_10128": fields.get("Test Steps", ""),
            "customfield_10129": fields.get("Test Data", ""),
            "customfield_10126": fields.get("Pre-Conditions", ""),
            "customfield_10124": fields.get("Test Scenario", ""),
            "customfield_10091": fields.get("Status", ""),   # Execution Status
            "customfield_10127": fields.get("Test Type", "")
        }
    }

    # 1. Create the Test Case issue
    resp = requests.post(
        f"{jira_base}/rest/api/3/issue",
        json=payload,
        auth=(jira_email, jira_token),
        headers={"Content-Type": "application/json"}
    )

    if resp.status_code != 201:
        print(f"❌ Failed to create Test Case: {resp.status_code} {resp.text}")
        return None

    issue_key = resp.json()["key"]
    print(f"✅ Created Test Case: {issue_key}")

    # 2. Link it to the parent story if Jira Keys field is provided
    parent_key = fields.get("Jira Keys")
    if parent_key:
        link_payload = {
            "type": {"name": "Relates"},  # you can also use "Tests" if configured in Jira
            "inwardIssue": {"key": issue_key},
            "outwardIssue": {"key": parent_key}
        }

        link_resp = requests.post(
            f"{jira_base}/rest/api/3/issueLink",
            json=link_payload,
            auth=(jira_email, jira_token),
            headers={"Content-Type": "application/json"}
        )

        if link_resp.status_code == 201:
            print(f"🔗 Linked {issue_key} to {parent_key}")
        else:
            print(f"⚠️ Failed to link {issue_key} to {parent_key}: {link_resp.status_code} {link_resp.text}")

    return issue_key

def main():
    print(f"📂 Scanning folder: {test_cases_dir.resolve()}")
    for md_file in test_cases_dir.glob("**/*.md"):
        print(f"➡️ Processing {md_file}")
        fields = parse_md(md_file)
        create_jira_testcase(fields)

if __name__ == "__main__":
    main()
