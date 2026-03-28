"""HTML report generator for schema comparison results."""

from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from typing import Any, Optional

import os


class HTMLReportGenerator:
    """Generates styled HTML reports from schema comparison results."""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize HTML report generator.

        Args:
            template_dir: Directory containing Jinja2 templates.
                         If None, uses default templates directory.
        """
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(
        self,
        diff_result: dict[str, Any],
        source_db: str,
        target_db: str,
        output_path: str,
    ) -> str:
        """Generate HTML report from comparison result.

        Args:
            diff_result: SchemaDiffResponse dict with comparison results
            source_db: Source database name/identifier
            target_db: Target database name/identifier
            output_path: Path to write HTML file

        Returns:
            Path to generated HTML file
        """
        template = self.env.get_template("report.html")
        html = template.render(
            diff=diff_result,
            source_db=source_db,
            target_db=target_db,
            generated_at=datetime.now(),
            summary=self._generate_summary(diff_result),
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    def _generate_summary(self, diff_result: dict[str, Any]) -> dict[str, Any]:
        """Generate summary statistics from diff result."""
        column_diffs = diff_result.get("column_diffs", [])
        index_diffs = diff_result.get("index_diffs", [])
        constraint_diffs = diff_result.get("constraint_diffs", [])

        # Count by diff type
        def count_by_type(diffs: list[dict]) -> dict[str, int]:
            counts = {"added": 0, "removed": 0, "modified": 0}
            for d in diffs:
                diff_type = d.get("diff_type", "modified")
                if diff_type in counts:
                    counts[diff_type] += 1
            return counts

        return {
            "total_column_diffs": len(column_diffs),
            "total_index_diffs": len(index_diffs),
            "total_constraint_diffs": len(constraint_diffs),
            "total_diffs": len(column_diffs) + len(index_diffs) + len(constraint_diffs),
            "column_counts": count_by_type(column_diffs),
            "index_counts": count_by_type(index_diffs),
            "constraint_counts": count_by_type(constraint_diffs),
            "has_differences": diff_result.get("has_differences", False),
        }
