"""Report generator for operations."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports for operations."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir or Path.cwd() / "reports"
        self.output_dir.mkdir(exist_ok=True)

    def generate_operation_report(
        self,
        operation_type: str,
        operation_name: str,
        status: str,
        details: dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> Path:
        """
        Generate a report for an operation.

        Args:
            operation_type: Type of operation
            operation_name: Name of operation
            status: Status (success, failed, etc.)
            details: Operation details
            timestamp: Timestamp (default: now)

        Returns:
            Path to generated report file
        """
        timestamp = timestamp or datetime.now(UTC).isoformat()
        report_id = f"{operation_type}_{operation_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        report = {
            "report_id": report_id,
            "operation_type": operation_type,
            "operation_name": operation_name,
            "status": status,
            "timestamp": timestamp,
            "details": details,
        }

        report_file = self.output_dir / f"{report_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report generated: {report_file}")
        return report_file

    def generate_summary_report(
        self,
        run_name: str,
        statistics: dict[str, Any],
        operations: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> Path:
        """
        Generate summary report for a run.

        Args:
            run_name: Name of the run
            statistics: Statistics dictionary
            operations: List of operations
            errors: List of errors

        Returns:
            Path to generated report file
        """
        report = {
            "run_name": run_name,
            "generated_at": datetime.now(UTC).isoformat(),
            "statistics": statistics,
            "total_operations": len(operations),
            "total_errors": len(errors),
            "operations": operations,
            "errors": errors,
        }

        report_file = self.output_dir / f"summary_{run_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Summary report generated: {report_file}")
        return report_file

    def generate_markdown_report(
        self,
        run_name: str,
        statistics: dict[str, Any],
        operations: list[dict[str, Any]],
        errors: list[dict[str, Any]],
    ) -> Path:
        """
        Generate markdown summary report.

        Args:
            run_name: Name of the run
            statistics: Statistics dictionary
            operations: List of operations
            errors: List of errors

        Returns:
            Path to generated markdown file
        """
        md_content = f"""# Telegram Automation Report

**Run Name:** {run_name}  
**Generated At:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Statistics

- **Total Operations:** {statistics.get('total_operations', 0)}
- **Successful Operations:** {statistics.get('successful_operations', 0)}
- **Failed Operations:** {statistics.get('failed_operations', 0)}
- **Login Attempts:** {statistics.get('login_attempts', 0)}
- **Contacts Added:** {statistics.get('contacts_added', 0)}
- **Groups Created:** {statistics.get('groups_created', 0)}

## Operations

"""
        for op in operations:
            status_emoji = "✅" if op.get("status") == "completed" else "❌" if op.get("status") == "failed" else "⏳"
            md_content += f"### {status_emoji} {op.get('type', 'unknown')}.{op.get('name', 'unknown')}\n\n"
            md_content += f"- **Status:** {op.get('status', 'unknown')}\n"
            md_content += f"- **Timestamp:** {op.get('timestamp', 'unknown')}\n"
            if op.get("error"):
                md_content += f"- **Error:** {op.get('error')}\n"
            md_content += "\n"

        if errors:
            md_content += "## Errors\n\n"
            for error in errors:
                md_content += f"### ❌ {error.get('type', 'unknown')}.{error.get('name', 'unknown')}\n\n"
                md_content += f"- **Error:** {error.get('error', 'Unknown error')}\n"
                md_content += f"- **Timestamp:** {error.get('timestamp', 'unknown')}\n\n"

        report_file = self.output_dir / f"report_{run_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown report generated: {report_file}")
        return report_file

