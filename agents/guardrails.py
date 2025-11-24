"""
LLM Guardrails and Safety Checks

This module provides security and safety checks for LLM inputs and outputs
to prevent prompt injection, SQL injection, and other security issues.
"""

import re
import json
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# Prompt Injection Patterns
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"disregard\s+(previous|above|all)",
    r"forget\s+(previous|above|all)",
    r"system\s*:\s*you\s+are",
    r"new\s+instructions",
    r"</system>",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"HUMAN:|ASSISTANT:",
    r"###\s*Instruction",
]

# Dangerous SQL Patterns
DANGEROUS_SQL_PATTERNS = [
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)",
    r"\bDELETE\s+FROM\s+\w+\s+(WHERE\s+1\s*=\s*1)?$",  # DELETE without WHERE or WHERE 1=1
    r"\bTRUNCATE\s+TABLE",
    r"\bALTER\s+TABLE\s+\w+\s+DROP",
    r"\bEXEC(\s+|\().*xp_cmdshell",
    r"\bEXECUTE\s+IMMEDIATE",
    r";.*DROP",
    r";\s*--",  # SQL injection attempts
    r"\bUNION\s+SELECT.*FROM\s+INFORMATION_SCHEMA",
]


def check_for_prompt_injection(text: str) -> bool:
    """
    Check if text contains potential prompt injection attempts.

    Args:
        text: Input text to check

    Returns:
        True if injection detected, False otherwise
    """
    if not text:
        return False

    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected: {pattern}")
            return True

    return False


def validate_llm_input(text: str, max_length: int = 50000) -> str:
    """
    Validate and sanitize LLM input.

    Args:
        text: Input text to validate
        max_length: Maximum allowed length

    Returns:
        Validated text

    Raises:
        ValueError: If input is invalid or potentially malicious
    """
    if not text:
        raise ValueError("Input text cannot be empty")

    if len(text) > max_length:
        raise ValueError(f"Input text exceeds maximum length of {max_length}")

    if check_for_prompt_injection(text):
        raise ValueError("Potential prompt injection detected in input")

    return text


def validate_llm_output(text: str, expected_format: Optional[str] = None) -> str:
    """
    Validate LLM output.

    Args:
        text: Output text to validate
        expected_format: Expected format ('json', 'sql', 'markdown', etc.)

    Returns:
        Validated text

    Raises:
        ValueError: If output is invalid
    """
    if not text:
        raise ValueError("LLM output is empty")

    if expected_format == "json":
        try:
            json.loads(validate_json_output(text))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON output: {e}")

    elif expected_format == "sql":
        text = sanitize_sql_output(text)

    return text


def validate_json_output(text: str) -> str:
    """
    Extract and validate JSON from LLM output.

    LLMs often wrap JSON in markdown code blocks. This function
    strips those and returns clean JSON.

    Args:
        text: LLM output potentially containing JSON

    Returns:
        Clean JSON string

    Raises:
        ValueError: If no valid JSON found
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # Try to find JSON object or array
    json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    # Validate it's proper JSON
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not extract valid JSON: {e}")


def sanitize_sql_output(sql: str) -> str:
    """
    Sanitize SQL output to prevent dangerous operations.

    Args:
        sql: SQL code to sanitize

    Returns:
        Sanitized SQL

    Raises:
        ValueError: If dangerous SQL patterns detected
    """
    if not sql:
        return sql

    sql_upper = sql.upper()

    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE | re.MULTILINE):
            logger.error(f"Dangerous SQL pattern detected: {pattern}")
            raise ValueError(f"Dangerous SQL operation detected: {pattern}")

    # Additional check: ensure it's a SELECT or dbt-compatible SQL
    # In dbt, we expect SELECT, WITH, or {{ }} jinja
    if not (
        re.search(r'^\s*(SELECT|WITH|{{)', sql, re.IGNORECASE | re.MULTILINE) or
        re.search(r'{{\s*config\(', sql, re.IGNORECASE)
    ):
        logger.warning("SQL does not appear to be a SELECT statement or dbt model")

    return sql


# Rate Limiting

_rate_limit_store: Dict[str, list] = {}


def check_rate_limit(
    key: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Simple rate limiting check.

    Args:
        key: Identifier for rate limiting (e.g., "assessment_agent")
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Returns:
        True if rate limit exceeded, False otherwise
    """
    current_time = time.time()

    # Initialize if not exists
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    # Remove old requests outside window
    _rate_limit_store[key] = [
        t for t in _rate_limit_store[key]
        if current_time - t < window_seconds
    ]

    # Check if limit exceeded
    if len(_rate_limit_store[key]) >= max_requests:
        logger.warning(f"Rate limit exceeded for {key}")
        return True

    # Add current request
    _rate_limit_store[key].append(current_time)
    return False


def with_fallback(primary_func: Callable, fallback_func: Callable) -> Callable:
    """
    Decorator to add fallback logic to a function.

    If primary function fails, fallback function is called.

    Args:
        primary_func: Primary function to try
        fallback_func: Fallback function if primary fails

    Returns:
        Wrapped function with fallback logic
    """
    @wraps(primary_func)
    def wrapper(*args, **kwargs):
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary function failed: {e}, using fallback")
            return fallback_func(*args, **kwargs)
    return wrapper


def validate_migration_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate migration state structure.

    Args:
        state: Migration state dictionary

    Returns:
        Validated state

    Raises:
        ValueError: If state is invalid
    """
    required_fields = ["phase", "models", "completed_count", "failed_count"]

    for field in required_fields:
        if field not in state:
            raise ValueError(f"Missing required field in state: {field}")

    valid_phases = ["assessment", "planning", "execution", "evaluation", "complete"]
    if state["phase"] not in valid_phases:
        raise ValueError(f"Invalid phase: {state['phase']}")

    if not isinstance(state["models"], list):
        raise ValueError("models must be a list")

    return state


def sanitize_file_path(path: str) -> str:
    """
    Sanitize file path to prevent directory traversal attacks.

    Args:
        path: File path to sanitize

    Returns:
        Sanitized path

    Raises:
        ValueError: If path contains dangerous patterns
    """
    # Check for directory traversal
    if ".." in path or path.startswith("/") or ":" in path[1:]:
        raise ValueError(f"Potentially dangerous file path: {path}")

    # Remove any shell metacharacters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
    for char in dangerous_chars:
        if char in path:
            raise ValueError(f"Dangerous character in path: {char}")

    return path


def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log security-related events.

    Args:
        event_type: Type of security event
        details: Event details
    """
    logger.warning(
        f"SECURITY EVENT: {event_type}",
        extra={"security_event": True, "details": details}
    )
