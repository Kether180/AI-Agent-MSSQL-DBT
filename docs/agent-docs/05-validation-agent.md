# Validation Agent

## Status: Beta (50%)

## Overview
The Validation Agent ensures migration accuracy by validating that dbt transformations accurately represent the source MSSQL data. It performs schema validation, SQL syntax checks, row count comparisons, data type mapping verification, and generates dbt tests.

## File Locations
- Main: `agents/validation_agent.py`
- API Integration: `agents/api.py`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Validation Agent                              │
│                                                                   │
│  Source Metadata ──┐                                              │
│                    ▼                                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  For each table:                                             │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐  │ │
│  │  │ Schema Check  │  │ Column Check  │  │  Source Ref     │  │ │
│  │  │ (model exists)│  │ (all present) │  │  (source() ok)  │  │ │
│  │  └───────────────┘  └───────────────┘  └─────────────────┘  │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐  │ │
│  │  │ PK/FK Check   │  │ Data Types    │  │  Column SQL     │  │ │
│  │  │ (constraints) │  │ (mappings ok) │  │  (SELECT verify)│  │ │
│  │  └───────────────┘  └───────────────┘  └─────────────────┘  │ │
│  │  ┌───────────────┐  ┌───────────────┐                       │ │
│  │  │ SQL Linting   │  │ Documentation │                       │ │
│  │  │ (best practic)│  │ (schema.yml)  │                       │ │
│  │  └───────────────┘  └───────────────┘                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│  Optional:                   ▼                                    │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ dbt compile      │  │ Row Count        │                      │
│  │ (syntax check)   │  │ (source compare) │                      │
│  └──────────────────┘  └──────────────────┘                      │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Generate dbt Tests (_schema_tests.yml)          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Classes

### Enums

```python
class ValidationStatus(str, Enum):
    """Validation result status"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationType(str, Enum):
    """Types of validation checks"""
    SCHEMA = "schema"
    SYNTAX = "syntax"
    ROW_COUNT = "row_count"
    DATA_SAMPLE = "data_sample"
    CONSTRAINTS = "constraints"
    RELATIONSHIPS = "relationships"
    DATA_TYPE = "data_type"
    DBT_TEST = "dbt_test"
    SQL_LINT = "sql_lint"
    COLUMN_SQL = "column_sql"
    DOCUMENTATION = "documentation"
```

### Data Classes

```python
@dataclass
class ValidationCheck:
    """Single validation check result"""
    check_type: ValidationType
    name: str
    status: ValidationStatus
    details: str
    source_value: Optional[Any] = None
    target_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TableValidationResult:
    """Validation result for a single table"""
    table_name: str
    source_table: str
    target_model: str
    checks: List[ValidationCheck] = field(default_factory=list)
    overall_status: ValidationStatus = ValidationStatus.PASSED


@dataclass
class SourceConnectionInfo:
    """Source database connection info for validation"""
    host: str
    port: int
    database: str
    username: str = ""
    password: str = ""
    use_windows_auth: bool = False


@dataclass
class ValidationReport:
    """Complete validation report"""
    migration_id: int
    project_path: str
    generated_at: datetime
    table_results: List[TableValidationResult]
    overall_status: ValidationStatus
    summary: Dict[str, int]
    dbt_tests_generated: int
    row_count_validated: bool
    syntax_validated: bool
```

## Main Class: ValidationAgent

### Initialization

```python
from agents.validation_agent import ValidationAgent, SourceConnectionInfo

# Basic initialization (no source connection)
agent = ValidationAgent(project_path="/path/to/dbt/project")

# With source connection for row count validation
source_conn = SourceConnectionInfo(
    host="localhost",
    port=1433,
    database="AdventureWorks",
    username="sa",
    password="password",
    use_windows_auth=False
)
agent = ValidationAgent(
    project_path="/path/to/dbt/project",
    source_connection=source_conn
)
```

### Core Methods

#### 1. Full Project Validation

```python
def validate_project(
    self,
    source_metadata: Dict[str, Any],
    run_dbt_compile: bool = False,
    validate_row_counts: bool = False,
    validate_data_types: bool = True,
    generate_dbt_tests: bool = True
) -> ValidationReport:
    """
    Run full validation of the dbt project against source metadata.

    Args:
        source_metadata: Extracted MSSQL metadata (from extractor agent)
        run_dbt_compile: Whether to run dbt compile (requires dbt installed)
        validate_row_counts: Whether to validate row counts from source
        validate_data_types: Whether to validate data type mappings
        generate_dbt_tests: Whether to generate dbt tests file

    Returns:
        ValidationReport with all validation results
    """

# Usage:
report = agent.validate_project(
    source_metadata=metadata,  # From MSSQL Extractor
    run_dbt_compile=True,
    validate_row_counts=True,
    validate_data_types=True,
    generate_dbt_tests=True
)

print(f"Overall Status: {report.overall_status}")
print(f"Tables Validated: {report.summary['total_tables']}")
print(f"Pass Rate: {report.summary['pass_rate']}%")
print(f"dbt Tests Generated: {report.dbt_tests_generated}")
```

#### 2. Quick Validation Function

```python
from agents.validation_agent import validate_migration

# Convenience function
result = validate_migration(
    project_path="/path/to/dbt/project",
    source_metadata=metadata,
    run_compile=True,
    validate_row_counts=True,
    validate_data_types=True,
    generate_dbt_tests=True,
    source_connection=source_conn
)

# Returns dict for JSON serialization
print(json.dumps(result, indent=2))
```

#### 3. Generate Enhanced Schema YAML

```python
from agents.validation_agent import enhance_schema_yml

# Generate schema.yml with tests based on constraints
yaml_content = enhance_schema_yml(
    project_path="/path/to/dbt/project",
    source_metadata=metadata
)

# Write to file
with open("models/staging/schema.yml", "w") as f:
    f.write(yaml_content)
```

## Type Mappings

MSSQL to target warehouse type mappings:

```python
TYPE_MAPPINGS = {
    # Exact numeric
    'int': ['int', 'integer', 'int64', 'bigint', 'number'],
    'bigint': ['bigint', 'int64', 'number'],
    'decimal': ['decimal', 'numeric', 'number', 'float'],
    'bit': ['boolean', 'bool', 'bit'],

    # Date and time
    'datetime': ['datetime', 'timestamp', 'timestamp_ntz'],
    'datetime2': ['datetime', 'timestamp', 'timestamp_ntz'],
    'date': ['date'],

    # Character strings
    'varchar': ['varchar', 'string', 'text'],
    'nvarchar': ['nvarchar', 'string', 'varchar', 'text'],
}
```

## Validation Checks Performed

| Check | Type | Description |
|-------|------|-------------|
| model_exists | SCHEMA | Model file exists |
| columns_present | SCHEMA | All source columns in model |
| source_reference | SCHEMA | Uses source() macro |
| primary_key | CONSTRAINTS | PK columns identified |
| not_null | CONSTRAINTS | NOT NULL mapped |
| foreign_keys | RELATIONSHIPS | FK relationships captured |
| data_type_mapping | DATA_TYPE | Types have valid mappings |
| sql_linting | SQL_LINT | No bad practices |
| column_sql_verification | COLUMN_SQL | Columns in SELECT |
| documentation_completeness | DOCUMENTATION | schema.yml complete |

## Generated dbt Tests

```yaml
version: 2
models:
  - name: stg_customers
    description: Staging model for dbo.Customers
    columns:
      - name: customer_id
        description: Column from source table
        tests:
          - not_null
          - unique
      - name: email
        tests:
          - not_null
      - name: order_id
        tests:
          - relationships:
              to: ref('stg_orders')
              field: order_id
```

## Integration with API

```python
@router.post("/migrations/{migration_id}/validate")
async def validate_migration_endpoint(
    migration_id: int,
    run_compile: bool = False,
    db: Session = Depends(get_db)
):
    """Validate generated dbt project"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()
    if not migration:
        raise HTTPException(status_code=404, detail="Migration not found")

    result = validate_migration(
        project_path=migration.output_path,
        source_metadata=migration.extracted_metadata,
        run_compile=run_compile,
        validate_row_counts=True,
        generate_dbt_tests=True
    )

    migration.validation_report = result
    migration.validation_status = result['overall_status']
    db.commit()

    return result
```

## Current Capabilities
- [x] Schema validation (model exists, columns present)
- [x] Source reference validation
- [x] Constraint detection (PK, FK, NOT NULL)
- [x] Data type mapping validation
- [x] Row count comparison (with source connection)
- [x] SQL linting (best practices)
- [x] Column SQL verification
- [x] Documentation completeness check
- [x] dbt compile integration
- [x] dbt test generation
- [ ] Sample data comparison
- [ ] Incremental validation

## Integration Status
- [x] Core validation engine - COMPLETE
- [x] dbt compile integration - COMPLETE
- [x] Test generation - COMPLETE
- [ ] API endpoint - NEEDS INTEGRATION
- [ ] Frontend display - NEEDS INTEGRATION

## TODO
1. [ ] Create API endpoint `/migrations/{id}/validate`
2. [ ] Add validation step to migration wizard
3. [ ] Display validation results in frontend
4. [ ] Add automatic validation trigger after generation

## CLI Usage

```bash
python agents/validation_agent.py /path/to/dbt/project --compile
```

## Dependencies
```
pyyaml
pyodbc
dbt-core
```

---
Last Updated: 2024-12-05
