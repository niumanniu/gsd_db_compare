---
phase: 02-multi-database-support
plan: 02
type: execute
wave: 2
depends_on: ["01-PLAN"]
files_modified:
  - backend/app/reports/html_generator.py
  - backend/app/reports/excel_generator.py
  - backend/app/reports/__init__.py
autonomous: true
requirements:
  - REPORT-01
  - REPORT-02

must_haves:
  truths:
    - "HTML report generator creates styled comparison reports"
    - "Excel report generator creates .xlsx files with multiple sheets"
    - "Reports include summary statistics and detailed differences"
  artifacts:
    - path: backend/app/reports/html_generator.py
      provides: HTML report generation
      contains: "class HTMLReportGenerator", "generate"
    - path: backend/app/reports/excel_generator.py
      provides: Excel report generation
      contains: "class ExcelReportGenerator", "generate"
  key_links:
    - from: backend/app/reports/html_generator.py
      to: backend/app/comparison/schema.py
      via: "Uses SchemaDiff data"
      pattern: "SchemaDiff"
---

<objective>
Implement HTML and Excel report generation modules.

Purpose: Enable users to export comparison results as shareable reports.
Output: Report generators for HTML and Excel formats.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/02-multi-database-support/CONTEXT.md (Key Decisions - Report Export Format)
@.planning/phases/01-foundation/1-CONTEXT.md (D-5: Diff Data Structure)
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Create HTML report generator</name>
  <files>backend/app/reports/html_generator.py, backend/app/reports/templates/report.html</files>
  <read_first>
    - .planning/phases/02-multi-database-support/CONTEXT.md (Report content requirements)
    - backend/app/comparison/schema.py (SchemaDiff structure)
  </read_first>
  <action>
    Create backend/app/reports/ directory and HTML generator:

    1. Create backend/app/reports/html_generator.py:
       ```python
       from jinja2 import Environment, FileSystemLoader
       from datetime import datetime
       from typing import Dict, Any

       class HTMLReportGenerator:
           def __init__(self, template_dir: str = "templates"):
               self.env = Environment(loader=FileSystemLoader(template_dir))

           def generate(
               self,
               diff_result: Dict[str, Any],
               source_db: str,
               target_db: str,
               output_path: str,
           ) -> str:
               """Generate HTML report from comparison result.

               Returns path to generated file.
               """
               template = self.env.get_template("report.html")
               html = template.render(
                   diff=diff_result,
                   source_db=source_db,
                   target_db=target_db,
                   generated_at=datetime.now(),
               )
               with open(output_path, "w", encoding="utf-8") as f:
                   f.write(html)
               return output_path
       ```

    2. Create backend/app/reports/templates/report.html:
       - HTML5 template with embedded CSS
       - Color coding: green=added, red=removed, yellow=modified
       - Sections:
         - Header with title, databases compared, timestamp
         - Summary cards (total differences by type)
         - Column differences table
         - Index differences table
         - Constraint differences table
       - Collapsible sections using <details>/<summary>
       - Print-friendly styles
  </action>
  <acceptance_criteria>
    - backend/app/reports/html_generator.py exists
    - backend/app/reports/templates/report.html exists
    - HTMLReportGenerator.generate() method works
    - Generated HTML includes all diff types
    - Report includes summary statistics at top
    - Color coding matches UI conventions
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class HTMLReportGenerator|def generate" backend/app/reports/html_generator.py</automated>
  </verify>
  <done>HTML report generator created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Create Excel report generator</name>
  <files>backend/app/reports/excel_generator.py</files>
  <read_first>
    - .planning/phases/02-multi-database-support/CONTEXT.md (Report content requirements)
    - backend/app/comparison/schema.py (SchemaDiff structure)
  </read_first>
  <action>
    Create backend/app/reports/excel_generator.py:

    ```python
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from datetime import datetime
    from typing import Dict, Any, List

    class ExcelReportGenerator:
        def __init__(self):
            self.wb = Workbook()
            self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            self.header_font = Font(bold=True, color="FFFFFF")
            self.added_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Green
            self.removed_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Red
            self.modified_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")  # Yellow

        def generate(
            self,
            diff_result: Dict[str, Any],
            source_db: str,
            target_db: str,
            output_path: str,
        ) -> str:
            """Generate Excel report with multiple sheets.

            Sheets:
            1. Summary - overview and statistics
            2. Column Differences
            3. Index Differences
            4. Constraint Differences

            Returns path to generated file.
            """
            # Remove default sheet
            self.wb.remove(self.wb.active)

            # Create sheets
            self._create_summary_sheet(diff_result, source_db, target_db)
            self._create_diff_sheet(
                "Column Differences",
                diff_result.get("column_diffs", []),
                ["Column", "Diff Type", "Source", "Target", "Differences"],
            )
            self._create_diff_sheet(
                "Index Differences",
                diff_result.get("index_diffs", []),
                ["Index", "Diff Type", "Source", "Target", "Differences"],
            )
            self._create_diff_sheet(
                "Constraint Differences",
                diff_result.get("constraint_diffs", []),
                ["Constraint", "Type", "Diff Type", "Source", "Target", "Differences"],
            )

            self.wb.save(output_path)
            return output_path

        def _create_summary_sheet(...):
            # Summary statistics, comparison metadata

        def _create_diff_sheet(...):
            # Reusable method for difference tables
    ```
  </action>
  <acceptance_criteria>
    - backend/app/reports/excel_generator.py exists
    - ExcelReportGenerator.generate() method works
    - Generated Excel has 4 sheets: Summary, Column Differences, Index Differences, Constraint Differences
    - Header row styled with blue background and white bold text
    - Diff type rows color-coded (green/yellow/red)
    - Summary sheet includes total counts and comparison metadata
  </acceptance_criteria>
  <verify>
    <automated>grep -E "class ExcelReportGenerator|def generate" backend/app/reports/excel_generator.py</automated>
  </verify>
  <done>Excel report generator created</done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Create report module exports and API endpoint</name>
  <files>backend/app/reports/__init__.py, backend/app/api/reports.py</files>
  <read_first>
    - backend/app/reports/html_generator.py
    - backend/app/reports/excel_generator.py
    - backend/app/api/compare.py (pattern reference)
  </read_first>
  <action>
    1. Create backend/app/reports/__init__.py:
       ```python
       from app.reports.html_generator import HTMLReportGenerator
       from app.reports.excel_generator import ExcelReportGenerator

       __all__ = ["HTMLReportGenerator", "ExcelReportGenerator"]
       ```

    2. Create backend/app/api/reports.py:
       ```python
       from fastapi import APIRouter, HTTPException
       from fastapi.responses import FileResponse
       from app.schemas.api import SchemaDiffResponse
       from app.reports import HTMLReportGenerator, ExcelReportGenerator
       import tempfile
       import os

       router = APIRouter(prefix="/api/reports", tags=["reports"])

       @router.post("/html")
       def generate_html_report(diff_result: SchemaDiffResponse, source_db: str, target_db: str):
           """Generate HTML report from comparison result."""
           generator = HTMLReportGenerator()
           output_path = tempfile.mktemp(suffix=".html")
           try:
               generator.generate(diff_result.dict(), source_db, target_db, output_path)
               return FileResponse(output_path, media_type="text/html", filename="comparison_report.html")
           finally:
               if os.path.exists(output_path):
                   os.remove(output_path)

       @router.post("/excel")
       def generate_excel_report(diff_result: SchemaDiffResponse, source_db: str, target_db: str):
           """Generate Excel report from comparison result."""
           generator = ExcelReportGenerator()
           output_path = tempfile.mktemp(suffix=".xlsx")
           try:
               generator.generate(diff_result.dict(), source_db, target_db, output_path)
               return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="comparison_report.xlsx")
           finally:
               if os.path.exists(output_path):
                   os.remove(output_path)
       ```
  </action>
  <acceptance_criteria>
    - backend/app/reports/__init__.py exists with exports
    - backend/app/api/reports.py exists with endpoints
    - POST /api/reports/html returns HTML file
    - POST /api/reports/excel returns Excel file
    - Files cleaned up after response
  </acceptance_criteria>
  <verify>
    <automated>ls backend/app/reports/__init__.py backend/app/reports/html_generator.py backend/app/reports/excel_generator.py backend/app/api/reports.py</automated>
  </verify>
  <done>Report module integrated with API</done>
</task>

</tasks>

<verification>
- HTML report generates with correct styling and content
- Excel report generates with multiple sheets and formatting
- API endpoints return downloadable files
- Reports include all required information from CONTEXT.md
</verification>

<success_criteria>
- backend/app/reports/ contains HTML and Excel generators
- backend/app/api/reports.py provides report generation endpoints
- Generated reports are properly formatted and readable
- Color coding consistent across both formats
</success_criteria>

<output>
After completion, create `.planning/phases/02-multi-database-support/02-multi-database-support-02-SUMMARY.md` with:
- Report generator implementations
- Template structure overview
- Any formatting considerations discovered
</output>
