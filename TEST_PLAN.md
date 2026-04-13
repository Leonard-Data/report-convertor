# Test Plan - Report Convertor Application

**Date:** 2026-04-11
**Author:** Test Architect
**Status:** Draft

---

## Executive Summary

**Scope:** Full application test plan for Report Convertor - a PyQt-based desktop application for merging Excel source files into consolidated reports using template mappings.

**Risk Summary:**

- Total risks identified: 8
- High-priority risks (≥6): 2
- Critical categories: DATA, TECH

**Coverage Summary:**

- P0 scenarios: 15 (~8 hours)
- P1 scenarios: 22 (~11 hours)
- P2/P3 scenarios: 35 (~10 hours)
- **Total effort**: ~29 hours (~4 days)

---

## Application Overview

### Core Features

1. **Template Management** - Create, edit, save, load template definitions
2. **Source File Reading** - Read Excel workbooks, list sheets, columns
3. **Report Generation** - Build DataFrames from mappings, export to Excel
4. **S3 Storage** - List and download reports from S3 bucket
5. **UI Components** - PyQt-based GUI for template editing and mapping

### Technology Stack

- **Framework:** PyQt6/PySide6
- **Data Processing:** pandas, openpyxl
- **Cloud Storage:** boto3 (AWS S3)
- **Testing:** pytest, pytest-qt

---

## Not in Scope

| Item | Reasoning | Mitigation |
|------|-----------|------------|
| **Legacy Excel formats** (.xls) | Only .xlsx supported | Document in requirements |
| **Password-protected files** | Not supported by pandas | Show clear error message |
| **Macro-enabled workbooks** | Not supported | Document limitation |
| **Network file access** | Local files only | Document in requirements |

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-001 | DATA | Source file missing or corrupted | 2 | 3 | 6 | Validate file exists before read, show clear error | Dev | Sprint 1 |
| R-002 | TECH | Column mismatch between source and mapping | 2 | 3 | 6 | Validate columns exist on load, warn on missing | Dev | Sprint 1 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|--------|-------|------------|-------|
| R-003 | TECH | Large file causes memory issues | 2 | 2 | 4 | Stream processing for large files | Dev |
| R-004 | DATA | Duplicate source keys in template | 1 | 3 | 3 | Validate uniqueness on save | Dev |
| R-005 | OPS | S3 connection failure | 2 | 2 | 4 | Graceful degradation, offline mode |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|--------|-------|--------|
| R-006 | TECH | Race condition in cache | 1 | 2 | 2 | Monitor |
| R-007 | BUS | Export path permission denied | 1 | 2 | 2 | Check permissions early |
| R-008 | OPS | Missing .env configuration | 1 | 1 | 1 | Show setup guide |

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks core journey + High risk (≥6) + No workaround

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|--------------|------------|---------|------------|-------|-------|
| Source file exists | Unit | R-001 | 3 | DEV | Test file not found, invalid path |
| Source file readable | Unit | R-001 | 4 | DEV | Test corrupted Excel |
| Column exists in source | Unit | R-002 | 5 | DEV | Test missing column error |
| Mapping completeness | Unit | R-002 | 3 | DEV | Test incomplete mapping |

**Total P0**: 15 tests, 8 hours

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-4) + Common workflows

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|--------------|------------|---------|------------|-------|-------|
| List sheets from workbook | Unit | R-003 | 3 | DEV | Single/multiple sheets |
| List columns from sheet | Unit | - | 4 | DEV | Empty sheet, many columns |
| Build DataFrame from mapping | Integration | R-002 | 5 | QA | Complete mapping |
| Export to Excel | Integration | R-007 | 4 | QA | Path validation |
| Save template | Integration | R-004 | 3 | DEV | Duplicate key validation |
| Load template | Unit | R-001 | 3 | DEV | JSON parsing |

**Total P1**: 22 tests, 11 hours

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Test Count | Owner | Notes |
|--------------|------------|----------|-------|-------|
| Template model serialization | Unit | 5 | DEV | JSON roundtrip |
| DestinationField model | Unit | 3 | DEV | Validation |
| SourceFile model | Unit | 3 | DEV | Path handling |
| S3 list reports | Integration | 4 | QA | Mock S3 |
| S3 download report | Integration | 5 | QA | Mock S3 |
| WorkbookReader edge cases | Unit | 8 | DEV | Empty file, single row |
| ReportGenerator edge cases | Unit | 7 | DEV | Empty mapping, no sources |

**Total P2**: 35 tests, 10 hours

---

## Entry Criteria

- [ ] Requirements and assumptions agreed upon by QA, Dev, PM
- [ ] Test environment provisioned and accessible
- [ ] Test data available (sample Excel files)
- [ ] pytest-qt installed and configured
- [ ] Mock objects for S3 operations ready

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] Test coverage agreed as sufficient
- [ ] All templates/UI components have test coverage

---

## Test Specifications by Module

### 1. WorkbookReader (`features/sources/workbook_reader.py`)

| Function | Test Cases | Priority | Notes |
|----------|-----------|----------|-------|
| `list_sheets()` | Valid workbook, no sheets, FileNotFoundError | P1 | Test with single/multiple sheets |
| `list_columns_from_path()` | Normal case, empty sheet, missing file | P1 | Test column name types |
| `list_columns()` | Normal case, custom sheet | P0 | SourceFile object |
| `read_frame()` | Normal case, first sheet auto-select | P0 | DataFrame shape |
| `read_frame_from_path()` | FileNotFoundError, sheet not found | P0 | Error handling |

### 2. TemplateService (`features/templates/service.py`)

| Function | Test Cases | Priority | Notes |
|----------|-----------|----------|-------|
| `list_templates()` | Directory exists, empty, missing | P1 | Returns list of names |
| `load_template()` | Valid JSON, invalid JSON, missing file | P0 | Returns TemplateDraft |
| `save_template()` | Valid draft, duplicate key handling | P1 | Creates/updates file |
| `build_definition()` | Complete draft, incomplete draft | P0 | Returns Definition |
| `import_destination_fields()` | Valid file, empty file, no columns | P0 | Returns field list |
| `create_source()` | New key, duplicate key increment | P1 | Unique key generation |

### 3. ReportGenerator (`features/reports/generator.py`)

| Function | Test Cases | Priority | Notes |
|----------|-----------|----------|-------|
| `build_dataframe()` | Complete mapping, all sources present | P0 | Correct data extraction |
| `build_review_dataframe()` | Complete mappings only | P0 | Filters incomplete |
| `export()` | Valid path, create directory, overwrite | P1 | Excel file output |
| `_mapped_series()` | Column exists, column missing | P0 | Error on missing column |

### 4. S3ReportRepository (`features/storage/s3_report_repository.py`)

| Function | Test Cases | Priority | Notes |
|----------|-----------|----------|-------|
| `list_reports()` | Connection success, failure, empty | P1 | Returns sorted list |
| `download_report()` | File exists, file not found, cache hit | P0 | Local cache |
| `clear_cache()` | All files, older than N days | P2 | Cleanup |

### 5. S3Config (`features/storage/config.py`)

| Function | Test Cases | Priority | Notes |
|----------|-----------|----------|-------|
| `from_env()` | All vars present, missing vars | P0 | Loads from .env |
| `full_key()` | Normal case, empty folder | P2 | Key prefix |

### 6. Models (`models/template.py`)

| Model/Class | Test Cases | Priority | Notes |
|-------------|-----------|----------|-------|
| `SourceFile` | Construction, equality | P2 | Data class |
| `DestinationField` | Construction, equality | P2 | Data class |
| `MappingRow` | Complete/incomplete check | P0 | is_complete property |
| `TemplateDraft` | Source/mapping management | P1 | Add/remove sources |
| `TemplateDefinition` | Serialization, validation | P2 | JSON conversion |

### 7. UI Components (PyQt)

| Component | Test Cases | Priority | Notes |
|-----------|-----------|----------|-------|
| MainWindow | Show/hide, close | P1 | qtbot testing |
| TemplateEditor | Load/save template | P1 | Widget interaction |
| MappingTable | Add/edit/delete row | P0 | Table editing |
| SourceFilesList | Add/remove file | P1 | List management |
| DestinationFieldsList | Add/remove field | P1 | List management |
| SearchableComboBox | Filter items | P2 | Combo filtering |

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] WorkbookReader basic read (30s)
- [ ] Template model creation (30s)
- [ ] Service instantiation (30s)
- [ ] Config loading (45s)

**Total**: 4 scenarios

### P0 Tests (<10 min)

**Purpose**: Critical path validation

- [ ] Source file reading (P0)
- [ ] Column validation (P0)
- [ ] Complete mapping (P0)
- [ ] Review DataFrame building (P0)

**Total**: 4 scenarios

### P1 Tests (<30 min)

**Purpose**: Important feature coverage

- [ ] All WorkbookReader methods (P1)
- [ ] Template operations (P1)
- [ ] Export functionality (P1)

**Total**: 3 scenarios

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage

- [ ] S3 operations (P2)
- [ ] Edge cases (P2)
- [ ] UI components (P2/P3)

**Total**: 3 scenarios

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
|----------|-------|------------|-------------|-------|
| P0 | 15 | 0.5 | 8 | Critical path |
| P1 | 22 | 0.5 | 11 | Important features |
| P2 | 35 | 0.25 | 9 | Edge cases, UI |
| **Total** | **72** | **-** | **28** | **~4 days** |

### Prerequisites

**Test Data:**
- Sample Excel files (.xlsx) with various sheet/column configurations
- Mock S3 responses
- Sample template JSON files

**Tooling:**
- pytest + pytest-qt
- pytest-mock
- pytest-cov

**Environment:**
- Python 3.11+
- Windows/macOS
- AWS credentials (for S3 tests)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Core functions**: ≥90%
- **Data models**: ≥80%
- **S3 operations**: ≥70% (can use mocks)
- **UI components**: ≥60%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] File not found errors handled gracefully
- [ ] Column mismatch errors clear and actionable

---

## Mitigation Plans

### R-001: Source file missing or corrupted

**Mitigation Strategy:** Validate file exists before reading. Check file extension. Catch openpyxl errors and convert to clear messages.
**Owner:** Dev Lead
**Timeline:** Sprint 1
**Status:** Planned
**Verification:** P0 tests pass for FileNotFoundError, corrupted file scenarios

### R-002: Column mismatch between source and mapping

**Mitigation Strategy:** Validate all mapped columns exist in source before generation. Show which columns are missing in error message.
**Owner:** Dev Lead
**Timeline:** Sprint 1
**Status:** Planned
**Verification:** P0 tests pass for missing column scenarios

### R-003: Large file causes memory issues

**Mitigation Strategy:** Document file size limits. Consider chunked reading for files > 100MB.
**Owner:** Dev Lead
**Timeline:** Backlog
**Status:** Planned
**Verification:** Performance tests with large files

---

## Assumptions and Dependencies

### Assumptions

1. Excel files are .xlsx format (not .xls)
2. Files fit in memory (< 500MB)
3. Template JSON files are valid UTF-8
4. S3 credentials are provided via .env

### Dependencies

1. pytest-qt - UI testing framework
2. Sample Excel test files - Test data
3. Mock S3 service - For CI/CD testing

### Risks to Plan

- **Risk**: AWS credentials not available in CI
  - **Impact**: S3 tests cannot run
  - **Contingency**: Use moto mock library

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: _________________ Date: ________
- [ ] Tech Lead: _________________ Date: ________
- [ ] QA Lead: _________________ Date: ________

**Comments:**

---

## Appendix

### Knowledge Base References

- `pytest-qt.readthedocs.io` - Qt testing documentation
- `pandas.pydata.org` - DataFrame operations
- `boto3.amazonaws.com` - AWS S3 SDK

### Related Documents

- README.md - Project overview
- requirements.txt - Dependencies
- .env.example - Configuration template

---

**Generated by**: Test Architect
**Version**: 1.0