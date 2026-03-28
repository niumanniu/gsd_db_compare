"""Email template rendering utilities."""

from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path


# Get the directory containing this module
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Create Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_alert_email(
    task_name: str,
    timestamp: str,
    severity: str,
    source_table: str,
    target_table: str,
    diff_count: int,
    report_url: str,
    source_row_count: Optional[int] = None,
    target_row_count: Optional[int] = None,
) -> str:
    """Render the alert email template.

    Args:
        task_name: Scheduled task name
        timestamp: Alert timestamp
        severity: Alert severity level
        source_table: Source table name
        target_table: Target table name
        diff_count: Number of differences
        report_url: URL to detailed report
        source_row_count: Optional source table row count
        target_row_count: Optional target table row count

    Returns:
        Rendered HTML content
    """
    template = jinja_env.get_template("alert_email.html")
    return template.render(
        task_name=task_name,
        timestamp=timestamp,
        severity=severity,
        source_table=source_table,
        target_table=target_table,
        diff_count=diff_count,
        report_url=report_url,
        source_row_count=source_row_count,
        target_row_count=target_row_count,
    )


def render_summary_email(
    report_date: str,
    period_start: str,
    period_end: str,
    total_comparisons: int,
    completed_count: int,
    failed_count: int,
    total_diffs: int,
    critical_diffs: List[Dict[str, Any]],
    recent_records: List[Dict[str, Any]],
    dashboard_url: str,
) -> str:
    """Render the summary email template.

    Args:
        report_date: Report generation date
        period_start: Period start date
        period_end: Period end date
        total_comparisons: Total comparison count
        completed_count: Completed comparison count
        failed_count: Failed comparison count
        total_diffs: Total differences found
        critical_diffs: List of critical difference records
        recent_records: List of recent comparison records
        dashboard_url: URL to dashboard

    Returns:
        Rendered HTML content
    """
    template = jinja_env.get_template("summary_email.html")
    return template.render(
        report_date=report_date,
        period_start=period_start,
        period_end=period_end,
        total_comparisons=total_comparisons,
        completed_count=completed_count,
        failed_count=failed_count,
        total_diffs=total_diffs,
        critical_diffs=critical_diffs,
        recent_records=recent_records,
        dashboard_url=dashboard_url,
    )
