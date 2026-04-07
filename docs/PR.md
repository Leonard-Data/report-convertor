Excel Mapping & Reporting Tool (GUI + CLI)
1. Overview

A Python-based application that provides both:

🖥️ GUI (PyQt) for interactive mapping and template creation
💻 CLI for automated report generation using predefined templates

The system allows users to:

Load multiple Excel files
Map their fields to a destination template
Generate a consolidated Excel report
Store and reuse templates via AWS S3
2. Core Concepts
2.1 Template (Central Object)

A template defines:

Destination schema (final report columns)
Mapping rules (source → destination fields)
Source file paths (absolute paths)
Optional transformation rules

📁 Stored as: JSON
☁️ Stored in: AWS S3

Example Template Structure
{
  "template_name": "employee_report_v1",
  "output_file": "output.xlsx",
  "sources": [
    {
      "file_path": "/data/source1.xlsx",
      "sheet_name": "Sheet1"
    }
  ],
  "mappings": [
    {
      "destination_field": "Employee Name",
      "source_file": "source1.xlsx",
      "source_column": "Name"
    }
  ]
}
3. Features
3.1 GUI Application (PyQt)
A. Template Management
Load template:
Local file
From AWS S3
Edit template:
Modify field mappings
Modify source file paths
Adjust destination fields
Save template:
Save locally
Upload to S3
B. Source File Upload
Upload multiple Excel files
Auto-read:
Sheet names
Column headers
Display loaded files in a list panel
C. Mapping Interface (IMPORTANT UX)

Instead of dropdowns:

✅ Use Searchable Selection Box (Searchable ComboBox)

Features:

Type-to-search field names
Filter large column lists instantly
Clean UI (no long dropdown overflow)
Mapping Table Layout:
Destination Field	Source File	Source Column (Searchable)
D. Data Preview
Preview mapped data (first N rows)
Validate mapping before execution
E. Generate Report
Button: "Generate Report"
Actions:
Validate template
Load all source files
Apply mappings
Merge data
Export final Excel
F. Error Feedback (GUI)

Use:

Popup dialogs
Inline validation messages
3.2 CLI Application
A. Run Command (Main)
python app.py run --template <template_name_or_s3_path>

✔ Behavior:

Load template from S3
Read all source file paths from template
Apply mappings
Generate final report
B. List Templates Command ✅ (NEW)
python app.py list

✔ Behavior:

Fetch all templates from S3
Display list:
Available Templates:
- employee_report_v1
- finance_summary_2024
- sales_mapping_template
C. Optional Debug Mode
python app.py run --template xxx --debug
Prints detailed logs
4. Tech Stack
Component	Technology
GUI	PyQt5 / PyQt6
CLI	argparse
Data Processing	pandas
Excel I/O	openpyxl
Cloud Storage	AWS S3 (boto3)
Config Format	JSON
5. System Architecture
            ┌───────────────┐
            │     GUI       │
            └──────┬────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Template Manager │◄──────► AWS S3
          └──────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Mapping Engine   │
          └──────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Source Loader        Validator
        │                     │
        └──────────┬──────────┘
                   ▼
           Report Generator
                   │
                   ▼
              Excel Output
6. Validation & Error Handling (CRITICAL)
A. File Validation
❌ Source file not found
→ "Source file not found: /path/to/file.xlsx"
❌ Template not found in S3
→ "Template not found in S3"
B. Column Validation
❌ Missing column in source file
→ "Column 'Email' not found in source1.xlsx"
C. Template Validation
Missing mapping definitions
Invalid structure
Broken JSON
D. Runtime Handling
Scenario	Behavior
GUI error	Popup + block execution
CLI error	Print error + exit (non-zero code)
7. Workflow
GUI Flow
Load template (local/S3)
Upload Excel files
Map fields (searchable UI)
Preview data
Generate report
Save/update template
CLI Flow
Run command with template name
Load template from S3
Validate:
Files
Columns
Process mapping
Generate final Excel
8. Extensibility (Future Enhancements)
Field transformation rules (e.g., concat, format date)
Template versioning in S3
Drag & drop mapping UI
Scheduling (batch jobs)
Logging system (file + cloud logs)
9. Key Design Principles
✅ Reusable templates (S3-based)
✅ Minimal CLI input (template-driven)
✅ Strong validation
✅ Scalable for large Excel datasets
✅ Clean and searchable UI (no cluttered dropdowns)