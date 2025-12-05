# Data Quality Agent

## Status: Beta (60%)

## Overview
The Data Quality Agent performs comprehensive data profiling and validation with 50+ quality checks and ML-based anomaly detection. It uses LangGraph for workflow orchestration and Claude for AI-powered recommendations.

## File Locations
- Main: `agents/data_quality_agent.py`
- API Integration: `agents/api.py`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Quality Agent                            │
│                                                                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │
│  │   Profile   │──▶│  Validate   │──▶│  Detect Anomalies   │    │
│  │    Data     │   │    Rules    │   │                     │    │
│  └─────────────┘   └─────────────┘   └──────────┬──────────┘    │
│                                                  │               │
│  ┌─────────────────────────────────────────────▼───────────┐    │
│  │              Calculate Scores                            │    │
│  └─────────────────────────────────────────────┬───────────┘    │
│                                                  │               │
│  ┌──────────────────────┐   ┌──────────────────▼───────────┐    │
│  │  Apply Remediation   │◀──│   Should Remediate?          │    │
│  │     (optional)       │   │                              │    │
│  └──────────┬───────────┘   └──────────────────────────────┘    │
│             │                                                    │
│  ┌──────────▼───────────────────────────────────────────────┐   │
│  │                  Generate Report                          │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Classes

### Enums

```python
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
```

### Data Classes

```python
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
```

## Main Class: DataQualityAgent

### Initialization

```python
from agents.data_quality_agent import DataQualityAgent

# Initialize with Anthropic API key
agent = DataQualityAgent(anthropic_api_key="your-key")

# Or use environment variable ANTHROPIC_API_KEY
agent = DataQualityAgent()
```

### Core Methods

#### 1. Full Quality Assessment

```python
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
        data: List of data records (each record is a dict)
        table_name: Name of the table/dataset
        rules: Custom quality rules to apply
        auto_remediate: Whether to apply automatic remediation

    Returns:
        Quality assessment results with scores and issues
    """

# Usage Example:
result = await agent.assess_quality(
    data=[
        {"id": 1, "email": "john@example.com", "amount": 150.00},
        {"id": 2, "email": "invalid-email", "amount": -50.00},
    ],
    table_name="customers",
    auto_remediate=False
)

print(f"Overall Score: {result['scores']['overall']:.1f}/100")
print(f"Issues Found: {len(result['issues'])}")
```

#### 2. Data Profiling Only

```python
async def profile_data(
    self,
    data: List[Dict[str, Any]],
    table_name: str = "data"
) -> Dict[str, Any]:
    """
    Profile data without full quality assessment.

    Returns:
        Data profile with statistics and patterns
    """

# Usage:
profile = await agent.profile_data(sample_data, "customers")
print(f"Columns: {len(profile['columns'])}")
print(f"Primary Key Candidates: {profile['primary_key_candidates']}")
```

#### 3. Custom Rule Management

```python
# Add a custom rule
agent.add_rule(QualityRule(
    rule_id="custom_amount",
    name="Amount Range Check",
    rule_type=RuleType.RANGE,
    dimension=QualityDimension.VALIDITY,
    severity=RuleSeverity.ERROR,
    column="amount",
    parameters={"min": 0, "max": 10000},
    description="Amount must be between 0 and 10000"
))

# Get all rules
rules = agent.get_rules()

# Remove a rule
agent.remove_rule("custom_amount")
```

#### 4. Validate Against Specific Rules

```python
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

# Usage:
result = await agent.validate_against_rules(
    data=sample_data,
    rule_ids=["email_format", "positive_amount"]
)
```

## Source Database Scanner

Direct connection to MSSQL for pre-migration quality assessment:

```python
from agents.data_quality_agent import scan_source_data_quality

# Scan source database quality
report = scan_source_data_quality(
    server="localhost",
    database="AdventureWorks",
    username="sa",
    password="password",
    port=1433,
    use_windows_auth=False,
    tables=["dbo.Customers", "dbo.Orders"],  # or None for all
    sample_size=10000
)

print(f"Overall Score: {report['overall_score']}/100")
print(f"Tables Scanned: {report['tables_scanned']}")
print(f"Critical Issues: {report['critical_issues']}")
print(f"Error Issues: {report['error_issues']}")
```

## Default Quality Rules

The agent comes with these built-in rules:

| Rule ID | Name | Type | Description |
|---------|------|------|-------------|
| email_format | Email Format Validation | REGEX | Validates email format |
| phone_format | Phone Number Format | REGEX | Validates phone numbers |
| date_not_future | Date Not in Future | CUSTOM | Transaction dates shouldn't be future |
| positive_amount | Positive Amount | RANGE | Monetary amounts >= 0 |

## Quality Score Calculation

Weighted average across dimensions:

```python
weights = {
    "completeness": 1.0,
    "accuracy": 1.5,
    "validity": 1.5,
    "uniqueness": 1.0,
    "consistency": 1.0,
    "timeliness": 0.5,
    "integrity": 1.5
}
```

## Integration with API

To integrate into the migration pipeline, add to `agents/api.py`:

```python
@router.post("/migrations/{migration_id}/quality-check")
async def run_quality_check(
    migration_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run data quality assessment on source data"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(status_code=404, detail="Migration not found")

    # Get source connection
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == migration.source_connection_id
    ).first()

    # Run quality scan
    report = scan_source_data_quality(
        server=connection.host,
        database=connection.database,
        username=connection.username,
        password=decrypt(connection.password),
        port=connection.port
    )

    # Save report to database
    migration.quality_report = report
    migration.quality_score = report['overall_score']
    db.commit()

    return report
```

## Current Capabilities
- [x] Column-level profiling (type, nulls, distinct, min/max, std_dev)
- [x] Table-level profiling (row count, duplicates)
- [x] Quality checks (null, unique, regex, range, enum, length)
- [x] Pattern detection (email, phone, URL, UUID, date, postal code)
- [x] Anomaly detection (Z-score based outliers)
- [x] Quality scoring by dimension
- [x] AI-powered recommendations (Claude)
- [x] Direct MSSQL source scanning
- [ ] Referential integrity validation
- [ ] Data drift monitoring
- [ ] Real-time streaming quality checks

## Integration Status
- [x] Core profiling engine - COMPLETE
- [x] LangGraph workflow - COMPLETE
- [ ] API endpoint - NEEDS INTEGRATION
- [ ] Frontend display - NEEDS INTEGRATION
- [ ] Pipeline hook - NEEDS INTEGRATION

## TODO - HIGH PRIORITY
1. [ ] Create API endpoint `/migrations/{id}/quality-check`
2. [ ] Add quality check step to migration wizard
3. [ ] Display quality report in frontend
4. [ ] Add quality gate (block migration if score < threshold)
5. [ ] Save quality reports to database

## Dependencies
```
langchain-anthropic
langgraph
pandas
numpy
scipy
pyodbc
```

---
Last Updated: 2024-12-05
