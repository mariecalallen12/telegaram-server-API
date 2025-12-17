"""Tracer for tracking operations and generating reports."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_global_tracer: Optional["Tracer"] = None


def get_global_tracer() -> Optional["Tracer"]:
    """Get global tracer instance."""
    return _global_tracer


def set_global_tracer(tracer: "Tracer") -> None:
    """Set global tracer instance."""
    global _global_tracer
    _global_tracer = tracer


class Tracer:
    """Tracks operations and generates reports."""

    def __init__(self, run_name: Optional[str] = None):
        """
        Initialize tracer.

        Args:
            run_name: Name for this run
        """
        self.run_name = run_name or f"run-{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self.run_id = self.run_name
        self.start_time = datetime.now(UTC).isoformat()
        self.end_time: Optional[str] = None

        self.operations: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.statistics: dict[str, Any] = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "login_attempts": 0,
            "contacts_added": 0,
            "groups_created": 0,
        }

        self._run_dir: Optional[Path] = None
        self._next_operation_id = 1

    def get_run_dir(self) -> Path:
        """Get or create run directory."""
        if self._run_dir is None:
            runs_dir = Path.cwd() / "telegram_runs"
            runs_dir.mkdir(exist_ok=True)

            self._run_dir = runs_dir / self.run_name
            self._run_dir.mkdir(exist_ok=True)

        return self._run_dir

    def log_operation(
        self,
        operation_type: str,
        operation_name: str,
        status: str = "started",
        details: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> int:
        """
        Log an operation.

        Args:
            operation_type: Type of operation (login, contact, group, etc.)
            operation_name: Name of the operation
            status: Status (started, completed, failed)
            details: Additional details
            error: Error message if failed

        Returns:
            Operation ID
        """
        operation_id = self._next_operation_id
        self._next_operation_id += 1

        operation = {
            "id": operation_id,
            "type": operation_type,
            "name": operation_name,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "details": details or {},
            "error": error,
        }

        self.operations.append(operation)

        # Update statistics
        self.statistics["total_operations"] += 1
        if status == "completed":
            self.statistics["successful_operations"] += 1
            if operation_type == "login":
                self.statistics["login_attempts"] += 1
            elif operation_type == "contact":
                self.statistics["contacts_added"] += 1
            elif operation_type == "group":
                self.statistics["groups_created"] += 1
        elif status == "failed":
            self.statistics["failed_operations"] += 1
            self.errors.append(operation)

        logger.info(f"Operation logged: {operation_type}.{operation_name} - {status}")

        # Auto-save periodically
        if len(self.operations) % 10 == 0:
            self.save_run_data()

        return operation_id

    def log_error(self, operation_type: str, operation_name: str, error: str) -> None:
        """
        Log an error.

        Args:
            operation_type: Type of operation
            operation_name: Name of the operation
            error: Error message
        """
        self.log_operation(operation_type, operation_name, status="failed", error=error)

    def save_run_data(self) -> None:
        """Save run data to file."""
        run_dir = self.get_run_dir()

        run_data = {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "statistics": self.statistics,
            "operations": self.operations,
            "errors": self.errors,
        }

        run_file = run_dir / "run_data.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2, default=str)

        logger.debug(f"Run data saved to {run_file}")

    def finish(self) -> None:
        """Finish tracing and save final data."""
        self.end_time = datetime.now(UTC).isoformat()
        self.save_run_data()

        logger.info(f"Tracer finished: {self.run_name}")

    def get_summary(self) -> dict[str, Any]:
        """Get summary of operations."""
        return {
            "run_name": self.run_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "statistics": self.statistics,
            "total_operations": len(self.operations),
            "total_errors": len(self.errors),
        }

