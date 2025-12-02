"""
Guardian Agent - AI Agent Security Wrapper

This module provides a security layer that wraps around AI agents to:
1. Monitor and validate all inputs/outputs
2. Detect and block prompt injection attacks
3. Enforce data isolation between organizations
4. Audit all agent actions for compliance
5. Rate limit agent operations
"""

import re
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading

from .guardrails import (
    check_for_prompt_injection,
    validate_llm_input,
    sanitize_sql_output,
    INJECTION_PATTERNS,
    DANGEROUS_SQL_PATTERNS
)

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Security event types"""
    AGENT_INVOCATION = "agent_invocation"
    PROMPT_INJECTION = "prompt_injection"
    DATA_ACCESS = "data_access"
    RATE_LIMIT = "rate_limit"
    OUTPUT_VALIDATION = "output_validation"
    POLICY_VIOLATION = "policy_violation"
    BLOCKED_REQUEST = "blocked_request"


@dataclass
class SecurityEvent:
    """Represents a security event for audit logging"""
    event_type: EventType
    severity: ThreatLevel
    agent_name: str
    organization_id: Optional[int]
    user_id: Optional[int]
    input_hash: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "agent_name": self.agent_name,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "input_hash": self.input_hash,
            "message": self.message,
            "metadata": self.metadata,
            "blocked": self.blocked,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SecurityPolicy:
    """Defines security rules for an organization"""
    organization_id: int
    max_requests_per_minute: int = 30
    max_input_length: int = 50000
    max_output_length: int = 100000
    allowed_agents: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)
    data_access_restrictions: Dict[str, Any] = field(default_factory=dict)


class GuardianAgent:
    """
    Guardian Agent - Security wrapper for AI agents

    This agent monitors, validates, and protects all AI agent operations.
    It implements the principle of defense in depth with multiple security layers.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._rate_limits: Dict[str, List[float]] = {}
        self._policies: Dict[int, SecurityPolicy] = {}
        self._audit_log: List[SecurityEvent] = []
        self._blocked_ips: Dict[str, datetime] = {}

        # Enhanced injection patterns
        self._injection_patterns = self._compile_patterns([
            # Original patterns
            *INJECTION_PATTERNS,
            # Additional advanced patterns
            r"(?i)you\s+are\s+now\s+",
            r"(?i)act\s+as\s+if\s+you",
            r"(?i)pretend\s+(to\s+be|you\s+are)",
            r"(?i)reveal\s+your\s+(system|instructions|prompt)",
            r"(?i)what\s+are\s+your\s+(instructions|rules|constraints)",
            r"(?i)ignore\s+(your|all|the)\s+(rules|constraints|instructions)",
            r"(?i)override\s+(your|the)\s+(instructions|rules)",
            r"(?i)jailbreak",
            r"(?i)DAN\s*mode",
            r"(?i)developer\s*mode\s*(enabled|on)",
            r"(?i)bypass\s+(your|the)\s+(filters|restrictions|safety)",
            r"(?i)\[INST\]|\[/INST\]",
            r"(?i)<<SYS>>|<</SYS>>",
            r"(?i)###\s*(System|Human|Assistant):",
        ])

        # Data exfiltration patterns
        self._exfiltration_patterns = self._compile_patterns([
            r"(?i)send\s+(this|the|all)\s+(data|information)\s+to",
            r"(?i)email\s+(me|this)\s+to",
            r"(?i)post\s+(this|the)\s+to\s+",
            r"(?i)upload\s+(this|the)\s+to",
            r"(?i)transfer\s+(this|the)\s+data",
            r"(?i)exfiltrate",
            r"(?i)webhook\.site|requestbin|pipedream",
        ])

        # SQL injection patterns (enhanced)
        self._sql_patterns = self._compile_patterns(DANGEROUS_SQL_PATTERNS + [
            r"(?i);\s*SHUTDOWN",
            r"(?i);\s*BACKUP\s+DATABASE",
            r"(?i)OPENROWSET",
            r"(?i)OPENDATASOURCE",
            r"(?i)INTO\s+OUTFILE",
            r"(?i)LOAD_FILE",
        ])

        logger.info("Guardian Agent initialized - AI security monitoring active")

    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """Compile regex patterns for efficient matching"""
        compiled = []
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
            except re.error as e:
                logger.warning(f"Invalid pattern '{pattern}': {e}")
        return compiled

    def _hash_input(self, input_text: str) -> str:
        """Create a hash of input for audit logging (privacy-preserving)"""
        return hashlib.sha256(input_text.encode()).hexdigest()[:16]

    def _check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 30,
        window_seconds: int = 60
    ) -> Tuple[bool, str]:
        """
        Check if rate limit is exceeded

        Returns:
            Tuple of (is_blocked, reason)
        """
        with self._lock:
            current_time = time.time()

            if identifier not in self._rate_limits:
                self._rate_limits[identifier] = []

            # Remove old requests outside window
            self._rate_limits[identifier] = [
                t for t in self._rate_limits[identifier]
                if current_time - t < window_seconds
            ]

            if len(self._rate_limits[identifier]) >= max_requests:
                return True, f"Rate limit exceeded: {max_requests} requests per {window_seconds}s"

            self._rate_limits[identifier].append(current_time)
            return False, ""

    def _detect_prompt_injection(self, text: str) -> Tuple[bool, str, ThreatLevel]:
        """
        Detect prompt injection attempts

        Returns:
            Tuple of (is_detected, pattern_description, threat_level)
        """
        if not text:
            return False, "", ThreatLevel.NONE

        # Check injection patterns
        for pattern in self._injection_patterns:
            if pattern.search(text):
                return True, f"Prompt injection pattern: {pattern.pattern[:50]}...", ThreatLevel.CRITICAL

        # Check exfiltration patterns
        for pattern in self._exfiltration_patterns:
            if pattern.search(text):
                return True, f"Data exfiltration pattern: {pattern.pattern[:50]}...", ThreatLevel.HIGH

        # Use existing guardrails
        if check_for_prompt_injection(text):
            return True, "Legacy injection pattern detected", ThreatLevel.HIGH

        return False, "", ThreatLevel.NONE

    def _detect_sql_threats(self, text: str) -> Tuple[bool, str, ThreatLevel]:
        """
        Detect SQL injection or dangerous SQL patterns

        Returns:
            Tuple of (is_detected, pattern_description, threat_level)
        """
        if not text:
            return False, "", ThreatLevel.NONE

        for pattern in self._sql_patterns:
            if pattern.search(text):
                return True, f"Dangerous SQL pattern: {pattern.pattern[:50]}...", ThreatLevel.CRITICAL

        return False, "", ThreatLevel.NONE

    def _log_event(self, event: SecurityEvent):
        """Log a security event"""
        with self._lock:
            self._audit_log.append(event)

            # Keep only last 10000 events in memory
            if len(self._audit_log) > 10000:
                self._audit_log = self._audit_log[-10000:]

        # Log to standard logger based on severity
        log_message = f"[SECURITY] {event.event_type.value}: {event.message}"

        if event.severity in (ThreatLevel.CRITICAL, ThreatLevel.HIGH):
            logger.warning(log_message, extra={"security_event": event.to_dict()})
        elif event.severity == ThreatLevel.MEDIUM:
            logger.info(log_message, extra={"security_event": event.to_dict()})
        else:
            logger.debug(log_message, extra={"security_event": event.to_dict()})

    def validate_input(
        self,
        input_text: str,
        agent_name: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[SecurityEvent]]:
        """
        Validate input before passing to an AI agent

        Args:
            input_text: The input to validate
            agent_name: Name of the target agent
            organization_id: Organization ID for multi-tenancy
            user_id: User ID for audit
            context: Additional context

        Returns:
            Tuple of (is_valid, error_message, security_event)
        """
        input_hash = self._hash_input(input_text)

        # 1. Check rate limits
        rate_key = f"{organization_id or 'global'}:{user_id or 'anon'}:{agent_name}"
        is_limited, limit_reason = self._check_rate_limit(rate_key)

        if is_limited:
            event = SecurityEvent(
                event_type=EventType.RATE_LIMIT,
                severity=ThreatLevel.MEDIUM,
                agent_name=agent_name,
                organization_id=organization_id,
                user_id=user_id,
                input_hash=input_hash,
                message=limit_reason,
                blocked=True
            )
            self._log_event(event)
            return False, limit_reason, event

        # 2. Check input length
        policy = self._policies.get(organization_id, SecurityPolicy(organization_id=0))
        if len(input_text) > policy.max_input_length:
            event = SecurityEvent(
                event_type=EventType.POLICY_VIOLATION,
                severity=ThreatLevel.LOW,
                agent_name=agent_name,
                organization_id=organization_id,
                user_id=user_id,
                input_hash=input_hash,
                message=f"Input exceeds maximum length ({len(input_text)} > {policy.max_input_length})",
                blocked=True
            )
            self._log_event(event)
            return False, "Input too long", event

        # 3. Check for prompt injection
        is_injection, injection_desc, threat_level = self._detect_prompt_injection(input_text)
        if is_injection:
            event = SecurityEvent(
                event_type=EventType.PROMPT_INJECTION,
                severity=threat_level,
                agent_name=agent_name,
                organization_id=organization_id,
                user_id=user_id,
                input_hash=input_hash,
                message=injection_desc,
                metadata={"context": context} if context else {},
                blocked=True
            )
            self._log_event(event)
            return False, "Potentially malicious input detected", event

        # 4. Check for SQL threats in input
        is_sql_threat, sql_desc, sql_threat_level = self._detect_sql_threats(input_text)
        if is_sql_threat:
            event = SecurityEvent(
                event_type=EventType.BLOCKED_REQUEST,
                severity=sql_threat_level,
                agent_name=agent_name,
                organization_id=organization_id,
                user_id=user_id,
                input_hash=input_hash,
                message=sql_desc,
                blocked=True
            )
            self._log_event(event)
            return False, "Dangerous SQL pattern detected", event

        # 5. Log successful validation
        event = SecurityEvent(
            event_type=EventType.AGENT_INVOCATION,
            severity=ThreatLevel.NONE,
            agent_name=agent_name,
            organization_id=organization_id,
            user_id=user_id,
            input_hash=input_hash,
            message=f"Input validated for {agent_name}",
            blocked=False
        )
        self._log_event(event)

        return True, "", event

    def validate_output(
        self,
        output_text: str,
        agent_name: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        expected_format: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate output from an AI agent

        Args:
            output_text: The output to validate
            agent_name: Name of the source agent
            organization_id: Organization ID
            user_id: User ID
            expected_format: Expected format (json, sql, etc.)

        Returns:
            Tuple of (is_valid, error_message, sanitized_output)
        """
        output_hash = self._hash_input(output_text)

        # 1. Check output length
        policy = self._policies.get(organization_id, SecurityPolicy(organization_id=0))
        if len(output_text) > policy.max_output_length:
            event = SecurityEvent(
                event_type=EventType.OUTPUT_VALIDATION,
                severity=ThreatLevel.LOW,
                agent_name=agent_name,
                organization_id=organization_id,
                user_id=user_id,
                input_hash=output_hash,
                message="Output exceeds maximum length",
                blocked=True
            )
            self._log_event(event)
            return False, "Output too long", None

        # 2. Validate SQL output
        if expected_format == "sql":
            try:
                sanitized = sanitize_sql_output(output_text)
                return True, "", sanitized
            except ValueError as e:
                event = SecurityEvent(
                    event_type=EventType.OUTPUT_VALIDATION,
                    severity=ThreatLevel.HIGH,
                    agent_name=agent_name,
                    organization_id=organization_id,
                    user_id=user_id,
                    input_hash=output_hash,
                    message=f"Dangerous SQL in output: {str(e)}",
                    blocked=True
                )
                self._log_event(event)
                return False, str(e), None

        # 3. Check for data leakage patterns
        leakage_patterns = [
            r"(?i)(password|secret|api[_-]?key|token)\s*[=:]\s*['\"][^'\"]+['\"]",
            r"(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
            r"(?i)aws[_-]?(access[_-]?key|secret)",
        ]

        for pattern in leakage_patterns:
            if re.search(pattern, output_text):
                event = SecurityEvent(
                    event_type=EventType.OUTPUT_VALIDATION,
                    severity=ThreatLevel.CRITICAL,
                    agent_name=agent_name,
                    organization_id=organization_id,
                    user_id=user_id,
                    input_hash=output_hash,
                    message="Potential sensitive data in output",
                    blocked=True
                )
                self._log_event(event)
                return False, "Output contains potentially sensitive data", None

        return True, "", output_text

    def protect_agent(self, agent_name: str):
        """
        Decorator to protect an agent function

        Usage:
            @guardian.protect_agent("my_agent")
            def my_agent_function(input_text, **kwargs):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(
                input_text: str,
                organization_id: Optional[int] = None,
                user_id: Optional[int] = None,
                **kwargs
            ):
                # Validate input
                is_valid, error, event = self.validate_input(
                    input_text,
                    agent_name,
                    organization_id,
                    user_id
                )

                if not is_valid:
                    raise SecurityException(error, event)

                # Execute agent
                try:
                    result = func(input_text, **kwargs)
                except Exception as e:
                    # Log agent error
                    self._log_event(SecurityEvent(
                        event_type=EventType.AGENT_INVOCATION,
                        severity=ThreatLevel.MEDIUM,
                        agent_name=agent_name,
                        organization_id=organization_id,
                        user_id=user_id,
                        input_hash=self._hash_input(input_text),
                        message=f"Agent error: {str(e)}",
                        blocked=False
                    ))
                    raise

                # Validate output if string
                if isinstance(result, str):
                    is_valid, error, sanitized = self.validate_output(
                        result,
                        agent_name,
                        organization_id,
                        user_id
                    )
                    if not is_valid:
                        raise SecurityException(error)
                    return sanitized

                return result

            return wrapper
        return decorator

    def set_policy(self, policy: SecurityPolicy):
        """Set security policy for an organization"""
        with self._lock:
            self._policies[policy.organization_id] = policy

    def get_audit_logs(
        self,
        organization_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        severity: Optional[ThreatLevel] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering"""
        with self._lock:
            logs = self._audit_log.copy()

        # Apply filters
        if organization_id is not None:
            logs = [l for l in logs if l.organization_id == organization_id]

        if event_type is not None:
            logs = [l for l in logs if l.event_type == event_type]

        if severity is not None:
            logs = [l for l in logs if l.severity == severity]

        if since is not None:
            logs = [l for l in logs if l.timestamp >= since]

        # Return most recent first, limited
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

        return [log.to_dict() for log in logs]

    def get_security_stats(
        self,
        organization_id: Optional[int] = None,
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get security statistics"""
        since = datetime.now() - timedelta(hours=period_hours)
        logs = self.get_audit_logs(organization_id=organization_id, since=since, limit=10000)

        blocked_count = sum(1 for l in logs if l.get("blocked", False))
        critical_count = sum(1 for l in logs if l.get("severity") == "critical")
        high_count = sum(1 for l in logs if l.get("severity") == "high")

        events_by_type = {}
        for log in logs:
            event_type = log.get("event_type", "unknown")
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

        return {
            "period_hours": period_hours,
            "total_events": len(logs),
            "blocked_count": blocked_count,
            "critical_count": critical_count,
            "high_severity_count": high_count,
            "events_by_type": events_by_type,
            "block_rate_percent": (blocked_count / max(len(logs), 1)) * 100
        }


class SecurityException(Exception):
    """Exception raised when security validation fails"""

    def __init__(self, message: str, event: Optional[SecurityEvent] = None):
        super().__init__(message)
        self.event = event


# Singleton instance
_guardian: Optional[GuardianAgent] = None
_guardian_lock = threading.Lock()


def get_guardian() -> GuardianAgent:
    """Get the singleton Guardian Agent instance"""
    global _guardian
    if _guardian is None:
        with _guardian_lock:
            if _guardian is None:
                _guardian = GuardianAgent()
    return _guardian


# Convenience decorators
def protected_agent(agent_name: str):
    """
    Decorator to protect an agent function

    Usage:
        @protected_agent("assessment_agent")
        def run_assessment(input_text, **kwargs):
            ...
    """
    return get_guardian().protect_agent(agent_name)


def validate_agent_input(
    input_text: str,
    agent_name: str,
    organization_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Validate input for an agent

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error, _ = get_guardian().validate_input(
        input_text, agent_name, organization_id, user_id
    )
    return is_valid, error
