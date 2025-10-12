import os
import requests
from pathlib import Path

# Jira environment variables from GitHub secrets
jira_base = os.getenv("JIRA_BASE_URL")
jira_email = os.getenv("JIRA_EMAIL")
jira_token = os.getenv("JIRA_API_TOKEN")
jira_project = os.getenv("JIRA_PROJECT_KEY", "SCRUM")  # Example: your project key

# Folder containing test cases
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
    """Creates a Jira Test Case issue with proper field mapping"""

    payload = {
        "fields": {
            "project": {"key": jira_project},
            "issuetype": {"name": "Test Case"},
            "summary": f"{fields.get('Test Case ID')} - {fields.get('Test Scenario')}",
            "description": fields.get("Test Description", ""),
            "priority": {"name": fields.get("Priority", "Medium")},

            # Link to parent User Story (important!)
            "parent": {"key": fields.get("Jira Keys")},

            # Custom fields mapping with your confirmed IDs
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

    # Call Jira API
    r = requests.post(
        f"{jira_base}/rest/api/3/issue",
        json=payload,
        auth=(jira_email, jira_token),
        headers={"Content-Type": "application/json"}
    )

    if r.status_code == 201:
        issue_key = r.json()["key"]
        print(f"✅ Created Jira Test Case: {issue_key} under {fields.get('Jira Keys')}")
    else:
        print(f"❌ Failed to create issue: {r.status_code} {r.text}")

def main():
    print(f"🔍 Scanning folder: {test_cases_dir.resolve()}")
    for md_file in test_cases_dir.rglob("*.md"):
        print(f"📄 Processing: {md_file}")
        fields = parse_md(md_file)
        create_jira_testcase(fields)

if __name__ == "__main__":
    main()
