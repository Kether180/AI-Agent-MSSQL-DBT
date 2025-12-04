# DataMigrate AI - Comprehensive Validation Procedures

## Document Information
- **Version:** 1.0
- **Date:** December 4, 2025
- **Classification:** Internal Documentation

---

## 1. Overview

The DataMigrate AI Validation Agent provides comprehensive validation of MSSQL to dbt transformations. This ensures that generated dbt models accurately represent the source database schema, maintain data integrity, and follow best practices.

### 1.1 Validation Philosophy

Our validation approach follows the principle of **"Trust but Verify"**:
- Every transformation is validated against the source schema
- Multiple validation layers catch different types of issues
- Automated test generation ensures ongoing data quality
- Clear reporting helps identify and prioritize fixes

---

## 2. Validation Types

### 2.1 Schema Validation
**Purpose:** Verify that dbt models correctly represent source table structures.

**Checks performed:**
- Model file exists for each source table
- All source columns are present in the model
- Source references use correct `{{ source() }}` syntax
- Column names are preserved (with optional case handling)

**Status outcomes:**
- `PASSED` - Model correctly represents source schema
- `WARNING` - Model exists but may have minor issues
- `FAILED` - Model missing or critically incorrect

### 2.2 Constraint Validation
**Purpose:** Ensure database constraints are documented and testable.

**Checks performed:**
- Primary key columns identified
- NOT NULL constraints documented
- Foreign key relationships tracked
- Unique constraints noted

**Implementation:**
```sql
-- Primary key detected on 'user_id' column
-- Generates dbt test: unique
-- Generates dbt test: not_null
```

### 2.3 Data Type Mapping Validation
**Purpose:** Verify MSSQL types map correctly to target warehouse types.

**Supported type mappings:**

| MSSQL Type | Snowflake | BigQuery | Databricks |
|------------|-----------|----------|------------|
| int, bigint | NUMBER | INT64 | BIGINT |
| varchar, nvarchar | VARCHAR | STRING | STRING |
| datetime, datetime2 | TIMESTAMP_NTZ | DATETIME | TIMESTAMP |
| decimal, numeric | NUMBER(p,s) | NUMERIC | DECIMAL |
| bit | BOOLEAN | BOOL | BOOLEAN |
| uniqueidentifier | VARCHAR(36) | STRING | STRING |
| varbinary, image | BINARY | BYTES | BINARY |

**Status outcomes:**
- `PASSED` - All types have known mappings
- `WARNING` - Unknown types detected (may need manual review)

### 2.4 SQL Linting
**Purpose:** Catch common SQL issues and enforce best practices.

**Checks performed:**
- No `SELECT *` usage (specify columns explicitly)
- No destructive statements (DELETE, DROP, TRUNCATE)
- Proper `{{ config() }}` block present
- Valid `source()` or `ref()` usage
- No TODO comments left in code

### 2.5 Row Count Validation
**Purpose:** Verify data completeness by comparing source row counts.

**Requirements:**
- Source database connection information
- Read access to source tables

**Process:**
1. Query source database for current row counts
2. Compare with counts captured during migration
3. Flag significant changes (>5% difference)

**Status outcomes:**
- `PASSED` - Row counts match
- `WARNING` - Minor change (<5%)
- `FAILED` - Significant change (>5%)

### 2.6 dbt Compile Validation
**Purpose:** Verify SQL syntax by running dbt compile.

**Requirements:**
- dbt CLI installed and in PATH
- Valid dbt project configuration

**Process:**
1. Execute `dbt compile` in project directory
2. Parse output for errors
3. Map errors to specific models

---

## 3. dbt Test Generation

### 3.1 Automatic Test Generation
The validation agent automatically generates dbt tests based on source constraints.

**Tests generated:**

1. **not_null** - For columns marked NOT NULL in source
2. **unique** - For primary key columns
3. **relationships** - For foreign key relationships

### 3.2 Generated Test File Structure

```yaml
version: 2
models:
  - name: stg_users
    description: Staging model for dbo.users
    columns:
      - name: user_id
        description: Primary key
        tests:
          - not_null
          - unique
      - name: email
        tests:
          - not_null
      - name: organization_id
        tests:
          - relationships:
              to: ref('stg_organizations')
              field: organization_id
```

### 3.3 Test File Location
Tests are written to: `models/staging/_schema_tests.yml`

---

## 4. API Endpoints

### 4.1 Validate Migration

**Endpoint:** `POST /migrations/{migration_id}/validate`

**Request Body:**
```json
{
  "run_dbt_compile": false,
  "validate_row_counts": false,
  "validate_data_types": true,
  "generate_dbt_tests": true,
  "source_host": "optional-for-row-counts",
  "source_port": 1433,
  "source_database": "optional",
  "source_username": "optional",
  "source_password": "optional",
  "use_windows_auth": false
}
```

**Response:**
```json
{
  "migration_id": 1,
  "project_path": "/path/to/dbt/project",
  "overall_status": "passed",
  "summary": {
    "total_tables": 17,
    "passed": 15,
    "warnings": 2,
    "failed": 0,
    "pass_rate": 88.2,
    "total_checks": 85,
    "passed_checks": 80,
    "warning_checks": 5,
    "failed_checks": 0,
    "check_pass_rate": 94.1,
    "dbt_tests_generated": 42,
    "row_count_validated": false,
    "syntax_validated": false
  },
  "table_results": [...],
  "dbt_tests_generated": 42,
  "row_count_validated": false,
  "syntax_validated": false
}
```

### 4.2 Enhance Schema

**Endpoint:** `POST /migrations/{migration_id}/enhance-schema`

**Purpose:** Generate enhanced schema.yml with column descriptions and tests.

---

## 5. Frontend Integration

### 5.1 Validation Options

Users can configure validation through checkboxes:

| Option | Default | Description |
|--------|---------|-------------|
| Data Type Mapping | Enabled | Check MSSQL type mappings |
| Generate dbt Tests | Enabled | Auto-generate test file |
| dbt Compile | Disabled | Requires dbt CLI |

### 5.2 Results Display

The validation results UI shows:

1. **Summary Cards** - Tables passed/warned/failed
2. **Check Statistics** - Total checks, dbt tests generated
3. **Pass Rate Bars** - Visual progress indicators
4. **Expandable Tables** - Click to see detailed checks per table

---

## 6. Validation Workflow

### 6.1 Recommended Process

1. **Complete Migration** - Wait for status "completed"
2. **Run Basic Validation** - Default options
3. **Review Results** - Check for warnings/failures
4. **Enable dbt Compile** - If dbt is installed
5. **Download Project** - Get validated dbt project

### 6.2 Handling Failures

| Failure Type | Resolution |
|--------------|------------|
| Missing model file | Re-run migration or manually create |
| Missing columns | Check source schema, update model |
| Unknown data type | Add type mapping or use generic type |
| Syntax error | Fix SQL in model file |
| Constraint missing | Add test to schema.yml |

---

## 7. Best Practices

### 7.1 Pre-Validation Checklist

- [ ] Migration status is "completed"
- [ ] Source database accessible (for row count validation)
- [ ] dbt CLI installed (for compile validation)
- [ ] Review generated files before validation

### 7.2 Post-Validation Actions

1. Address all `FAILED` checks immediately
2. Review `WARNING` checks for potential issues
3. Run `dbt test` to verify generated tests
4. Document any manual adjustments

### 7.3 Continuous Validation

For production environments, consider:
- Scheduled validation runs
- Integration with CI/CD pipelines
- Alerting on validation failures
- Row count drift monitoring

---

## 8. Troubleshooting

### 8.1 Common Issues

**"No dbt project found"**
- Ensure migration completed successfully
- Check project path in migration record

**"dbt compile failed"**
- Verify dbt CLI is installed
- Check dbt_project.yml configuration
- Review profiles.yml for valid target

**"Row count validation skipped"**
- Provide source connection information
- Verify network access to source database

### 8.2 Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 404 | Project not found | Check migration ID |
| 500 | Validation failed | Check server logs |
| TIMEOUT | dbt compile timeout | Reduce model complexity |

---

## 9. Architecture

### 9.1 Component Diagram

```
+-------------------+     +-------------------+
|   Frontend UI     |---->|   Python API      |
| (Vue.js)          |     |   (FastAPI)       |
+-------------------+     +--------+----------+
                                   |
                          +--------v----------+
                          | ValidationAgent   |
                          | - Schema Check    |
                          | - Type Mapping    |
                          | - SQL Linting     |
                          | - dbt Compile     |
                          | - Test Generation |
                          +--------+----------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
    +---------v---------+ +--------v--------+ +--------v--------+
    | Source MSSQL      | | dbt Project     | | Generated Tests |
    | (Row Counts)      | | (SQL Models)    | | (YAML Files)    |
    +-------------------+ +-----------------+ +-----------------+
```

### 9.2 Data Flow

1. User triggers validation from frontend
2. API receives request with options
3. ValidationAgent instantiated with project path
4. Each validation type runs sequentially
5. Results aggregated into ValidationReport
6. Response returned to frontend
7. UI displays results with drill-down capability

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-04 | Initial comprehensive validation implementation |

---

*This document is confidential and intended for internal use only.*
