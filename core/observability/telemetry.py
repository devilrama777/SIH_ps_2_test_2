"""
Diagnostic Telemetry Logger and Operational Stage Monitor.
Adheres to CIL Master Implementation Plan Section 35:
- processing stage
- duration
- failures
- model used
- parser used
- document IDs
- job IDs
- Avoid logging confidential content unnecessarily.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StageTelemetry:
    stage_name: str
    start_time: str
    end_time: str
    duration_sec: float
    status: str  # "SUCCESS", "FAILED", "WARNING", "FALLBACK"
    job_id: Optional[str] = None
    document_ids: List[str] = field(default_factory=list)
    model_used: Optional[str] = None
    parser_used: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ObservabilityManager:
    """
    Thread-safe operational telemetry recorder.
    Maintains in-memory ring buffer and persistent JSON Lines diagnostic log.
    """

    def __init__(self, log_dir: str = "data/workspace/audit_logs", max_in_memory: int = 200):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "diagnostic_telemetry.jsonl"
        self.max_in_memory = max_in_memory
        self._buffer: List[StageTelemetry] = []
        self._lock = threading.Lock()

    def record_stage(
        self,
        stage_name: str,
        duration_sec: float,
        status: str = "SUCCESS",
        job_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        model_used: Optional[str] = None,
        parser_used: Optional[str] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> StageTelemetry:
        """Record an execution stage with non-confidential metrics."""
        now = datetime.now(timezone.utc).isoformat()
        entry = StageTelemetry(
            stage_name=stage_name,
            start_time=now,
            end_time=now,
            duration_sec=round(duration_sec, 4),
            status=status,
            job_id=job_id,
            document_ids=document_ids or [],
            model_used=model_used,
            parser_used=parser_used,
            error_message=error_message,
            metrics=metrics or {},
        )

        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) > self.max_in_memory:
                self._buffer.pop(0)

            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            except OSError as e:
                logger.warning(f"Could not persist telemetry log: {e}")

        return entry

    def get_recent_telemetry(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent in-memory telemetry records."""
        with self._lock:
            return [e.to_dict() for e in self._buffer[-limit:]]

    def get_stage_aggregates(self) -> Dict[str, Dict[str, Any]]:
        """Calculate average durations and failure counts per stage."""
        with self._lock:
            events = list(self._buffer)

        aggregates: Dict[str, Dict[str, Any]] = {}
        for ev in events:
            st = aggregates.setdefault(ev.stage_name, {
                "count": 0,
                "total_duration": 0.0,
                "failures": 0,
                "avg_duration": 0.0,
            })
            st["count"] += 1
            st["total_duration"] += ev.duration_sec
            if ev.status == "FAILED":
                st["failures"] += 1
            st["avg_duration"] = round(st["total_duration"] / st["count"], 4)

        return aggregates
