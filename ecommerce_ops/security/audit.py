"""
Audit Logging
Comprehensive audit logging for security events.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ecommerce_ops.security.models import SecurityEvent

logger = logging.getLogger("ecommerce_ops.security.audit")


class AuditEntry(BaseModel):
    """Single audit log entry."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    api_key_id: Optional[str] = None
    role: Optional[str] = None
    success: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high, critical

    class Config:
        extra = "allow"


class AuditLogger:
    """Comprehensive audit logging service."""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self._entries: List[AuditEntry] = []
        self._sensitive_fields = {
            "password",
            "api_key",
            "secret",
            "token",
            "credit_card",
            "ssn",
        }

    def log_event(self, event: SecurityEvent) -> AuditEntry:
        """Log a security event."""
        entry = AuditEntry(
            id=str(len(self._entries) + 1),
            event_type=event.event_type,
            action=event.action,
            resource=event.resource,
            resource_id=event.resource_id,
            user_id=event.user_id,
            api_key_id=event.api_key_id,
            success=event.success,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            details=self._sanitize_details(event.details),
            risk_level=self._assess_risk_level(event),
        )

        self._entries.append(entry)

        # Log to logger
        log_level = logging.WARNING if not entry.success else logging.INFO
        logger.log(
            log_level,
            "Audit: %s %s on %s by %s (%s)",
            entry.action,
            entry.resource,
            entry.resource_id or "N/A",
            entry.user_id or "system",
            "success" if entry.success else "failure",
        )

        # Write to file if configured
        if self.log_file:
            self._write_to_file(entry)

        return entry

    def log_auth_event(
        self,
        action: str,
        user_id: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Log authentication event."""
        event = SecurityEvent(
            event_type="authentication",
            action=action,
            resource="auth",
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            details=details or {},
        )
        return self.log_event(event)

    def log_permission_event(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource: str = "unknown",
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Log permission check event."""
        event = SecurityEvent(
            event_type="authorization",
            action=action,
            resource=resource,
            user_id=user_id,
            success=success,
            details=details or {},
        )
        return self.log_event(event)

    def log_data_access(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Log data access event."""
        event = SecurityEvent(
            event_type="data_access",
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            success=True,
            details=details or {},
        )
        return self.log_event(event)

    def log_config_change(
        self,
        action: str,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Log configuration change."""
        event = SecurityEvent(
            event_type="config_change",
            action=action,
            resource="config",
            user_id=user_id,
            success=True,
            details={"changes": changes or {}},
        )
        return self.log_event(event)

    def log_security_violation(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Log security violation."""
        event = SecurityEvent(
            event_type="security_violation",
            action=action,
            resource=resource,
            user_id=user_id,
            success=False,
            ip_address=ip_address,
            details=details or {},
        )
        return self.log_event(event)

    def get_entries(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        success: Optional[bool] = None,
        risk_level: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get audit entries with filters."""
        entries = self._entries.copy()

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if resource:
            entries = [e for e in entries if e.resource == resource]
        if success is not None:
            entries = [e for e in entries if e.success == success]
        if risk_level:
            entries = [e for e in entries if e.risk_level == risk_level]

        # Sort by timestamp (newest first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        return entries[:limit]

    def get_security_summary(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get security summary for the last N hours."""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        recent = [
            e for e in self._entries
            if e.timestamp.timestamp() > cutoff
        ]

        total = len(recent)
        failures = sum(1 for e in recent if not e.success)
        violations = sum(1 for e in recent if e.event_type == "security_violation")

        by_type = {}
        for entry in recent:
            by_type[entry.event_type] = by_type.get(entry.event_type, 0) + 1

        by_risk = {}
        for entry in recent:
            by_risk[entry.risk_level] = by_risk.get(entry.risk_level, 0) + 1

        return {
            "period_hours": hours,
            "total_events": total,
            "successful": total - failures,
            "failures": failures,
            "security_violations": violations,
            "failure_rate": round(failures / total, 3) if total > 0 else 0,
            "events_by_type": by_type,
            "events_by_risk": by_risk,
        }

    def _assess_risk_level(self, event: SecurityEvent) -> str:
        """Assess risk level of an event."""
        if event.event_type == "security_violation":
            return "critical"
        if not event.success:
            return "high"
        if event.event_type == "config_change":
            return "medium"
        if event.event_type == "authorization":
            return "medium"
        return "low"

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive fields from details."""
        sanitized = {}
        for key, value in details.items():
            if any(s in key.lower() for s in self._sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        return sanitized

    def _write_to_file(self, entry: AuditEntry):
        """Write audit entry to file."""
        try:
            with open(self.log_file, "a") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error("Failed to write audit entry to file: %s", e)


# Singleton
audit_logger = AuditLogger()
