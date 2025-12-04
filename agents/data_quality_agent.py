"""
Data Quality Agent - Intelligent Data Quality Management

This agent provides comprehensive data quality monitoring, validation, profiling,
and automated remediation capabilities for enterprise data migrations.
Part of the DataMigrate AI Eight-Agent Architecture.

Author: DataMigrate AI Team
Version: 1.0.0
"""

import os
import json
import logging
import re
import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import statistics

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Data quality dimensions"""
    COMPLETENESS = "completeness"      # No missing values
    ACCURACY = "accuracy"              # Correct values
    CONSISTENCY = "consistency"        # Uniform format/values
    TIMELINESS = "timeliness"          # Up-to-date data
    VALIDITY = "validity"              # Conforms to rules
    UNIQUENESS = "uniqueness"          # No duplicates
    INTEGRITY = "integrity"            # Referential integrity


class RuleSeverity(str, Enum):
    """Severity levels for quality rules"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleType(str, Enum):
    """Types of data quality rules"""
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    RANGE = "range"
    REGEX = "regex"
    ENUM = "enum"
    LENGTH = "length"
    FOREIGN_KEY = "foreign_key"
    CUSTOM = "custom"
    FRESHNESS = "freshness"
    SCHEMA = "schema"


class RemediationAction(str, Enum):
    """Automated remediation actions"""
    FLAG = "flag"              # Flag for review
    IMPUTE = "impute"          # Fill with default/calculated value
    QUARANTINE = "quarantine"  # Move to quarantine table
    REJECT = "reject"          # Reject the record
    TRANSFORM = "transform"    # Apply transformation
    ALERT = "alert"            # Send alert only


@dataclass
class QualityRule:
    """Represents a data quality rule"""
    rule_id: str
    name: str
    rule_type: RuleType
    dimension: QualityDimension
    severity: RuleSeverity
    column: Optional[str] = None
    table: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    enabled: bool = True
    remediation: RemediationAction = RemediationAction.FLAG


@dataclass
class QualityIssue:
    """Represents a detected quality issue"""
    issue_id: str
    rule: QualityRule
    affected_records: int
    sample_values: List[Any] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    details: str = ""
    remediation_applied: bool = False


@dataclass
class QualityScore:
    """Quality score for a dimension or overall"""
    dimension: Optional[QualityDimension]
    score: float  # 0-100
    total_records: int
    passed_records: int
    failed_records: int
    issues: List[QualityIssue] = field(default_factory=list)


@dataclass
class ColumnProfile:
    """Profile of a single column"""
    name: str
    data_type: str
    total_count: int
    null_count: int
    distinct_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    std_dev: Optional[float] = None
    pattern_detected: Optional[str] = None
    sample_values: List[Any] = field(default_factory=list)
    inferred_constraints: List[str] = field(default_factory=list)


@dataclass
class TableProfile:
    """Profile of a complete table"""
    table_name: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile] = field(default_factory=list)
    primary_key_candidates: List[str] = field(default_factory=list)
    foreign_key_candidates: List[Dict[str, str]] = field(default_factory=list)
    quality_score: float = 0.0
    profiled_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityReport:
    """Comprehensive quality report"""
    report_id: str
    generated_at: datetime
    overall_score: float
    dimension_scores: Dict[str, float]
    tables_analyzed: int
    total_records: int
    issues_found: int
    critical_issues: int
    recommendations: List[str] = field(default_factory=list)
    detailed_issues: List[QualityIssue] = field(default_factory=list)


class DataQualityAgent:
    """
    Data Quality Agent for comprehensive data quality management.

    Capabilities:
    - Real-time Quality Monitoring
    - Automated Data Profiling
    - Rule-based Validation
    - Anomaly Detection
    - Quality Scoring
    - Automated Remediation
    - Quality Reporting
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the Data Quality Agent"""
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            max_tokens=4096
        )

        # Initialize rule library
        self.rules: Dict[str, QualityRule] = {}
        self._initialize_default_rules()

        # Initialize the LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("Data Quality Agent initialized successfully")

    def _initialize_default_rules(self):
        """Initialize default quality rules"""
        default_rules = [
            QualityRule(
                rule_id="email_format",
                name="Email Format Validation",
                rule_type=RuleType.REGEX,
                dimension=QualityDimension.VALIDITY,
                severity=RuleSeverity.ERROR,
                parameters={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                description="Validates email addresses match standard format"
            ),
            QualityRule(
                rule_id="phone_format",
                name="Phone Number Format",
                rule_type=RuleType.REGEX,
                dimension=QualityDimension.VALIDITY,
                severity=RuleSeverity.WARNING,
                parameters={"pattern": r"^\+?[\d\s-]{10,}$"},
                description="Validates phone numbers"
            ),
            QualityRule(
                rule_id="date_not_future",
                name="Date Not in Future",
                rule_type=RuleType.CUSTOM,
                dimension=QualityDimension.ACCURACY,
                severity=RuleSeverity.ERROR,
                description="Transaction dates should not be in the future"
            ),
            QualityRule(
                rule_id="positive_amount",
                name="Positive Amount",
                rule_type=RuleType.RANGE,
                dimension=QualityDimension.VALIDITY,
                severity=RuleSeverity.ERROR,
                parameters={"min": 0},
                description="Monetary amounts should be positive"
            )
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for data quality"""
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("profile_data", self._profile_data_node)
        workflow.add_node("validate_rules", self._validate_rules_node)
        workflow.add_node("detect_anomalies", self._detect_anomalies_node)
        workflow.add_node("calculate_scores", self._calculate_scores_node)
        workflow.add_node("apply_remediation", self._apply_remediation_node)
        workflow.add_node("generate_report", self._generate_report_node)

        # Set entry point
        workflow.set_entry_point("profile_data")

        # Add edges
        workflow.add_edge("profile_data", "validate_rules")
        workflow.add_edge("validate_rules", "detect_anomalies")
        workflow.add_edge("detect_anomalies", "calculate_scores")

        # Conditional edge for remediation
        workflow.add_conditional_edges(
            "calculate_scores",
            self._should_remediate,
            {
                "remediate": "apply_remediation",
                "skip": "generate_report"
            }
        )

        workflow.add_edge("apply_remediation", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    def _should_remediate(self, state: dict) -> str:
        """Determine if remediation should be applied"""
        if state.get("auto_remediate", False) and state.get("issues", []):
            return "remediate"
        return "skip"

    async def _profile_data_node(self, state: dict) -> dict:
        """Profile the input data"""
        data = state.get("data", [])
        table_name = state.get("table_name", "unknown")

        if not data:
            state["profile"] = None
            return state

        columns = []
        sample_row = data[0]

        for col_name, sample_value in sample_row.items():
            values = [row.get(col_name) for row in data]
            non_null_values = [v for v in values if v is not None]

            # Detect data type
            data_type = self._infer_type(non_null_values)

            # Calculate statistics
            profile = ColumnProfile(
                name=col_name,
                data_type=data_type,
                total_count=len(values),
                null_count=len(values) - len(non_null_values),
                distinct_count=len(set(str(v) for v in non_null_values)),
                sample_values=non_null_values[:5]
            )

            # Numeric statistics
            if data_type in ["integer", "float"] and non_null_values:
                numeric_values = [float(v) for v in non_null_values if self._is_numeric(v)]
                if numeric_values:
                    profile.min_value = min(numeric_values)
                    profile.max_value = max(numeric_values)
                    profile.mean_value = statistics.mean(numeric_values)
                    profile.std_dev = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0

            # Pattern detection for strings
            if data_type == "string" and non_null_values:
                profile.pattern_detected = self._detect_pattern(non_null_values)

            # Infer constraints
            profile.inferred_constraints = self._infer_constraints(profile)

            columns.append(profile)

        # Detect primary key candidates
        pk_candidates = [
            col.name for col in columns
            if col.distinct_count == col.total_count and col.null_count == 0
        ]

        table_profile = TableProfile(
            table_name=table_name,
            row_count=len(data),
            column_count=len(columns),
            columns=columns,
            primary_key_candidates=pk_candidates
        )

        state["profile"] = self._table_profile_to_dict(table_profile)
        return state

    async def _validate_rules_node(self, state: dict) -> dict:
        """Validate data against quality rules"""
        data = state.get("data", [])
        custom_rules = state.get("rules", [])
        issues = []

        # Combine default and custom rules
        all_rules = list(self.rules.values())
        for rule_dict in custom_rules:
            rule = QualityRule(**rule_dict)
            all_rules.append(rule)

        for rule in all_rules:
            if not rule.enabled:
                continue

            # Apply rule based on type
            rule_issues = self._apply_rule(rule, data)
            issues.extend(rule_issues)

        state["issues"] = [self._issue_to_dict(i) for i in issues]
        return state

    def _apply_rule(self, rule: QualityRule, data: List[Dict]) -> List[QualityIssue]:
        """Apply a specific rule to data"""
        issues = []
        failed_records = []
        sample_values = []

        for i, row in enumerate(data):
            if rule.column and rule.column not in row:
                continue

            value = row.get(rule.column) if rule.column else row
            passed = True

            if rule.rule_type == RuleType.NOT_NULL:
                passed = value is not None and value != ""

            elif rule.rule_type == RuleType.UNIQUE:
                # Handled separately for efficiency
                pass

            elif rule.rule_type == RuleType.RANGE:
                if value is not None:
                    min_val = rule.parameters.get("min")
                    max_val = rule.parameters.get("max")
                    try:
                        num_value = float(value)
                        if min_val is not None and num_value < min_val:
                            passed = False
                        if max_val is not None and num_value > max_val:
                            passed = False
                    except (ValueError, TypeError):
                        passed = False

            elif rule.rule_type == RuleType.REGEX:
                if value is not None:
                    pattern = rule.parameters.get("pattern", "")
                    passed = bool(re.match(pattern, str(value)))

            elif rule.rule_type == RuleType.ENUM:
                allowed_values = rule.parameters.get("values", [])
                passed = value in allowed_values

            elif rule.rule_type == RuleType.LENGTH:
                if value is not None:
                    min_len = rule.parameters.get("min", 0)
                    max_len = rule.parameters.get("max", float("inf"))
                    passed = min_len <= len(str(value)) <= max_len

            if not passed:
                failed_records.append(i)
                if len(sample_values) < 5:
                    sample_values.append(value)

        # Handle uniqueness check
        if rule.rule_type == RuleType.UNIQUE and rule.column:
            values = [row.get(rule.column) for row in data]
            seen = set()
            duplicates = []
            for i, v in enumerate(values):
                if v in seen:
                    duplicates.append(i)
                    if len(sample_values) < 5:
                        sample_values.append(v)
                seen.add(v)
            failed_records = duplicates

        if failed_records:
            issue = QualityIssue(
                issue_id=f"{rule.rule_id}_{hashlib.md5(str(failed_records).encode()).hexdigest()[:8]}",
                rule=rule,
                affected_records=len(failed_records),
                sample_values=sample_values,
                details=f"Rule '{rule.name}' failed for {len(failed_records)} records"
            )
            issues.append(issue)

        return issues

    async def _detect_anomalies_node(self, state: dict) -> dict:
        """Detect statistical anomalies in data"""
        data = state.get("data", [])
        profile = state.get("profile", {})
        anomalies = state.get("issues", [])

        if not profile:
            return state

        columns = profile.get("columns", [])

        for col in columns:
            if col.get("data_type") in ["integer", "float"]:
                col_name = col.get("name")
                mean = col.get("mean_value")
                std_dev = col.get("std_dev")

                if mean is not None and std_dev is not None and std_dev > 0:
                    values = [row.get(col_name) for row in data if row.get(col_name) is not None]
                    outliers = []

                    for i, v in enumerate(values):
                        try:
                            z_score = abs((float(v) - mean) / std_dev)
                            if z_score > 3:
                                outliers.append((i, v))
                        except (ValueError, TypeError):
                            pass

                    if outliers:
                        rule = QualityRule(
                            rule_id=f"outlier_{col_name}",
                            name=f"Statistical Outlier in {col_name}",
                            rule_type=RuleType.CUSTOM,
                            dimension=QualityDimension.ACCURACY,
                            severity=RuleSeverity.WARNING
                        )

                        anomalies.append(self._issue_to_dict(QualityIssue(
                            issue_id=f"anomaly_{col_name}",
                            rule=rule,
                            affected_records=len(outliers),
                            sample_values=[v for _, v in outliers[:5]],
                            details=f"Found {len(outliers)} statistical outliers (Z-score > 3)"
                        )))

        state["issues"] = anomalies
        return state

    async def _calculate_scores_node(self, state: dict) -> dict:
        """Calculate quality scores by dimension"""
        data = state.get("data", [])
        issues = state.get("issues", [])
        profile = state.get("profile", {})

        total_records = len(data)
        if total_records == 0:
            state["scores"] = {}
            return state

        # Initialize dimension scores
        dimension_scores = {dim.value: {"passed": total_records, "failed": 0, "issues": []} for dim in QualityDimension}

        # Attribute issues to dimensions
        for issue in issues:
            rule = issue.get("rule", {})
            dimension = rule.get("dimension", QualityDimension.VALIDITY.value)
            affected = issue.get("affected_records", 0)

            if dimension in dimension_scores:
                dimension_scores[dimension]["failed"] += affected
                dimension_scores[dimension]["passed"] -= affected
                dimension_scores[dimension]["issues"].append(issue)

        # Calculate completeness from profile
        if profile:
            total_nulls = sum(col.get("null_count", 0) for col in profile.get("columns", []))
            total_cells = profile.get("row_count", 0) * profile.get("column_count", 1)
            if total_cells > 0:
                completeness_score = (1 - total_nulls / total_cells) * 100
                dimension_scores[QualityDimension.COMPLETENESS.value] = {
                    "score": completeness_score,
                    "passed": total_cells - total_nulls,
                    "failed": total_nulls,
                    "issues": []
                }

        # Calculate scores
        scores = {}
        for dim, data_dim in dimension_scores.items():
            total = data_dim.get("passed", 0) + data_dim.get("failed", 0)
            if "score" in data_dim:
                scores[dim] = data_dim["score"]
            elif total > 0:
                scores[dim] = (data_dim["passed"] / total) * 100
            else:
                scores[dim] = 100.0

        # Overall score (weighted average)
        weights = {
            QualityDimension.COMPLETENESS.value: 1.0,
            QualityDimension.ACCURACY.value: 1.5,
            QualityDimension.VALIDITY.value: 1.5,
            QualityDimension.UNIQUENESS.value: 1.0,
            QualityDimension.CONSISTENCY.value: 1.0,
            QualityDimension.TIMELINESS.value: 0.5,
            QualityDimension.INTEGRITY.value: 1.5
        }

        total_weight = sum(weights.get(dim, 1.0) for dim in scores.keys())
        overall_score = sum(scores[dim] * weights.get(dim, 1.0) for dim in scores.keys()) / total_weight

        state["scores"] = {
            "overall": overall_score,
            "by_dimension": scores,
            "total_records": total_records,
            "total_issues": len(issues)
        }

        return state

    async def _apply_remediation_node(self, state: dict) -> dict:
        """Apply automated remediation to issues"""
        data = state.get("data", [])
        issues = state.get("issues", [])
        remediated_data = data.copy()
        remediation_log = []

        for issue in issues:
            rule = issue.get("rule", {})
            action = rule.get("remediation", RemediationAction.FLAG.value)

            if action == RemediationAction.IMPUTE.value:
                # Apply imputation based on rule type
                col = rule.get("column")
                if col:
                    default_value = rule.get("parameters", {}).get("default_value")
                    if default_value is not None:
                        for row in remediated_data:
                            if row.get(col) is None:
                                row[col] = default_value
                        remediation_log.append(f"Imputed {col} with {default_value}")

            elif action == RemediationAction.FLAG.value:
                # Add quality flag column
                affected_indices = issue.get("affected_indices", [])
                for i, row in enumerate(remediated_data):
                    if i in affected_indices:
                        row["_quality_flag"] = True
                remediation_log.append(f"Flagged {len(affected_indices)} records")

        state["remediated_data"] = remediated_data
        state["remediation_log"] = remediation_log
        return state

    async def _generate_report_node(self, state: dict) -> dict:
        """Generate comprehensive quality report"""
        scores = state.get("scores", {})
        issues = state.get("issues", [])
        profile = state.get("profile", {})

        # Count critical issues
        critical_count = sum(
            1 for i in issues
            if i.get("rule", {}).get("severity") == RuleSeverity.CRITICAL.value
        )

        # Generate AI-powered recommendations
        recommendations = await self._generate_recommendations(state)

        report = QualityReport(
            report_id=f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            overall_score=scores.get("overall", 0),
            dimension_scores=scores.get("by_dimension", {}),
            tables_analyzed=1,
            total_records=scores.get("total_records", 0),
            issues_found=len(issues),
            critical_issues=critical_count,
            recommendations=recommendations,
            detailed_issues=issues
        )

        state["report"] = self._report_to_dict(report)
        return state

    async def _generate_recommendations(self, state: dict) -> List[str]:
        """Generate AI-powered recommendations"""
        issues = state.get("issues", [])
        scores = state.get("scores", {})

        if not issues and scores.get("overall", 100) > 95:
            return ["Data quality is excellent. Continue monitoring to maintain standards."]

        system_prompt = """You are a data quality expert. Based on the quality issues and scores,
        provide 3-5 actionable recommendations to improve data quality.
        Return a JSON array of recommendation strings."""

        context = {
            "overall_score": scores.get("overall", 0),
            "dimension_scores": scores.get("by_dimension", {}),
            "issue_count": len(issues),
            "issue_types": list(set(i.get("rule", {}).get("rule_type", "unknown") for i in issues))
        }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Quality Analysis:\n{json.dumps(context, indent=2)}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            recommendations = json.loads(response.content)
            return recommendations if isinstance(recommendations, list) else [recommendations]
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review detected issues and implement data validation rules."]

    # Helper methods

    def _infer_type(self, values: List[Any]) -> str:
        """Infer data type from values"""
        if not values:
            return "unknown"

        sample = values[0]
        if isinstance(sample, bool):
            return "boolean"
        if isinstance(sample, int):
            return "integer"
        if isinstance(sample, float):
            return "float"
        if isinstance(sample, str):
            # Check if it's a date
            if self._looks_like_date(sample):
                return "date"
            # Check if it's numeric string
            if self._is_numeric(sample):
                return "numeric_string"
            return "string"
        return "unknown"

    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _looks_like_date(self, value: str) -> bool:
        """Check if string looks like a date"""
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",
            r"\d{2}/\d{2}/\d{4}",
            r"\d{2}-\d{2}-\d{4}"
        ]
        return any(re.match(p, value) for p in date_patterns)

    def _detect_pattern(self, values: List[Any]) -> Optional[str]:
        """Detect common pattern in string values"""
        if not values:
            return None

        patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^\+?[\d\s-]{10,}$",
            "url": r"^https?://",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "date_iso": r"^\d{4}-\d{2}-\d{2}$",
            "postal_code": r"^\d{5}(-\d{4})?$"
        }

        for name, pattern in patterns.items():
            matches = sum(1 for v in values if re.match(pattern, str(v), re.I))
            if matches > len(values) * 0.8:
                return name

        return None

    def _infer_constraints(self, profile: ColumnProfile) -> List[str]:
        """Infer constraints from column profile"""
        constraints = []

        if profile.null_count == 0:
            constraints.append("NOT NULL")

        if profile.distinct_count == profile.total_count:
            constraints.append("UNIQUE")

        if profile.data_type in ["integer", "float"] and profile.min_value is not None:
            if profile.min_value >= 0:
                constraints.append("POSITIVE")

        if profile.pattern_detected:
            constraints.append(f"PATTERN:{profile.pattern_detected}")

        return constraints

    def _table_profile_to_dict(self, profile: TableProfile) -> dict:
        """Convert TableProfile to dictionary"""
        return {
            "table_name": profile.table_name,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "columns": [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "total_count": col.total_count,
                    "null_count": col.null_count,
                    "distinct_count": col.distinct_count,
                    "min_value": col.min_value,
                    "max_value": col.max_value,
                    "mean_value": col.mean_value,
                    "std_dev": col.std_dev,
                    "pattern_detected": col.pattern_detected,
                    "sample_values": col.sample_values,
                    "inferred_constraints": col.inferred_constraints
                }
                for col in profile.columns
            ],
            "primary_key_candidates": profile.primary_key_candidates,
            "foreign_key_candidates": profile.foreign_key_candidates,
            "quality_score": profile.quality_score,
            "profiled_at": profile.profiled_at.isoformat()
        }

    def _issue_to_dict(self, issue: QualityIssue) -> dict:
        """Convert QualityIssue to dictionary"""
        return {
            "issue_id": issue.issue_id,
            "rule": {
                "rule_id": issue.rule.rule_id,
                "name": issue.rule.name,
                "rule_type": issue.rule.rule_type.value if isinstance(issue.rule.rule_type, Enum) else issue.rule.rule_type,
                "dimension": issue.rule.dimension.value if isinstance(issue.rule.dimension, Enum) else issue.rule.dimension,
                "severity": issue.rule.severity.value if isinstance(issue.rule.severity, Enum) else issue.rule.severity,
                "column": issue.rule.column,
                "remediation": issue.rule.remediation.value if isinstance(issue.rule.remediation, Enum) else issue.rule.remediation
            },
            "affected_records": issue.affected_records,
            "sample_values": issue.sample_values,
            "timestamp": issue.timestamp.isoformat(),
            "details": issue.details,
            "remediation_applied": issue.remediation_applied
        }

    def _report_to_dict(self, report: QualityReport) -> dict:
        """Convert QualityReport to dictionary"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "overall_score": report.overall_score,
            "dimension_scores": report.dimension_scores,
            "tables_analyzed": report.tables_analyzed,
            "total_records": report.total_records,
            "issues_found": report.issues_found,
            "critical_issues": report.critical_issues,
            "recommendations": report.recommendations,
            "detailed_issues": report.detailed_issues
        }

    # Public API Methods

    async def assess_quality(
        self,
        data: List[Dict[str, Any]],
        table_name: str = "data",
        rules: Optional[List[Dict]] = None,
        auto_remediate: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive quality assessment.

        Args:
            data: List of data records
            table_name: Name of the table/dataset
            rules: Custom quality rules to apply
            auto_remediate: Whether to apply automatic remediation

        Returns:
            Quality assessment results with scores and issues
        """
        logger.info(f"Assessing quality for {len(data)} records from {table_name}")

        state = {
            "data": data,
            "table_name": table_name,
            "rules": rules or [],
            "auto_remediate": auto_remediate
        }

        result = await self.workflow.ainvoke(state)

        return {
            "profile": result.get("profile"),
            "scores": result.get("scores"),
            "issues": result.get("issues", []),
            "report": result.get("report"),
            "remediated_data": result.get("remediated_data") if auto_remediate else None
        }

    async def profile_data(
        self,
        data: List[Dict[str, Any]],
        table_name: str = "data"
    ) -> Dict[str, Any]:
        """
        Profile data without full quality assessment.

        Args:
            data: List of data records
            table_name: Name of the table/dataset

        Returns:
            Data profile with statistics and patterns
        """
        logger.info(f"Profiling {len(data)} records from {table_name}")

        state = {"data": data, "table_name": table_name}
        result = await self._profile_data_node(state)

        return result.get("profile", {})

    def add_rule(self, rule: QualityRule) -> None:
        """Add a quality rule to the library"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the library"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed rule: {rule_id}")
            return True
        return False

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all registered rules"""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "rule_type": r.rule_type.value,
                "dimension": r.dimension.value,
                "severity": r.severity.value,
                "enabled": r.enabled
            }
            for r in self.rules.values()
        ]

    async def validate_against_rules(
        self,
        data: List[Dict[str, Any]],
        rule_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate data against specific rules.

        Args:
            data: List of data records
            rule_ids: Specific rule IDs to validate (None = all)

        Returns:
            Validation results
        """
        selected_rules = []
        for rule_id, rule in self.rules.items():
            if rule_ids is None or rule_id in rule_ids:
                selected_rules.append(rule)

        all_issues = []
        for rule in selected_rules:
            issues = self._apply_rule(rule, data)
            all_issues.extend(issues)

        return {
            "rules_applied": len(selected_rules),
            "records_validated": len(data),
            "issues_found": len(all_issues),
            "issues": [self._issue_to_dict(i) for i in all_issues]
        }

    def generate_quality_report_text(self, report: Dict[str, Any]) -> str:
        """Generate a text-based quality report"""
        lines = [
            "=" * 60,
            "DATA QUALITY ASSESSMENT REPORT",
            f"Report ID: {report.get('report_id', 'N/A')}",
            f"Generated: {report.get('generated_at', 'N/A')}",
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40,
            f"Overall Quality Score: {report.get('overall_score', 0):.1f}/100",
            f"Records Analyzed: {report.get('total_records', 0):,}",
            f"Issues Found: {report.get('issues_found', 0)}",
            f"Critical Issues: {report.get('critical_issues', 0)}",
            "",
            "DIMENSION SCORES",
            "-" * 40
        ]

        for dim, score in report.get("dimension_scores", {}).items():
            bar = "#" * int(score / 5) + "-" * (20 - int(score / 5))
            lines.append(f"{dim.title():20} [{bar}] {score:.1f}%")

        lines.extend(["", "RECOMMENDATIONS", "-" * 40])
        for i, rec in enumerate(report.get("recommendations", []), 1):
            lines.append(f"{i}. {rec}")

        if report.get("detailed_issues"):
            lines.extend(["", "ISSUES DETAIL", "-" * 40])
            for issue in report["detailed_issues"][:10]:  # Limit to top 10
                rule = issue.get("rule", {})
                lines.append(f"\n[{rule.get('severity', 'N/A').upper()}] {rule.get('name', 'Unknown Rule')}")
                lines.append(f"   Affected Records: {issue.get('affected_records', 0)}")
                lines.append(f"   {issue.get('details', '')}")

        lines.extend(["", "=" * 60, "END OF REPORT", "=" * 60])

        return "\n".join(lines)


# Example usage and testing
async def main():
    """Example usage of the Data Quality Agent"""

    # Sample data with quality issues
    sample_data = [
        {"id": 1, "email": "john@example.com", "phone": "+1-555-0100", "amount": 150.00, "status": "active"},
        {"id": 2, "email": "invalid-email", "phone": "555-0101", "amount": 200.00, "status": "active"},
        {"id": 3, "email": "jane@example.com", "phone": None, "amount": -50.00, "status": "pending"},
        {"id": 4, "email": "bob@test.org", "phone": "+1-555-0103", "amount": 300.00, "status": "active"},
        {"id": 5, "email": "alice@example.com", "phone": "+1-555-0104", "amount": 175.50, "status": None},
        {"id": 1, "email": "duplicate@example.com", "phone": "+1-555-0105", "amount": 500.00, "status": "active"},  # Duplicate ID
    ]

    try:
        agent = DataQualityAgent()

        # Test quality assessment
        print("Running quality assessment...")
        result = await agent.assess_quality(sample_data, "customers")

        print(f"\nOverall Score: {result['scores']['overall']:.1f}/100")
        print(f"Issues Found: {len(result['issues'])}")

        # Generate and print report
        if result.get("report"):
            report_text = agent.generate_quality_report_text(result["report"])
            print("\n" + report_text)

        # Test profiling only
        print("\n\nRunning data profiling...")
        profile = await agent.profile_data(sample_data, "customers")
        print(f"Columns profiled: {len(profile.get('columns', []))}")
        print(f"Primary key candidates: {profile.get('primary_key_candidates', [])}")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the ANTHROPIC_API_KEY environment variable")


# =============================================================================
# Source Database Scanner - Direct MSSQL Connection
# =============================================================================

def scan_source_data_quality(
    server: str,
    database: str,
    username: str = "",
    password: str = "",
    port: int = 1433,
    use_windows_auth: bool = False,
    tables: Optional[List[str]] = None,
    sample_size: int = 10000
) -> Dict[str, Any]:
    """
    Scan source MSSQL database for data quality issues.

    This function connects directly to the source database and profiles
    data quality BEFORE migration to help users understand their data.

    Args:
        server: Database server hostname
        database: Database name
        username: SQL Server username (if not Windows auth)
        password: SQL Server password (if not Windows auth)
        port: Database port (default 1433)
        use_windows_auth: Use Windows/Trusted authentication
        tables: Specific tables to scan (None = all)
        sample_size: Sample size for profiling

    Returns:
        Data quality report as dictionary
    """
    import pyodbc
    from datetime import datetime

    logger.info(f"Scanning data quality for {database} on {server}")

    # Build connection string
    if use_windows_auth:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
        )

    report = {
        "database_name": database,
        "server": server,
        "scan_started_at": datetime.now().isoformat(),
        "tables_scanned": 0,
        "total_rows_scanned": 0,
        "total_issues": 0,
        "critical_issues": 0,
        "error_issues": 0,
        "warning_issues": 0,
        "info_issues": 0,
        "overall_score": 100.0,
        "tables": [],
        "issues_by_severity": {
            "critical": [],
            "error": [],
            "warning": [],
            "info": []
        }
    }

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()

        # Get list of tables
        if tables:
            table_list = [(t.split('.')[0] if '.' in t else 'dbo',
                          t.split('.')[-1]) for t in tables]
        else:
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            table_list = [(row.TABLE_SCHEMA, row.TABLE_NAME) for row in cursor.fetchall()]

        # Scan each table
        for schema, table in table_list:
            try:
                table_profile = _scan_table(cursor, schema, table, sample_size)
                report["tables"].append(table_profile)
                report["tables_scanned"] += 1
                report["total_rows_scanned"] += table_profile.get("row_count", 0)

                # Collect issues
                for issue in table_profile.get("issues", []):
                    severity = issue.get("severity", "info")
                    report["issues_by_severity"][severity].append(issue)

                    if severity == "critical":
                        report["critical_issues"] += 1
                    elif severity == "error":
                        report["error_issues"] += 1
                    elif severity == "warning":
                        report["warning_issues"] += 1
                    else:
                        report["info_issues"] += 1

            except Exception as e:
                logger.error(f"Error scanning table {schema}.{table}: {e}")
                report["issues_by_severity"]["error"].append({
                    "table_name": f"{schema}.{table}",
                    "column_name": None,
                    "category": "validity",
                    "severity": "error",
                    "issue_type": "scan_error",
                    "description": f"Failed to scan table: {str(e)}",
                    "recommendation": "Check table permissions and structure"
                })
                report["error_issues"] += 1

        # Check foreign key integrity
        fk_issues = _check_foreign_keys(cursor)
        for issue in fk_issues:
            severity = issue.get("severity", "error")
            report["issues_by_severity"][severity].append(issue)
            if severity == "error":
                report["error_issues"] += 1
            else:
                report["warning_issues"] += 1

        conn.close()

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        report["issues_by_severity"]["critical"].append({
            "table_name": None,
            "column_name": None,
            "category": "validity",
            "severity": "critical",
            "issue_type": "connection_error",
            "description": f"Failed to connect: {str(e)}",
            "recommendation": "Check connection settings and credentials"
        })
        report["critical_issues"] += 1

    # Calculate overall score
    report["total_issues"] = (report["critical_issues"] + report["error_issues"] +
                              report["warning_issues"] + report["info_issues"])
    report["overall_score"] = _calculate_score(report)
    report["scan_completed_at"] = datetime.now().isoformat()

    logger.info(f"Scan complete: {report['tables_scanned']} tables, {report['total_issues']} issues, score: {report['overall_score']}")

    return report


def _scan_table(cursor, schema: str, table: str, sample_size: int) -> Dict[str, Any]:
    """Scan a single table for data quality issues"""
    full_name = f"[{schema}].[{table}]"

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {full_name}")
    row_count = cursor.fetchone()[0]

    # Get column info
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE,
               CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, schema, table)

    columns_info = cursor.fetchall()

    profile = {
        "table_name": table,
        "schema_name": schema,
        "row_count": row_count,
        "column_count": len(columns_info),
        "columns": [],
        "issues": []
    }

    # Empty table check
    if row_count == 0:
        profile["issues"].append({
            "table_name": f"{schema}.{table}",
            "column_name": None,
            "category": "completeness",
            "severity": "warning",
            "issue_type": "empty_table",
            "description": "Table has no data",
            "affected_rows": 0,
            "affected_percentage": 0,
            "recommendation": "Verify this table should be migrated"
        })
        return profile

    # Profile each column
    for col_info in columns_info:
        col_name, data_type, is_nullable, char_len, num_prec = col_info

        col_profile = _profile_column(cursor, full_name, col_name, data_type, row_count)
        profile["columns"].append(col_profile)

        # Check for issues
        issues = _check_column_issues(col_profile, schema, table, is_nullable)
        profile["issues"].extend(issues)

    # Check for duplicates
    dup_issues = _check_table_duplicates(cursor, full_name, schema, table, row_count)
    profile["issues"].extend(dup_issues)

    return profile


def _profile_column(cursor, full_table: str, col_name: str, data_type: str, total_rows: int) -> Dict[str, Any]:
    """Profile a single column"""
    safe_col = f"[{col_name}]"

    # Get null count and distinct count
    cursor.execute(f"""
        SELECT
            SUM(CASE WHEN {safe_col} IS NULL THEN 1 ELSE 0 END) as null_count,
            COUNT(DISTINCT {safe_col}) as distinct_count
        FROM {full_table}
    """)
    result = cursor.fetchone()
    null_count = result[0] or 0
    distinct_count = result[1] or 0

    profile = {
        "column_name": col_name,
        "data_type": data_type,
        "total_rows": total_rows,
        "null_count": null_count,
        "null_percentage": round((null_count / total_rows * 100), 2) if total_rows > 0 else 0,
        "distinct_count": distinct_count,
        "distinct_percentage": round((distinct_count / total_rows * 100), 2) if total_rows > 0 else 0,
        "min_value": None,
        "max_value": None
    }

    # Get min/max for numeric and date types
    if data_type.lower() in ('int', 'bigint', 'smallint', 'tinyint', 'decimal',
                              'numeric', 'float', 'real', 'money', 'smallmoney',
                              'date', 'datetime', 'datetime2', 'smalldatetime'):
        try:
            cursor.execute(f"""
                SELECT MIN({safe_col}), MAX({safe_col})
                FROM {full_table}
                WHERE {safe_col} IS NOT NULL
            """)
            min_max = cursor.fetchone()
            profile["min_value"] = str(min_max[0]) if min_max[0] is not None else None
            profile["max_value"] = str(min_max[1]) if min_max[1] is not None else None
        except Exception:
            pass

    return profile


def _check_column_issues(profile: Dict, schema: str, table: str, is_nullable: str) -> List[Dict]:
    """Check column profile for issues"""
    issues = []
    full_table = f"{schema}.{table}"

    null_pct = profile.get("null_percentage", 0)

    # High null rate
    if null_pct >= 50:
        issues.append({
            "table_name": full_table,
            "column_name": profile["column_name"],
            "category": "completeness",
            "severity": "error",
            "issue_type": "high_null_rate",
            "description": f"{null_pct}% of values are NULL",
            "affected_rows": profile["null_count"],
            "affected_percentage": null_pct,
            "recommendation": "Consider if this column should have a default value or be excluded"
        })
    elif null_pct >= 10:
        issues.append({
            "table_name": full_table,
            "column_name": profile["column_name"],
            "category": "completeness",
            "severity": "warning",
            "issue_type": "moderate_null_rate",
            "description": f"{null_pct}% of values are NULL",
            "affected_rows": profile["null_count"],
            "affected_percentage": null_pct,
            "recommendation": "Review if NULL values are expected for this column"
        })

    # Constant column
    if profile["distinct_count"] == 1 and profile["total_rows"] > 100:
        issues.append({
            "table_name": full_table,
            "column_name": profile["column_name"],
            "category": "validity",
            "severity": "warning",
            "issue_type": "constant_column",
            "description": "Column has only one distinct value",
            "affected_rows": profile["total_rows"],
            "affected_percentage": 100.0,
            "recommendation": "Consider removing this column or adding a default in dbt"
        })

    # Low cardinality
    distinct_pct = profile.get("distinct_percentage", 100)
    if distinct_pct < 1 and profile["total_rows"] > 1000:
        issues.append({
            "table_name": full_table,
            "column_name": profile["column_name"],
            "category": "validity",
            "severity": "info",
            "issue_type": "low_cardinality",
            "description": f"Only {profile['distinct_count']} distinct values ({distinct_pct}%)",
            "affected_rows": profile["total_rows"],
            "affected_percentage": 100.0,
            "recommendation": "Consider if this should be a dimension/lookup table"
        })

    return issues


def _check_table_duplicates(cursor, full_table: str, schema: str, table: str, total_rows: int) -> List[Dict]:
    """Check for duplicate rows"""
    issues = []

    if total_rows == 0:
        return issues

    # Get primary key columns
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
          AND kcu.TABLE_SCHEMA = ?
          AND kcu.TABLE_NAME = ?
        ORDER BY kcu.ORDINAL_POSITION
    """, schema, table)

    pk_columns = [row[0] for row in cursor.fetchall()]

    if not pk_columns:
        issues.append({
            "table_name": f"{schema}.{table}",
            "column_name": None,
            "category": "uniqueness",
            "severity": "warning",
            "issue_type": "no_primary_key",
            "description": "Table has no primary key defined",
            "affected_rows": 0,
            "affected_percentage": 0,
            "recommendation": "Consider adding a surrogate key in dbt transformation"
        })

    return issues


def _check_foreign_keys(cursor) -> List[Dict]:
    """Check for foreign key violations"""
    issues = []

    # Get all foreign keys
    cursor.execute("""
        SELECT
            fk.name AS fk_name,
            OBJECT_SCHEMA_NAME(fk.parent_object_id) AS child_schema,
            OBJECT_NAME(fk.parent_object_id) AS child_table,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS child_column,
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS parent_schema,
            OBJECT_NAME(fk.referenced_object_id) AS parent_table,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS parent_column
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    """)

    foreign_keys = cursor.fetchall()

    for fk in foreign_keys:
        fk_name, child_schema, child_table, child_col, parent_schema, parent_table, parent_col = fk

        try:
            # Check for orphaned records
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM [{child_schema}].[{child_table}] c
                WHERE c.[{child_col}] IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM [{parent_schema}].[{parent_table}] p
                      WHERE p.[{parent_col}] = c.[{child_col}]
                  )
            """)

            orphan_count = cursor.fetchone()[0]

            if orphan_count > 0:
                issues.append({
                    "table_name": f"{child_schema}.{child_table}",
                    "column_name": child_col,
                    "category": "consistency",
                    "severity": "error",
                    "issue_type": "orphaned_records",
                    "description": f"{orphan_count} orphaned records (FK: {fk_name} -> {parent_schema}.{parent_table}.{parent_col})",
                    "affected_rows": orphan_count,
                    "affected_percentage": 0,
                    "recommendation": "Orphaned records will fail dbt relationship tests - consider cleanup"
                })

        except Exception as e:
            logger.warning(f"Error checking FK {fk_name}: {e}")

    return issues


def _calculate_score(report: Dict) -> float:
    """Calculate overall quality score (0-100)"""
    score = 100.0

    # Critical penalties
    score -= report.get("critical_issues", 0) * 20
    score = max(score, 0)

    # Error penalties
    if score > 20:
        score -= report.get("error_issues", 0) * 10
        score = max(score, 20)

    # Warning penalties
    if score > 50:
        score -= report.get("warning_issues", 0) * 2
        score = max(score, 50)

    return round(score, 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
