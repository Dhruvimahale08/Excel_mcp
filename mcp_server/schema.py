# mcp_server/schema.py

DROPDOWNS = {
    "Department": ["Web", "AI", "HR", "Finance", "Operations"],
    "Designation": ["Intern", "Junior", "Senior", "Lead"],
    "Salary_Band": ["L1", "L2", "L3"],
    "Skill_Level": ["Beginner", "Intermediate", "Expert"],
    "Promotion_Eligibility": ["Yes", "No"],
    "Is_Processed": ["Yes", "No"]
}

REQUIRED_COLUMNS = [
    "Emp_ID",
    "Name",
    "DOJ",
    "Experience_Years",
    "Role",
    "Status",
    "Department",
    "Designation",
    "Salary_Band",
    "Promotion_Eligibility",
    "Is_Processed",
    "Last_Processed_On",
    "Processing_Version",
    "AI_Decision_Reason",
    "Rule_Applied",
    "Confidence_Score"
]

# Optional columns that may exist
OPTIONAL_COLUMNS = [
    "Skill_Level",
]
