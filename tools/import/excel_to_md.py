import pandas as pd
import os

# Input Excel file
excel_file = "../../GitHub Test cases.xlsx"

# Output folder for markdown test cases
output_dir = "test-cases"
os.makedirs(output_dir, exist_ok=True)

# Load Excel
df = pd.read_excel(excel_file)

# Replace NaN with empty string
df = df.fillna("")

for _, row in df.iterrows():
    feature = str(row["Feature"]).strip()
    test_id = str(row["Test Case ID"]).strip()
    jira_keys = str(row["Jira Keys"]).strip()   # <-- NEW FIELD

    # Create subfolder by feature
    feature_dir = os.path.join(output_dir, feature.replace(" ", "_"))
    os.makedirs(feature_dir, exist_ok=True)

    # File name = Test Case ID
    file_name = f"{test_id}.md"
    file_path = os.path.join(feature_dir, file_name)

    # Markdown content
    content = f"""---
Feature: {feature}
Test Case ID: {row['Test Case ID']}
Test Scenario: {row['Test Scenario']}
Test Description: {row['Test Description']}
Pre-Conditions: {row['Pre-Conditions']}
Priority: {row['Priority']}
Test Type: {row['Test Type']}
Defect ID: {row['Defect id']}
Jira Keys: {jira_keys}
---

## Test Steps
{row['Test Steps']}

**Test Data:** {row['Test Data']}

## Expected Result
{row['Expected Result']}

## Actual Result
{row['Actual Result']}

## Status
{row['Status']}

## Comments
{row['Comments']}
"""

    # Save file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"✅ Export complete! Test cases saved in '{output_dir}/' folder.")
