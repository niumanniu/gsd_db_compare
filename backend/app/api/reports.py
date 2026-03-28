"""Report generation API endpoints."""

import os
import tempfile
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.api import SchemaDiffResponse
from app.reports import HTMLReportGenerator, ExcelReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/html")
async def generate_html_report(
    diff_result: SchemaDiffResponse,
    source_db: str,
    target_db: str,
) -> FileResponse:
    """Generate HTML report from comparison result.

    Args:
        diff_result: Schema comparison result
        source_db: Source database name
        target_db: Target database name

    Returns:
        Downloadable HTML file
    """
    generator = HTMLReportGenerator()
    output_path = tempfile.mktemp(suffix=".html")

    try:
        generator.generate(
            diff_result=diff_result.model_dump(),
            source_db=source_db,
            target_db=target_db,
            output_path=output_path,
        )

        return FileResponse(
            output_path,
            media_type="text/html",
            filename="comparison_report.html",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate HTML report: {str(e)}",
        )
    finally:
        # Clean up temp file
        if os.path.exists(output_path):
            os.remove(output_path)


@router.post("/excel")
async def generate_excel_report(
    diff_result: SchemaDiffResponse,
    source_db: str,
    target_db: str,
) -> FileResponse:
    """Generate Excel report from comparison result.

    Args:
        diff_result: Schema comparison result
        source_db: Source database name
        target_db: Target database name

    Returns:
        Downloadable Excel file (.xlsx)
    """
    generator = ExcelReportGenerator()
    output_path = tempfile.mktemp(suffix=".xlsx")

    try:
        generator.generate(
            diff_result=diff_result.model_dump(),
            source_db=source_db,
            target_db=target_db,
            output_path=output_path,
        )

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="comparison_report.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel report: {str(e)}",
        )
    finally:
        # Clean up temp file
        if os.path.exists(output_path):
            os.remove(output_path)
