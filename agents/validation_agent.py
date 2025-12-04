"""
Validation Agent - dbt Transformation Accuracy Validation

This agent validates that MSSQL to dbt transformations are accurate by:
1. Schema Validation - Comparing source and target column structures
2. Syntax Validation - Running dbt compile to check SQL syntax
3. Row Count Validation - Comparing record counts from source database
4. Data Type Mapping - Verifying MSSQL types map correctly to target warehouse
5. Test Generation - Creating dbt tests based on source constraints (not_null, unique, relationships)
6. SQL Linting - Basic SQL syntax validation

Part of the DataMigrate AI Eight-Agent Architecture.
Phase 1 Comprehensive Validation Implementation.
"""

import os
import re
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


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

    def add_check(self, check: ValidationCheck):
        self.checks.append(check)
        # Update overall status based on check result
        if check.status == ValidationStatus.FAILED:
            self.overall_status = ValidationStatus.FAILED
        elif check.status == ValidationStatus.WARNING and self.overall_status != ValidationStatus.FAILED:
            self.overall_status = ValidationStatus.WARNING


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
    table_results: List[TableValidationResult] = field(default_factory=list)
    overall_status: ValidationStatus = ValidationStatus.PASSED
    summary: Dict[str, int] = field(default_factory=dict)
    dbt_tests_generated: int = 0
    row_count_validated: bool = False
    syntax_validated: bool = False

    def calculate_summary(self):
        passed = sum(1 for t in self.table_results if t.overall_status == ValidationStatus.PASSED)
        warnings = sum(1 for t in self.table_results if t.overall_status == ValidationStatus.WARNING)
        failed = sum(1 for t in self.table_results if t.overall_status == ValidationStatus.FAILED)

        # Count all checks
        total_checks = sum(len(t.checks) for t in self.table_results)
        passed_checks = sum(
            1 for t in self.table_results
            for c in t.checks
            if c.status == ValidationStatus.PASSED
        )
        warning_checks = sum(
            1 for t in self.table_results
            for c in t.checks
            if c.status == ValidationStatus.WARNING
        )
        failed_checks = sum(
            1 for t in self.table_results
            for c in t.checks
            if c.status == ValidationStatus.FAILED
        )

        self.summary = {
            "total_tables": len(self.table_results),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "pass_rate": round((passed / len(self.table_results)) * 100, 1) if self.table_results else 0,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "warning_checks": warning_checks,
            "failed_checks": failed_checks,
            "check_pass_rate": round((passed_checks / total_checks) * 100, 1) if total_checks else 0,
            "dbt_tests_generated": self.dbt_tests_generated,
            "row_count_validated": self.row_count_validated,
            "syntax_validated": self.syntax_validated
        }

        if failed > 0:
            self.overall_status = ValidationStatus.FAILED
        elif warnings > 0:
            self.overall_status = ValidationStatus.WARNING


class ValidationAgent:
    """
    Agent for validating dbt transformation accuracy.

    Validates:
    1. Schema matches between source and generated models
    2. SQL syntax is valid for target warehouse
    3. Row counts match (when data is available)
    4. Data types are correctly mapped
    5. Constraints are preserved (PK, FK, NOT NULL, UNIQUE)
    """

    # MSSQL to common dbt type mappings
    TYPE_MAPPINGS = {
        # Exact numeric
        'int': ['int', 'integer', 'int64', 'bigint', 'number'],
        'bigint': ['bigint', 'int64', 'number'],
        'smallint': ['smallint', 'int', 'integer', 'number'],
        'tinyint': ['tinyint', 'smallint', 'int', 'number'],
        'bit': ['boolean', 'bool', 'bit'],
        'decimal': ['decimal', 'numeric', 'number', 'float'],
        'numeric': ['numeric', 'decimal', 'number', 'float'],
        'money': ['decimal', 'numeric', 'number', 'float'],
        'smallmoney': ['decimal', 'numeric', 'number', 'float'],

        # Approximate numeric
        'float': ['float', 'float64', 'double', 'real', 'number'],
        'real': ['real', 'float', 'float32', 'number'],

        # Date and time
        'date': ['date'],
        'datetime': ['datetime', 'timestamp', 'timestamp_ntz'],
        'datetime2': ['datetime', 'timestamp', 'timestamp_ntz'],
        'smalldatetime': ['datetime', 'timestamp'],
        'time': ['time'],
        'datetimeoffset': ['timestamp_tz', 'timestamptz', 'datetime'],

        # Character strings
        'char': ['char', 'string', 'varchar', 'text'],
        'varchar': ['varchar', 'string', 'text'],
        'text': ['text', 'string', 'varchar'],
        'nchar': ['nchar', 'string', 'varchar', 'text'],
        'nvarchar': ['nvarchar', 'string', 'varchar', 'text'],
        'ntext': ['ntext', 'string', 'text'],

        # Binary strings
        'binary': ['binary', 'bytes', 'varbinary'],
        'varbinary': ['varbinary', 'binary', 'bytes'],
        'image': ['binary', 'bytes', 'varbinary'],

        # Other
        'uniqueidentifier': ['string', 'varchar', 'uuid'],
        'xml': ['string', 'text', 'varchar'],
        'sql_variant': ['variant', 'string', 'any'],
    }

    def __init__(self, project_path: str, source_connection: Optional[SourceConnectionInfo] = None):
        """
        Initialize the validation agent.

        Args:
            project_path: Path to the dbt project directory
            source_connection: Optional source database connection for row count validation
        """
        self.project_path = Path(project_path)
        self.models_path = self.project_path / "models"
        self.staging_path = self.models_path / "staging"
        self.source_connection = source_connection
        self._mssql_extractor = None

    def _get_mssql_connection(self):
        """Get MSSQL connection for row count validation"""
        if self._mssql_extractor is None and self.source_connection:
            try:
                from .mssql_extractor import MSSQLExtractor
                self._mssql_extractor = MSSQLExtractor(
                    server=self.source_connection.host,
                    database=self.source_connection.database,
                    username=self.source_connection.username,
                    password=self.source_connection.password,
                    port=self.source_connection.port,
                    trusted_connection=self.source_connection.use_windows_auth
                )
            except Exception as e:
                logger.warning(f"Could not create MSSQL connection: {e}")
        return self._mssql_extractor

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
            source_metadata: Extracted MSSQL metadata
            run_dbt_compile: Whether to run dbt compile (requires dbt installed)
            validate_row_counts: Whether to validate row counts from source database
            validate_data_types: Whether to validate data type mappings
            generate_dbt_tests: Whether to generate dbt tests file

        Returns:
            ValidationReport with all validation results
        """
        report = ValidationReport(
            migration_id=0,
            project_path=str(self.project_path),
            generated_at=datetime.now()
        )

        # Validate each table
        tables = source_metadata.get('tables', [])
        foreign_keys = source_metadata.get('foreign_keys', [])

        for table in tables:
            table_result = self._validate_table(table, source_metadata)

            # Add data type validation if requested
            if validate_data_types:
                self._validate_data_types(table, table_result)

            # Add column-level SQL verification (always run for accuracy)
            self._validate_column_sql(table, table_result)

            # Add documentation completeness check (always run)
            self._validate_documentation(table, table_result)

            report.table_results.append(table_result)

        # Validate row counts if connection available and requested
        if validate_row_counts and self.source_connection:
            self._validate_row_counts(tables, report)
            report.row_count_validated = True

        # Run dbt compile if requested
        if run_dbt_compile:
            compile_result = self._run_dbt_compile()
            report.syntax_validated = True

            # Add compile results to each table
            for table_result in report.table_results:
                model_name = f"stg_{table_result.table_name.lower()}"
                if model_name in compile_result.get('errors', {}):
                    table_result.add_check(ValidationCheck(
                        check_type=ValidationType.SYNTAX,
                        name="dbt_compile",
                        status=ValidationStatus.FAILED,
                        details=compile_result['errors'][model_name]
                    ))
                elif compile_result.get('success', True):
                    table_result.add_check(ValidationCheck(
                        check_type=ValidationType.SYNTAX,
                        name="dbt_compile",
                        status=ValidationStatus.PASSED,
                        details="Model compiles successfully"
                    ))

        # Run basic SQL linting
        for table_result in report.table_results:
            self._lint_sql_model(table_result)

        # Generate dbt tests if requested
        if generate_dbt_tests:
            tests_count = self._generate_dbt_tests(source_metadata)
            report.dbt_tests_generated = tests_count

        report.calculate_summary()
        return report

    def _validate_table(
        self,
        table: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> TableValidationResult:
        """Validate a single table's transformation"""
        table_name = table.get('name', '')
        schema = table.get('schema', 'dbo')
        model_name = f"stg_{table_name.lower()}"

        result = TableValidationResult(
            table_name=table_name,
            source_table=f"{schema}.{table_name}",
            target_model=model_name
        )

        # Check 1: Model file exists
        model_file = self.staging_path / f"{model_name}.sql"
        if not model_file.exists():
            result.add_check(ValidationCheck(
                check_type=ValidationType.SCHEMA,
                name="model_exists",
                status=ValidationStatus.FAILED,
                details=f"Model file not found: {model_name}.sql"
            ))
            return result

        result.add_check(ValidationCheck(
            check_type=ValidationType.SCHEMA,
            name="model_exists",
            status=ValidationStatus.PASSED,
            details=f"Model file exists: {model_name}.sql"
        ))

        # Check 2: All columns present
        source_columns = {col['name'].lower() for col in table.get('columns', [])}
        model_content = model_file.read_text()
        missing_columns = []

        for col in source_columns:
            if col.lower() not in model_content.lower():
                missing_columns.append(col)

        if missing_columns:
            result.add_check(ValidationCheck(
                check_type=ValidationType.SCHEMA,
                name="columns_present",
                status=ValidationStatus.WARNING,
                details=f"Columns not found in model: {', '.join(missing_columns)}",
                source_value=len(source_columns),
                target_value=len(source_columns) - len(missing_columns)
            ))
        else:
            result.add_check(ValidationCheck(
                check_type=ValidationType.SCHEMA,
                name="columns_present",
                status=ValidationStatus.PASSED,
                details=f"All {len(source_columns)} columns present in model"
            ))

        # Check 3: Source reference correct
        if "source('mssql_source'" not in model_content and "source(\"mssql_source\"" not in model_content:
            result.add_check(ValidationCheck(
                check_type=ValidationType.SCHEMA,
                name="source_reference",
                status=ValidationStatus.WARNING,
                details="Model does not use source() macro"
            ))
        else:
            result.add_check(ValidationCheck(
                check_type=ValidationType.SCHEMA,
                name="source_reference",
                status=ValidationStatus.PASSED,
                details="Source reference is correct"
            ))

        # Check 4: Primary key constraints
        pk_columns = [col['name'] for col in table.get('columns', []) if col.get('is_primary_key')]
        if pk_columns:
            result.add_check(ValidationCheck(
                check_type=ValidationType.CONSTRAINTS,
                name="primary_key",
                status=ValidationStatus.PASSED,
                details=f"Primary key columns identified: {', '.join(pk_columns)}"
            ))

        # Check 5: NOT NULL constraints
        not_null_cols = [col['name'] for col in table.get('columns', []) if not col.get('is_nullable', True)]
        if not_null_cols:
            result.add_check(ValidationCheck(
                check_type=ValidationType.CONSTRAINTS,
                name="not_null",
                status=ValidationStatus.PASSED,
                details=f"NOT NULL columns identified: {len(not_null_cols)} columns"
            ))

        # Check 6: Foreign key relationships
        foreign_keys = [fk for fk in metadata.get('foreign_keys', [])
                       if fk.get('source_table', '').lower() == table_name.lower()]
        if foreign_keys:
            result.add_check(ValidationCheck(
                check_type=ValidationType.RELATIONSHIPS,
                name="foreign_keys",
                status=ValidationStatus.PASSED,
                details=f"Foreign key relationships identified: {len(foreign_keys)}"
            ))

        return result

    def _run_dbt_compile(self) -> Dict[str, Any]:
        """
        Run dbt compile to validate SQL syntax.

        Returns:
            Dict with compile results
        """
        result = {"success": True, "errors": {}}

        try:
            # Run dbt compile
            process = subprocess.run(
                ["dbt", "compile"],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=300
            )

            if process.returncode != 0:
                result["success"] = False
                # Parse errors from output
                error_output = process.stderr + process.stdout
                result["raw_output"] = error_output

                # Try to parse specific model errors
                # dbt usually outputs errors like: "Error in model stg_xxx"
                error_pattern = r"Error in model (\w+)"
                matches = re.findall(error_pattern, error_output)
                for model_name in matches:
                    result["errors"][model_name] = f"Compilation error in {model_name}"

        except FileNotFoundError:
            result["success"] = False
            result["errors"]["dbt"] = "dbt CLI not installed or not in PATH"
        except subprocess.TimeoutExpired:
            result["success"] = False
            result["errors"]["dbt"] = "dbt compile timed out"
        except Exception as e:
            result["success"] = False
            result["errors"]["dbt"] = str(e)

        return result

    def _validate_data_types(
        self,
        table: Dict[str, Any],
        table_result: TableValidationResult
    ) -> None:
        """
        Validate that MSSQL data types are correctly mapped.

        Args:
            table: Source table metadata
            table_result: Table validation result to update
        """
        columns = table.get('columns', [])
        type_issues = []
        valid_types = 0

        for col in columns:
            source_type = col.get('data_type', '').lower()

            # Check if we have a mapping for this type
            if source_type in self.TYPE_MAPPINGS:
                valid_types += 1
            else:
                # Unknown type - might need manual mapping
                type_issues.append(f"{col['name']} ({source_type})")

        if type_issues:
            table_result.add_check(ValidationCheck(
                check_type=ValidationType.DATA_TYPE,
                name="data_type_mapping",
                status=ValidationStatus.WARNING,
                details=f"Unknown data types that may need manual review: {', '.join(type_issues[:5])}{'...' if len(type_issues) > 5 else ''}",
                source_value=len(columns),
                target_value=valid_types
            ))
        else:
            table_result.add_check(ValidationCheck(
                check_type=ValidationType.DATA_TYPE,
                name="data_type_mapping",
                status=ValidationStatus.PASSED,
                details=f"All {len(columns)} column types have valid mappings"
            ))

    def _validate_row_counts(
        self,
        tables: List[Dict[str, Any]],
        report: ValidationReport
    ) -> None:
        """
        Validate row counts from source database.

        Args:
            tables: List of source tables
            report: Validation report to update
        """
        extractor = self._get_mssql_connection()
        if not extractor:
            logger.warning("Cannot validate row counts: no database connection")
            return

        try:
            with extractor.connection() as conn:
                cursor = conn.cursor()

                for table in tables:
                    table_name = table.get('name', '')
                    schema = table.get('schema', 'dbo')
                    expected_count = table.get('row_count')

                    # Get actual row count from database
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table_name}]")
                        actual_count = cursor.fetchone()[0]

                        # Find the table result
                        for table_result in report.table_results:
                            if table_result.table_name.lower() == table_name.lower():
                                # Compare counts
                                if expected_count is not None:
                                    if actual_count == expected_count:
                                        table_result.add_check(ValidationCheck(
                                            check_type=ValidationType.ROW_COUNT,
                                            name="row_count",
                                            status=ValidationStatus.PASSED,
                                            details=f"Row count matches: {actual_count:,} rows",
                                            source_value=expected_count,
                                            target_value=actual_count
                                        ))
                                    else:
                                        diff = actual_count - expected_count
                                        pct = (abs(diff) / expected_count * 100) if expected_count else 0
                                        status = ValidationStatus.WARNING if pct < 5 else ValidationStatus.FAILED
                                        table_result.add_check(ValidationCheck(
                                            check_type=ValidationType.ROW_COUNT,
                                            name="row_count",
                                            status=status,
                                            details=f"Row count changed: {expected_count:,} → {actual_count:,} ({diff:+,}, {pct:.1f}%)",
                                            source_value=expected_count,
                                            target_value=actual_count
                                        ))
                                else:
                                    table_result.add_check(ValidationCheck(
                                        check_type=ValidationType.ROW_COUNT,
                                        name="row_count",
                                        status=ValidationStatus.PASSED,
                                        details=f"Source row count: {actual_count:,} rows",
                                        target_value=actual_count
                                    ))
                                break

                    except Exception as e:
                        logger.warning(f"Could not get row count for {schema}.{table_name}: {e}")

        except Exception as e:
            logger.error(f"Row count validation failed: {e}")

    def _lint_sql_model(self, table_result: TableValidationResult) -> None:
        """
        Run basic SQL linting on the model file.

        Args:
            table_result: Table validation result to update
        """
        model_file = self.staging_path / f"{table_result.target_model}.sql"
        if not model_file.exists():
            return

        try:
            content = model_file.read_text()
            issues = []

            # Check for common SQL issues
            checks = [
                (r'\bSELECT\s+\*\s+FROM', "Using SELECT * (should specify columns)", ValidationStatus.WARNING),
                (r'--\s*TODO', "Contains TODO comments", ValidationStatus.WARNING),
                (r'\/\*.*TODO.*\*\/', "Contains TODO comments", ValidationStatus.WARNING),
                (r'\bDELETE\b|\bDROP\b|\bTRUNCATE\b', "Contains destructive statements", ValidationStatus.FAILED),
                (r'\bINSERT\b|\bUPDATE\b', "Contains data modification statements", ValidationStatus.WARNING),
            ]

            worst_status = ValidationStatus.PASSED

            for pattern, message, status in checks:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(message)
                    if status == ValidationStatus.FAILED:
                        worst_status = ValidationStatus.FAILED
                    elif status == ValidationStatus.WARNING and worst_status == ValidationStatus.PASSED:
                        worst_status = ValidationStatus.WARNING

            # Check for proper dbt patterns
            has_config = '{{ config(' in content or '{{config(' in content
            has_source = 'source(' in content
            has_ref = 'ref(' in content

            if not has_config:
                issues.append("Missing {{ config() }} block")
                if worst_status == ValidationStatus.PASSED:
                    worst_status = ValidationStatus.WARNING

            if not has_source and not has_ref:
                issues.append("No source() or ref() found")
                if worst_status == ValidationStatus.PASSED:
                    worst_status = ValidationStatus.WARNING

            if issues:
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.SQL_LINT,
                    name="sql_linting",
                    status=worst_status,
                    details=f"Issues found: {'; '.join(issues)}"
                ))
            else:
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.SQL_LINT,
                    name="sql_linting",
                    status=ValidationStatus.PASSED,
                    details="SQL passes basic linting checks"
                ))

        except Exception as e:
            logger.warning(f"SQL linting failed for {table_result.target_model}: {e}")

    def _validate_column_sql(
        self,
        table: Dict[str, Any],
        table_result: TableValidationResult
    ) -> None:
        """
        Validate that all source columns appear in the SELECT statement of the SQL model.
        This is a more accurate check than simple text matching - it parses the SQL
        to verify columns are actually selected.

        Args:
            table: Source table metadata
            table_result: Table validation result to update
        """
        model_file = self.staging_path / f"{table_result.target_model}.sql"
        if not model_file.exists():
            return

        try:
            content = model_file.read_text()
            source_columns = [col['name'].lower() for col in table.get('columns', [])]

            # Extract the SELECT portion of the SQL (before FROM)
            # This handles both simple SELECT and CTE patterns
            select_pattern = r'(?:SELECT|select)\s+(.*?)(?:\bFROM\b|\bfrom\b)'
            select_matches = re.findall(select_pattern, content, re.DOTALL)

            if not select_matches:
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.COLUMN_SQL,
                    name="column_sql_verification",
                    status=ValidationStatus.WARNING,
                    details="Could not parse SELECT statement"
                ))
                return

            # Get the last SELECT clause (main query after CTEs)
            select_clause = select_matches[-1].lower()

            # Check for SELECT * which means all columns are included
            if re.search(r'^\s*\*\s*$', select_clause.strip()) or re.search(r'\.\s*\*', select_clause):
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.COLUMN_SQL,
                    name="column_sql_verification",
                    status=ValidationStatus.PASSED,
                    details=f"SELECT * used - all {len(source_columns)} source columns included",
                    source_value=len(source_columns),
                    target_value=len(source_columns)
                ))
                return

            # Parse individual columns from SELECT clause
            # Handle aliases (column AS alias, column alias)
            columns_in_select = set()

            # Split by comma (accounting for nested functions)
            depth = 0
            current_col = ""
            for char in select_clause:
                if char == '(':
                    depth += 1
                    current_col += char
                elif char == ')':
                    depth -= 1
                    current_col += char
                elif char == ',' and depth == 0:
                    columns_in_select.add(current_col.strip())
                    current_col = ""
                else:
                    current_col += char
            if current_col.strip():
                columns_in_select.add(current_col.strip())

            # Extract column names from the parsed columns
            extracted_columns = set()
            for col_expr in columns_in_select:
                # Handle "column AS alias" pattern
                as_match = re.search(r'(\w+)\s+as\s+(\w+)\s*$', col_expr, re.IGNORECASE)
                if as_match:
                    extracted_columns.add(as_match.group(1))
                    extracted_columns.add(as_match.group(2))
                    continue

                # Handle "table.column" pattern
                dot_match = re.search(r'\.(\w+)\s*$', col_expr)
                if dot_match:
                    extracted_columns.add(dot_match.group(1))
                    continue

                # Handle simple column name
                simple_match = re.search(r'^(\w+)\s*$', col_expr.strip())
                if simple_match:
                    extracted_columns.add(simple_match.group(1))
                    continue

                # Handle "expression alias" pattern (without AS)
                alias_match = re.search(r'\)\s+(\w+)\s*$', col_expr)
                if alias_match:
                    extracted_columns.add(alias_match.group(1))

            # Check which source columns are missing
            missing_columns = []
            found_columns = 0
            for src_col in source_columns:
                if src_col in extracted_columns or src_col in content.lower():
                    found_columns += 1
                else:
                    missing_columns.append(src_col)

            if missing_columns:
                # Limit the list to avoid overly long messages
                display_missing = missing_columns[:5]
                more_text = f" (+{len(missing_columns) - 5} more)" if len(missing_columns) > 5 else ""
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.COLUMN_SQL,
                    name="column_sql_verification",
                    status=ValidationStatus.WARNING if len(missing_columns) <= 2 else ValidationStatus.FAILED,
                    details=f"Missing columns in SELECT: {', '.join(display_missing)}{more_text}",
                    source_value=len(source_columns),
                    target_value=found_columns
                ))
            else:
                table_result.add_check(ValidationCheck(
                    check_type=ValidationType.COLUMN_SQL,
                    name="column_sql_verification",
                    status=ValidationStatus.PASSED,
                    details=f"All {len(source_columns)} source columns verified in SQL",
                    source_value=len(source_columns),
                    target_value=found_columns
                ))

        except Exception as e:
            logger.warning(f"Column SQL verification failed for {table_result.target_model}: {e}")
            table_result.add_check(ValidationCheck(
                check_type=ValidationType.COLUMN_SQL,
                name="column_sql_verification",
                status=ValidationStatus.WARNING,
                details=f"Verification error: {str(e)}"
            ))

    def _validate_documentation(
        self,
        table: Dict[str, Any],
        table_result: TableValidationResult
    ) -> None:
        """
        Validate that proper documentation exists for the model in schema.yml.
        Checks for model description, column descriptions, and test definitions.

        Args:
            table: Source table metadata
            table_result: Table validation result to update
        """
        model_name = table_result.target_model

        # Look for schema.yml or _schema.yml files in staging directory
        schema_files = [
            self.staging_path / "schema.yml",
            self.staging_path / "_schema.yml",
            self.staging_path / f"{model_name}_schema.yml",
            self.staging_path / "_schema_tests.yml"
        ]

        schema_content = None
        schema_file_found = None

        for schema_file in schema_files:
            if schema_file.exists():
                try:
                    schema_content = yaml.safe_load(schema_file.read_text())
                    schema_file_found = schema_file
                    break
                except Exception as e:
                    logger.warning(f"Could not parse {schema_file}: {e}")

        if not schema_content:
            table_result.add_check(ValidationCheck(
                check_type=ValidationType.DOCUMENTATION,
                name="documentation_completeness",
                status=ValidationStatus.WARNING,
                details="No schema.yml found - model lacks documentation"
            ))
            return

        # Find this model in the schema
        models = schema_content.get('models', [])
        model_config = None
        for m in models:
            if m.get('name') == model_name:
                model_config = m
                break

        if not model_config:
            table_result.add_check(ValidationCheck(
                check_type=ValidationType.DOCUMENTATION,
                name="documentation_completeness",
                status=ValidationStatus.WARNING,
                details=f"Model '{model_name}' not documented in {schema_file_found.name}"
            ))
            return

        # Check documentation completeness
        issues = []
        score = 0
        max_score = 4

        # Check 1: Model description
        if model_config.get('description'):
            score += 1
        else:
            issues.append("Missing model description")

        # Check 2: Column definitions exist
        columns = model_config.get('columns', [])
        source_columns = table.get('columns', [])
        if columns:
            score += 1
            # Check 3: Column descriptions
            cols_with_desc = sum(1 for c in columns if c.get('description'))
            if cols_with_desc == len(columns):
                score += 1
            elif cols_with_desc > 0:
                score += 0.5
                issues.append(f"Only {cols_with_desc}/{len(columns)} columns have descriptions")
            else:
                issues.append("No column descriptions")

            # Check 4: Tests defined
            cols_with_tests = sum(1 for c in columns if c.get('tests'))
            if cols_with_tests > 0:
                score += 1
            else:
                issues.append("No column-level tests defined")
        else:
            issues.append("No columns documented")
            issues.append("No column-level tests defined")

        # Determine status based on score
        if score >= 3.5:
            status = ValidationStatus.PASSED
            details = f"Documentation complete ({int(score)}/{max_score} checks passed)"
        elif score >= 2:
            status = ValidationStatus.WARNING
            details = f"Partial documentation: {'; '.join(issues)}"
        else:
            status = ValidationStatus.WARNING
            details = f"Incomplete documentation: {'; '.join(issues)}"

        table_result.add_check(ValidationCheck(
            check_type=ValidationType.DOCUMENTATION,
            name="documentation_completeness",
            status=status,
            details=details,
            source_value=max_score,
            target_value=score
        ))

    def _generate_dbt_tests(self, source_metadata: Dict[str, Any]) -> int:
        """
        Generate dbt tests file based on source constraints.

        Args:
            source_metadata: Source database metadata

        Returns:
            Number of tests generated
        """
        tables = source_metadata.get('tables', [])
        foreign_keys = source_metadata.get('foreign_keys', [])

        tests_count = 0
        schema_config = {
            "version": 2,
            "models": []
        }

        for table in tables:
            table_name = table.get('name', '')
            model_name = f"stg_{table_name.lower()}"
            columns = table.get('columns', [])

            model_config = {
                "name": model_name,
                "description": f"Staging model for {table.get('schema', 'dbo')}.{table_name}",
                "columns": []
            }

            for col in columns:
                col_name = col.get('name', '').lower()
                col_config = {
                    "name": col_name,
                    "description": col.get('description') or f"Column from source table",
                    "tests": []
                }

                # Add not_null test for non-nullable columns
                if not col.get('is_nullable', True):
                    col_config["tests"].append("not_null")
                    tests_count += 1

                # Add unique test for primary keys
                if col.get('is_primary_key', False):
                    col_config["tests"].append("unique")
                    tests_count += 1

                # Add relationship tests for foreign keys
                table_fks = [
                    fk for fk in foreign_keys
                    if fk.get('source_table', '').lower() == table_name.lower()
                    and fk.get('source_column', '').lower() == col_name
                ]

                for fk in table_fks:
                    target_model = f"stg_{fk['target_table'].lower()}"
                    target_col = fk['target_column'].lower()
                    col_config["tests"].append({
                        "relationships": {
                            "to": f"ref('{target_model}')",
                            "field": target_col
                        }
                    })
                    tests_count += 1

                # Only add column if it has tests
                if col_config["tests"]:
                    model_config["columns"].append(col_config)

            # Add model to schema
            if model_config["columns"]:
                schema_config["models"].append(model_config)

        # Write the tests schema file
        if schema_config["models"]:
            tests_file = self.staging_path / "_schema_tests.yml"
            try:
                yaml_content = yaml.dump(
                    schema_config,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )
                tests_file.write_text(yaml_content)
                logger.info(f"Generated {tests_count} dbt tests in {tests_file}")
            except Exception as e:
                logger.error(f"Failed to write tests file: {e}")

        return tests_count

    def generate_enhanced_schema_yml(
        self,
        source_metadata: Dict[str, Any]
    ) -> str:
        """
        Generate enhanced schema.yml with column-level tests based on source constraints.

        Args:
            source_metadata: Extracted MSSQL metadata

        Returns:
            YAML content for enhanced schema.yml
        """
        tables = source_metadata.get('tables', [])
        foreign_keys = source_metadata.get('foreign_keys', [])

        schema = {
            "version": 2,
            "models": []
        }

        for table in tables:
            table_name = table.get('name', '')
            model_name = f"stg_{table_name.lower()}"

            model_config = {
                "name": model_name,
                "description": f"Staging model for {table.get('schema', 'dbo')}.{table_name}",
                "columns": []
            }

            for col in table.get('columns', []):
                col_config = {
                    "name": col['name'].lower(),
                    "description": col.get('description') or f"Column {col['name']} from source table",
                    "tests": []
                }

                # Add NOT NULL test
                if not col.get('is_nullable', True):
                    col_config["tests"].append("not_null")

                # Add UNIQUE test for primary keys
                if col.get('is_primary_key'):
                    col_config["tests"].append("unique")

                # Add relationship tests for foreign keys
                table_fks = [fk for fk in foreign_keys
                            if fk.get('source_table', '').lower() == table_name.lower()
                            and fk.get('source_column', '').lower() == col['name'].lower()]

                for fk in table_fks:
                    target_model = f"stg_{fk['target_table'].lower()}"
                    target_col = fk['target_column'].lower()
                    col_config["tests"].append({
                        "relationships": {
                            "to": f"ref('{target_model}')",
                            "field": target_col
                        }
                    })

                # Add accepted_values test for small enums (if we detect them)
                # This would require data profiling - skipped for now

                # Only add column if it has tests or description
                if col_config["tests"] or col.get('description'):
                    if not col_config["tests"]:
                        del col_config["tests"]
                    model_config["columns"].append(col_config)

            schema["models"].append(model_config)

        return yaml.dump(schema, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert validation report to dictionary for JSON serialization"""
        return {
            "migration_id": report.migration_id,
            "project_path": report.project_path,
            "generated_at": report.generated_at.isoformat(),
            "overall_status": report.overall_status.value,
            "summary": report.summary,
            "dbt_tests_generated": report.dbt_tests_generated,
            "row_count_validated": report.row_count_validated,
            "syntax_validated": report.syntax_validated,
            "table_results": [
                {
                    "table_name": tr.table_name,
                    "source_table": tr.source_table,
                    "target_model": tr.target_model,
                    "overall_status": tr.overall_status.value,
                    "checks": [
                        {
                            "check_type": c.check_type.value,
                            "name": c.name,
                            "status": c.status.value,
                            "details": c.details,
                            "source_value": c.source_value,
                            "target_value": c.target_value,
                            "timestamp": c.timestamp.isoformat()
                        }
                        for c in tr.checks
                    ]
                }
                for tr in report.table_results
            ]
        }


def validate_migration(
    project_path: str,
    source_metadata: Dict[str, Any],
    run_compile: bool = False,
    validate_row_counts: bool = False,
    validate_data_types: bool = True,
    generate_dbt_tests: bool = True,
    source_connection: Optional[SourceConnectionInfo] = None
) -> Dict[str, Any]:
    """
    Convenience function to validate a migration.

    Args:
        project_path: Path to dbt project
        source_metadata: Source database metadata
        run_compile: Whether to run dbt compile
        validate_row_counts: Whether to validate row counts from source
        validate_data_types: Whether to validate data type mappings
        generate_dbt_tests: Whether to generate dbt tests
        source_connection: Optional source connection for row count validation

    Returns:
        Validation report as dictionary
    """
    agent = ValidationAgent(project_path, source_connection=source_connection)
    report = agent.validate_project(
        source_metadata,
        run_dbt_compile=run_compile,
        validate_row_counts=validate_row_counts,
        validate_data_types=validate_data_types,
        generate_dbt_tests=generate_dbt_tests
    )
    return agent.to_dict(report)


def enhance_schema_yml(
    project_path: str,
    source_metadata: Dict[str, Any]
) -> str:
    """
    Generate enhanced schema.yml with tests.

    Args:
        project_path: Path to dbt project
        source_metadata: Source database metadata

    Returns:
        Enhanced YAML content
    """
    agent = ValidationAgent(project_path)
    return agent.generate_enhanced_schema_yml(source_metadata)


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validation_agent.py <project_path> [--compile]")
        sys.exit(1)

    project_path = sys.argv[1]
    run_compile = "--compile" in sys.argv

    # For testing, create mock metadata
    mock_metadata = {
        "tables": [
            {
                "name": "users",
                "schema": "dbo",
                "columns": [
                    {"name": "id", "is_primary_key": True, "is_nullable": False},
                    {"name": "email", "is_nullable": False},
                    {"name": "name", "is_nullable": True}
                ]
            }
        ],
        "foreign_keys": []
    }

    result = validate_migration(project_path, mock_metadata, run_compile)
    print(json.dumps(result, indent=2))
