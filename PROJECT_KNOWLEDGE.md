# Report Convertor - Project Knowledge

## Overview

**Report Convertor** is a PyQt6 desktop application that merges multiple Excel source files into consolidated reports using template-based mappings.

---

## Project Structure

```
report-convertor/
├── main.py                          # Entry point
├── report_convertor/
│   ├── functions/                   # CLI and GUI entrypoints
│   │   ├── entrypoint.py           # CLI: list, run, gui commands
│   │   └── gui_app.py              # PyQt6 launcher
│   ├── components/                 # PyQt6 UI widgets
│   │   ├── main_window.py          # MainWindow shell
│   │   ├── template_editor.py      # TemplateEditorWidget (main UI)
│   │   ├── template_editor_controller.py
│   │   ├── template_editor_support.py
│   │   ├── mapping_table.py        # PreviewTableWidget
│   │   ├── editable_mapping_table.py
│   │   ├── source_files_list.py     # SourceFilesWidget
│   │   ├── destination_fields_list.py
│   │   ├── searchable_combo_box.py
│   │   └── review_worker.py        # Background thread worker
│   ├── features/                  # Business logic
│   │   ├── sources/
│   │   │   └── workbook_reader.py    # Read Excel files
│   │   ├── templates/
│   │   │   ├── service.py        # TemplateService
│   │   │   ├── repository.py    # LocalTemplateRepository
│   │   │   └── s3_repository.py
│   │   ├── reports/
│   │   │   ├── generator.py     # ReportGenerator
│   │   │   └── s3_uploader.py
│   │   ├── storage/
│   │   │   ├── s3_report_repository.py
│   │   │   └── config.py       # S3Config
│   │   └── mapping/
│   │       └── preview_service.py
│   ├── models/
│   │   └── template.py         # Pydantic models
│   └── utils/
│       ├── paths.py
│       └── logging.py
├── tests/                         # Test suite
└── .env                         # Configuration
```

---

## Application Flow

### CLI Flow (`entrypoint.py`)

```
┌─────────────────────────────────────────────────────┐
│ main()                                            │
│  ├─ build_parser() → argparse                      │
│  └─ dispatch by command:                          │
│      ├─ "list" → list_templates()                 │
│      ├─ "run"  → run_report()                    │
│      └─ "gui"  → run_gui()                      │
└─────────────────────────────────────────────────────┘
```

### GUI Flow (`gui_app.py` → `main_window.py` → `template_editor.py`)

```
┌─────────────────────────────────────────────────────┐
│ run_gui()                                          │
│  └─ QApplication + MainWindow                      │
│       └─ TemplateEditorWidget                      │
│           ├─ DestinationFieldsWidget             │
│           ├─ SourceFilesWidget                   │
│           ├─ EditableMappingTableWidget           │
│           ├─ PreviewTableWidget                  │
│           └─ ReviewWorker (background thread)      │
└─────────────────────────────────────────────────────┘
```

### Template Editing Flow

```
┌─────────────────────────────────────────────────────┐
│ User Action Sequence:                                │
│  1. Browse/Load Template → load_draft()          │
│  2. Add Source Files    → source_columns cached  │
│  3. Add Dest Fields    → mapping_rows created    │
│  4. Edit Mappings     → schedule_review_refresh │
│  5. Preview          → ReviewWorker thread    │
│  6. Generate         → ReportGenerator.export │
└─────────────────────────────────────────────────────┘
```

---

## Core Functions

### 1. WorkbookReader (`features/sources/workbook_reader.py`)

| Method | Description | Returns |
|--------|-------------|---------|
| `list_sheets(path)` | Get sheet names | `list[str]` |
| `list_columns_from_path(path, sheet?)` | Get column names | `list[str]` |
| `list_columns(source)` | Get columns for SourceFile | `list[str]` |
| `read_frame(source)` | Read sheet as DataFrame | `pd.DataFrame` |
| `read_frame_from_path(path, sheet?)` | Read path as DataFrame | `pd.DataFrame` |

### 2. TemplateService (`features/templates/service.py`)

| Method | Description | Returns |
|--------|-------------|---------|
| `list_templates(dir)` | List template names | `list[str]` |
| `load_template(id, dir)` | Load draft from JSON | `TemplateDraft` |
| `save_template(draft, dir)` | Save draft to JSON | `Path` |
| `build_definition(draft)` | Convert draft to definition | `TemplateDefinition` |
| `import_destination_fields(path, sheet?)` | Read Excel headers | `list[DestinationField]` |
| `create_source(path, existing_keys?, sheet?)` | Create SourceFile with unique key | `SourceFile` |

### 3. ReportGenerator (`features/reports/generator.py`)

| Method | Description | Returns |
|--------|-------------|---------|
| `build_dataframe(template)` | Build full output DataFrame | `pd.DataFrame` |
| `build_review_dataframe(template)` | Build using complete mappings only | `pd.DataFrame` |
| `export(template, output_path?)` | Write to Excel file | `Path` |

### 4. PreviewService (`features/mapping/preview_service.py`)

| Method | Description | Returns |
|--------|-------------|---------|
| `preview_rows(template, row_count)` | Get first N rows as dicts | `list[dict]` |

### 5. S3ReportRepository (`features/storage/s3_report_repository.py`)

| Method | Description | Returns |
|--------|-------------|---------|
| `list_reports()` | List files in S3 folder | `list[str]` |
| `download_report(filename)` | Download to local cache | `Path` |
| `clear_cache(older_than_days?)` | Delete cached files | `int` |

---

## Data Models (`models/template.py`)

### Domain Models

```
DestinationField
├── name: str (required, unique)

SourceFile
├── key: str (required, unique)
├── file_path: str (required)
├── sheet_name: str | None
└── resolved_path: Path (property)

DraftMapping
├── destination_field: str (required)
├── source_key: str | None
├── source_column: str | None
└── is_complete: bool (property)

FieldMapping
├── destination_field: str (required)
├── source_key: str (required)
├── source_column: str (required)
```

### Container Models

```
TemplateDraft (editable JSON)
├── template_name: str
├── output_file: str
├── destination_fields: list[DestinationField]
├── sources: list[SourceFile]
├── mappings: list[DraftMapping]
└── methods:
    ├── ensure_mapping_rows() → self
    └── to_definition() → TemplateDefinition

TemplateDefinition (generation-ready)
├── template_name: str
├── output_file: str
├── sources: list[SourceFile]
├── mappings: list[FieldMapping]
└── source_map: dict[str, SourceFile] (property)
```

---

## UI Components Architecture

### MainWindow (`main_window.py`)

```python
class MainWindow(QMainWindow):
    templates_dir: Path
    editor: TemplateEditorWidget
    # Exposed for testing:
    template_input, preview_rows_input
    summary_label, mappings_table, preview_table
```

### TemplateEditorWidget (`template_editor.py`)

```python
class TemplateEditorWidget(QWidget):
    # Inputs
    template_path_input: QLineEdit
    template_name_input: QLineEdit
    version_combo: QComboBox
    output_file_input: QLineEdit
    preview_rows_input: QSpinBox
    
    # Lists
    destination_fields: DestinationFieldsWidget
    sources: SourceFilesWidget
    
    # Tables
    mapping_editor: EditableMappingTableWidget
    preview_table: PreviewTableWidget
    
    # State
    source_columns: dict[str, list[str]]
    _review_request_id: int
    
    # Background
    _review_thread: QThread
    _review_worker: ReviewWorker
    
    # Methods:
    - load_draft(draft)
    - compose_draft(require_name) → TemplateDraft
    - refresh_source_columns(reader)
    - schedule_review_refresh()
    - sync_editor()
```

### EditableMappingTableWidget (`editable_mapping_table.py`)

| Signal | Payload |
|--------|---------|
| `mapping_changed` | None |

### ReviewWorker (`review_worker.py`)

```
Signals:
- review_ready(request_id, rows)
- review_failed(request_id, message)

Slots:
- generate_review(request_id, draft, row_count)
```

---

## Configuration

### Environment Variables (.env)

```
S3_BUCKET=bob-rpa
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=xxx
S3_SECRET_ACCESS_KEY=xxx
S3_FOLDER=bob-rpa/QA/Templates
S3_REPORT_FOLDER=bob-rpa/QA/
```

### S3Config (`features/storage/config.py`)

```python
class S3Config:
    bucket: str
    region: str
    access_key_id: str
    secret_access_key: str
    folder: str          # Templates folder
    report_folder: str  # Reports folder
    
    @classmethod
    def from_env(cls, env_path?) → S3Config
    def full_key(filename) → str
```

---

## Execution Commands

```bash
# CLI
report-convertor list
report-convertor run --template my-template --output output.xlsx
report-convertor run --template my-template --preview-rows 10

# GUI
report-convertor gui

# Via Python
python main.py gui
python -m report_convertor.gui_app
```

---

## Key Behaviors

### Template Lifecycle

```
1. Create draft → TemplateDraft(template_name="...")
2. Add sources (files) → Add to sources list
3. Add destination fields → Add to destination_fields
4. Map fields → Edit mappings (source_key, source_column)
5. Save → JSON to templates_dir
6. Build → TemplateDefinition (validates completeness)
7. Generate → ReportGenerator.export() → Excel
```

### Validation Rules

| Model | Validation |
|-------|------------|
| `TemplateDraft` | Unique destination field names, unique source keys, mappings reference valid fields, mappings reference known sources |
| `TemplateDefinition` | At least one mapping, source keys in mappings exist in sources |
| `SourceFile` | key and file_path required, path expandable |

### Error Handling

| Error | Raised By | Message |
|-------|----------|--------|
| FileNotFoundError | WorkbookReader | "Source file not found: {path}" |
| ValueError | ReportGenerator | "Column '{col}' not found in {path}" |
| ValueError | TemplateDraft.to_definition() | "Destination field '{field}' is not fully mapped" |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| PyQt6 | UI framework |
| pandas | DataFrame operations |
| openpyxl | Excel file reading/writing |
| boto3 | AWS S3 access |
| pydantic | Data validation |
| python-dotenv | .env loading |

---

## Test Coverage

- **Unit tests**: Models, WorkbookReader, TemplateService
- **Integration tests**: ReportGenerator, S3 operations
- **UI tests**: MainWindow, TemplateEditorWidget (pytest-qt)
- **Total tests**: ~50 tests

---

## Author

Generated for Report Convertor project analysis