# report-convertor

Local-first Excel mapping and reporting tool with shared `PyQt6` GUI and CLI services.

## Current MVP

- `PyQt6` GUI workflow for creating templates, importing destination headers, uploading source reports, editing mappings, saving drafts, auto-refreshing a review section, and generating reports
- CLI commands for `list`, `run`, and `gui`
- `Pydantic` models for draft and final template validation
- Local JSON template repository
- Excel inspection and report generation via `pandas` + `openpyxl`

## Project Structure

```text
report_convertor/
  models/
  features/
  components/
  functions/
  utils/
tests/
```

## Template Format

```json
{
  "template_name": "employee_report_v1",
  "output_file": "output.xlsx",
  "destination_fields": [
    { "name": "Employee Name" },
    { "name": "Work Email" }
  ],
  "sources": [
    {
      "key": "source1",
      "file_path": "E:\\data\\source1.xlsx",
      "sheet_name": "Sheet1"
    }
  ],
  "mappings": [
    {
      "destination_field": "Employee Name",
      "source_key": "source1",
      "source_column": "Name"
    },
    {
      "destination_field": "Work Email",
      "source_key": null,
      "source_column": null
    }
  ]
}
```

`Save Template` allows incomplete draft mappings. `Generate Report` requires every destination field to be fully mapped.

## GUI Workflow

1. Enter a template name and output file.
2. Add destination fields manually or import them from a workbook header row.
3. Add one or more source reports.
4. Map each destination field to a source file and source column.
5. The review section refreshes automatically in the background when one or more mappings are complete, and refreshes again when mappings change.
6. Save the draft template JSON.
7. Generate the final Excel report.

## Commands

Install dependencies:

```bash
python -m pip install -e .[dev,packaging]
```

List local templates:

```bash
python main.py list --templates-dir templates
```

Preview rows from a template:

```bash
python main.py run --template employee_report_v1 --templates-dir templates --preview-rows 5
```

Generate a report:

```bash
python main.py run --template employee_report_v1 --templates-dir templates --output output.xlsx
```

Launch the GUI:

```bash
python main.py gui --templates-dir templates
```

Run tests:

```bash
pytest
```

Build a distributable executable:

```bash
python -m pip install -e .[packaging]
pyinstaller report_convertor.spec
```

## Versioning

- Use `git` with short-lived feature branches.
- Prefer Conventional Commits such as `feat:`, `fix:`, and `chore:`.
- Tag releases with semantic versions, for example `v0.1.0`.
