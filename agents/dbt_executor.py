"""
dbt Executor Agent - Warehouse Deployment

This agent handles deploying dbt projects to data warehouses:
1. Generates profiles.yml for the target warehouse
2. Runs dbt run to create tables/views
3. Runs dbt test to validate data quality
4. Parses and returns results

Supports: Snowflake, BigQuery, Databricks, Amazon Redshift, Microsoft Fabric, Apache Spark

Part of the DataMigrate AI Eight-Agent Architecture.
"""

import os
import re
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class WarehouseType(str, Enum):
    """Supported data warehouse types"""
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    DATABRICKS = "databricks"
    REDSHIFT = "redshift"
    FABRIC = "fabric"  # Microsoft Fabric / Synapse
    SPARK = "spark"  # Apache Spark


class DeploymentStatus(str, Enum):
    """Deployment status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WarehouseConnection:
    """Warehouse connection configuration"""
    warehouse_type: WarehouseType

    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

    # BigQuery
    project: Optional[str] = None
    dataset: Optional[str] = None
    keyfile: Optional[str] = None
    keyfile_json: Optional[Dict] = None
    location: Optional[str] = None

    # Databricks
    host: Optional[str] = None
    http_path: Optional[str] = None
    token: Optional[str] = None
    catalog: Optional[str] = None

    # Amazon Redshift
    redshift_host: Optional[str] = None
    redshift_port: Optional[int] = None
    redshift_database: Optional[str] = None
    redshift_username: Optional[str] = None
    redshift_password: Optional[str] = None
    redshift_schema: Optional[str] = None

    # Microsoft Fabric / Synapse
    fabric_server: Optional[str] = None
    fabric_port: Optional[int] = None
    fabric_database: Optional[str] = None
    fabric_schema: Optional[str] = None
    fabric_authentication: Optional[str] = None  # 'sql' or 'serviceprincipal'
    fabric_username: Optional[str] = None
    fabric_password: Optional[str] = None
    fabric_tenant_id: Optional[str] = None
    fabric_client_id: Optional[str] = None
    fabric_client_secret: Optional[str] = None

    # Apache Spark
    spark_host: Optional[str] = None
    spark_port: Optional[int] = None
    spark_cluster: Optional[str] = None
    spark_method: Optional[str] = None  # 'thrift', 'http', 'session'
    spark_token: Optional[str] = None
    spark_schema: Optional[str] = None



@dataclass
class DbtRunResult:
    """Result of a dbt run command"""
    success: bool
    tables_created: int = 0
    models_succeeded: int = 0
    models_failed: int = 0
    models_skipped: int = 0
    output: str = ""
    error: Optional[str] = None
    run_time_seconds: float = 0


@dataclass
class DbtTestResult:
    """Result of a dbt test command"""
    success: bool
    tests_passed: int = 0
    tests_failed: int = 0
    tests_warned: int = 0
    tests_skipped: int = 0
    output: str = ""
    error: Optional[str] = None
    failed_tests: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """Complete deployment result"""
    deployment_id: Optional[int] = None
    status: DeploymentStatus = DeploymentStatus.PENDING
    dbt_run_result: Optional[DbtRunResult] = None
    dbt_test_result: Optional[DbtTestResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DbtExecutor:
    """
    Agent for executing dbt commands against data warehouses.

    Handles:
    1. Profile generation for target warehouse
    2. dbt run execution
    3. dbt test execution
    4. Result parsing
    """

    def __init__(self, project_path: str, connection: WarehouseConnection):
        """
        Initialize the dbt executor.

        Args:
            project_path: Path to the dbt project directory
            connection: Warehouse connection configuration
        """
        self.project_path = Path(project_path)
        self.connection = connection
        self.profiles_dir = None

    def _generate_profiles_yml(self) -> Path:
        """
        Generate profiles.yml for the target warehouse.

        Returns:
            Path to the generated profiles directory
        """
        # Create temporary directory for profiles
        self.profiles_dir = Path(tempfile.mkdtemp(prefix="dbt_profiles_"))
        profiles_path = self.profiles_dir / "profiles.yml"

        profile_name = "datamigrate_target"

        if self.connection.warehouse_type == WarehouseType.SNOWFLAKE:
            profile = self._generate_snowflake_profile(profile_name)
        elif self.connection.warehouse_type == WarehouseType.BIGQUERY:
            profile = self._generate_bigquery_profile(profile_name)
        elif self.connection.warehouse_type == WarehouseType.DATABRICKS:
            profile = self._generate_databricks_profile(profile_name)
        elif self.connection.warehouse_type == WarehouseType.REDSHIFT:
            profile = self._generate_redshift_profile(profile_name)
        elif self.connection.warehouse_type == WarehouseType.FABRIC:
            profile = self._generate_fabric_profile(profile_name)
        elif self.connection.warehouse_type == WarehouseType.SPARK:
            profile = self._generate_spark_profile(profile_name)
        else:
            raise ValueError(f"Unsupported warehouse type: {self.connection.warehouse_type}")

        # Write profiles.yml
        with open(profiles_path, 'w') as f:
            yaml.dump(profile, f, default_flow_style=False)

        logger.info(f"Generated profiles.yml at {profiles_path}")
        return self.profiles_dir

    def _generate_snowflake_profile(self, profile_name: str) -> Dict:
        """Generate Snowflake dbt profile"""
        return {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "snowflake",
                        "account": self.connection.account,
                        "user": self.connection.username,
                        "password": self.connection.password,
                        "role": self.connection.role or "TRANSFORM",
                        "database": self.connection.database,
                        "warehouse": self.connection.warehouse,
                        "schema": self.connection.schema or "PUBLIC",
                        "threads": 4,
                        "client_session_keep_alive": False,
                    }
                }
            }
        }

    def _generate_bigquery_profile(self, profile_name: str) -> Dict:
        """Generate BigQuery dbt profile"""
        profile = {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "bigquery",
                        "method": "service-account",
                        "project": self.connection.project,
                        "dataset": self.connection.dataset or "staging",
                        "threads": 4,
                        "timeout_seconds": 300,
                        "location": self.connection.location or "US",
                    }
                }
            }
        }

        # Handle keyfile - either path or JSON content
        if self.connection.keyfile:
            profile[profile_name]["outputs"]["prod"]["keyfile"] = self.connection.keyfile
        elif self.connection.keyfile_json:
            # Write keyfile to temp location
            keyfile_path = self.profiles_dir / "bigquery_keyfile.json"
            with open(keyfile_path, 'w') as f:
                json.dump(self.connection.keyfile_json, f)
            profile[profile_name]["outputs"]["prod"]["keyfile"] = str(keyfile_path)

        return profile

    def _generate_databricks_profile(self, profile_name: str) -> Dict:
        """Generate Databricks dbt profile"""
        return {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "databricks",
                        "catalog": self.connection.catalog or "hive_metastore",
                        "schema": self.connection.schema or "default",
                        "host": self.connection.host,
                        "http_path": self.connection.http_path,
                        "token": self.connection.token,
                        "threads": 4,
                    }
                }
            }
        }

    def _generate_redshift_profile(self, profile_name: str) -> Dict:
        """Generate Amazon Redshift dbt profile"""
        return {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "redshift",
                        "host": self.connection.redshift_host,
                        "port": self.connection.redshift_port or 5439,
                        "user": self.connection.redshift_username,
                        "password": self.connection.redshift_password,
                        "dbname": self.connection.redshift_database,
                        "schema": self.connection.redshift_schema or "public",
                        "threads": 4,
                        "keepalives_idle": 240,
                        "connect_timeout": 10,
                    }
                }
            }
        }

    def _generate_fabric_profile(self, profile_name: str) -> Dict:
        """Generate Microsoft Fabric / Synapse dbt profile"""
        profile = {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "fabric",
                        "driver": "ODBC Driver 18 for SQL Server",
                        "server": self.connection.fabric_server,
                        "port": self.connection.fabric_port or 1433,
                        "database": self.connection.fabric_database,
                        "schema": self.connection.fabric_schema or "dbo",
                        "threads": 4,
                    }
                }
            }
        }

        # Handle authentication method
        if self.connection.fabric_authentication == "serviceprincipal":
            profile[profile_name]["outputs"]["prod"]["authentication"] = "ServicePrincipal"
            profile[profile_name]["outputs"]["prod"]["tenant_id"] = self.connection.fabric_tenant_id
            profile[profile_name]["outputs"]["prod"]["client_id"] = self.connection.fabric_client_id
            profile[profile_name]["outputs"]["prod"]["client_secret"] = self.connection.fabric_client_secret
        else:
            # SQL authentication
            profile[profile_name]["outputs"]["prod"]["authentication"] = "sql"
            profile[profile_name]["outputs"]["prod"]["user"] = self.connection.fabric_username
            profile[profile_name]["outputs"]["prod"]["password"] = self.connection.fabric_password

        return profile

    def _generate_spark_profile(self, profile_name: str) -> Dict:
        """Generate Apache Spark dbt profile (using dbt-spark adapter)"""
        profile = {
            profile_name: {
                "target": "prod",
                "outputs": {
                    "prod": {
                        "type": "spark",
                        "method": self.connection.spark_method or "thrift",
                        "host": self.connection.spark_host,
                        "port": self.connection.spark_port or 10000,
                        "schema": self.connection.spark_schema or "default",
                        "threads": 4,
                    }
                }
            }
        }

        # Add cluster for http method (Databricks-style)
        if self.connection.spark_method == "http" and self.connection.spark_cluster:
            profile[profile_name]["outputs"]["prod"]["cluster"] = self.connection.spark_cluster

        # Add token for authentication if provided
        if self.connection.spark_token:
            profile[profile_name]["outputs"]["prod"]["token"] = self.connection.spark_token

        return profile

    def _update_dbt_project_profile(self, profile_name: str):
        """Update dbt_project.yml to use our profile"""
        project_file = self.project_path / "dbt_project.yml"

        if project_file.exists():
            with open(project_file, 'r') as f:
                project_config = yaml.safe_load(f)

            project_config['profile'] = profile_name

            with open(project_file, 'w') as f:
                yaml.dump(project_config, f, default_flow_style=False)

            logger.info(f"Updated dbt_project.yml to use profile: {profile_name}")

    def run_dbt_run(self, full_refresh: bool = False) -> DbtRunResult:
        """
        Execute dbt run command.

        Args:
            full_refresh: Whether to do a full refresh (--full-refresh flag)

        Returns:
            DbtRunResult with execution details
        """
        result = DbtRunResult(success=False)

        try:
            # Generate profiles
            profiles_dir = self._generate_profiles_yml()
            self._update_dbt_project_profile("datamigrate_target")

            # Build command
            cmd = [
                "dbt", "run",
                "--profiles-dir", str(profiles_dir),
                "--project-dir", str(self.project_path)
            ]

            if full_refresh:
                cmd.append("--full-refresh")

            logger.info(f"Executing: {' '.join(cmd)}")

            # Run dbt
            start_time = datetime.now()
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                cwd=str(self.project_path)
            )
            end_time = datetime.now()

            result.run_time_seconds = (end_time - start_time).total_seconds()
            result.output = process.stdout + process.stderr

            # Parse output for results
            result = self._parse_dbt_run_output(result, process.returncode == 0)

        except subprocess.TimeoutExpired:
            result.error = "dbt run timed out after 30 minutes"
            result.success = False
        except FileNotFoundError:
            result.error = "dbt CLI not found. Please install dbt-core and the appropriate adapter."
            result.success = False
        except Exception as e:
            result.error = str(e)
            result.success = False
            logger.error(f"dbt run failed: {e}", exc_info=True)

        return result

    def _parse_dbt_run_output(self, result: DbtRunResult, process_success: bool) -> DbtRunResult:
        """Parse dbt run output to extract model counts"""
        output = result.output

        # Look for summary line like: "Completed successfully. 17 passed, 0 failed, 0 skipped."
        # Or: "Done. PASS=17 WARN=0 ERROR=0 SKIP=0 TOTAL=17"

        # Pattern 1: Newer dbt format
        match = re.search(r'PASS=(\d+)\s+WARN=\d+\s+ERROR=(\d+)\s+SKIP=(\d+)', output)
        if match:
            result.models_succeeded = int(match.group(1))
            result.models_failed = int(match.group(2))
            result.models_skipped = int(match.group(3))
            result.tables_created = result.models_succeeded
            result.success = result.models_failed == 0 and process_success
            return result

        # Pattern 2: Older dbt format
        match = re.search(r'(\d+)\s+(?:passed|of \d+ OK)', output)
        if match:
            result.models_succeeded = int(match.group(1))
            result.tables_created = result.models_succeeded

        match = re.search(r'(\d+)\s+(?:failed|ERROR)', output)
        if match:
            result.models_failed = int(match.group(1))

        match = re.search(r'(\d+)\s+skipped', output)
        if match:
            result.models_skipped = int(match.group(1))

        result.success = result.models_failed == 0 and process_success

        return result

    def run_dbt_test(self) -> DbtTestResult:
        """
        Execute dbt test command.

        Returns:
            DbtTestResult with test results
        """
        result = DbtTestResult(success=False)

        try:
            # Ensure profiles exist
            if not self.profiles_dir:
                self._generate_profiles_yml()
                self._update_dbt_project_profile("datamigrate_target")

            # Build command
            cmd = [
                "dbt", "test",
                "--profiles-dir", str(self.profiles_dir),
                "--project-dir", str(self.project_path)
            ]

            logger.info(f"Executing: {' '.join(cmd)}")

            # Run dbt test
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                cwd=str(self.project_path)
            )

            result.output = process.stdout + process.stderr

            # Parse output for results
            result = self._parse_dbt_test_output(result, process.returncode == 0)

        except subprocess.TimeoutExpired:
            result.error = "dbt test timed out after 30 minutes"
            result.success = False
        except FileNotFoundError:
            result.error = "dbt CLI not found. Please install dbt-core and the appropriate adapter."
            result.success = False
        except Exception as e:
            result.error = str(e)
            result.success = False
            logger.error(f"dbt test failed: {e}", exc_info=True)

        return result

    def _parse_dbt_test_output(self, result: DbtTestResult, process_success: bool) -> DbtTestResult:
        """Parse dbt test output to extract test counts"""
        output = result.output

        # Pattern 1: Newer dbt format
        match = re.search(r'PASS=(\d+)\s+WARN=(\d+)\s+ERROR=(\d+)\s+SKIP=(\d+)', output)
        if match:
            result.tests_passed = int(match.group(1))
            result.tests_warned = int(match.group(2))
            result.tests_failed = int(match.group(3))
            result.tests_skipped = int(match.group(4))
            result.success = result.tests_failed == 0 and process_success
            return result

        # Pattern 2: Count individual test results
        passed = len(re.findall(r'\[PASS\]', output))
        failed = len(re.findall(r'\[FAIL\]|\[ERROR\]', output))
        warned = len(re.findall(r'\[WARN\]', output))
        skipped = len(re.findall(r'\[SKIP\]', output))

        result.tests_passed = passed
        result.tests_failed = failed
        result.tests_warned = warned
        result.tests_skipped = skipped

        # Extract failed test details
        failed_pattern = r'Failure in test (\w+)\s+\(([^)]+)\)'
        for match in re.finditer(failed_pattern, output):
            result.failed_tests.append({
                "test_name": match.group(1),
                "location": match.group(2)
            })

        result.success = result.tests_failed == 0 and process_success

        return result

    def deploy(self, run_tests: bool = True, full_refresh: bool = False) -> DeploymentResult:
        """
        Full deployment: run dbt run and optionally dbt test.

        Args:
            run_tests: Whether to run dbt test after dbt run
            full_refresh: Whether to do a full refresh

        Returns:
            DeploymentResult with complete deployment status
        """
        deployment = DeploymentResult(
            status=DeploymentStatus.RUNNING,
            started_at=datetime.now()
        )

        try:
            # Step 1: dbt run
            logger.info(f"Starting dbt run for project: {self.project_path}")
            run_result = self.run_dbt_run(full_refresh=full_refresh)
            deployment.dbt_run_result = run_result

            if not run_result.success:
                deployment.status = DeploymentStatus.FAILED
                deployment.error = run_result.error or "dbt run failed"
                deployment.completed_at = datetime.now()
                return deployment

            # Step 2: dbt test (optional)
            if run_tests:
                logger.info(f"Starting dbt test for project: {self.project_path}")
                test_result = self.run_dbt_test()
                deployment.dbt_test_result = test_result

                # Deployment is successful even if some tests fail
                # Tests failing is informational, not a deployment failure

            deployment.status = DeploymentStatus.COMPLETED

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error = str(e)
            logger.error(f"Deployment failed: {e}", exc_info=True)

        finally:
            deployment.completed_at = datetime.now()

            # Cleanup temp profiles directory
            if self.profiles_dir and self.profiles_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(self.profiles_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup profiles dir: {e}")

        return deployment

    def to_dict(self, result: DeploymentResult) -> Dict[str, Any]:
        """Convert deployment result to dictionary for JSON serialization"""
        data = {
            "deployment_id": result.deployment_id,
            "status": result.status.value,
            "error": result.error,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        }

        if result.dbt_run_result:
            data["dbt_run"] = {
                "success": result.dbt_run_result.success,
                "tables_created": result.dbt_run_result.tables_created,
                "models_succeeded": result.dbt_run_result.models_succeeded,
                "models_failed": result.dbt_run_result.models_failed,
                "models_skipped": result.dbt_run_result.models_skipped,
                "run_time_seconds": result.dbt_run_result.run_time_seconds,
                "error": result.dbt_run_result.error,
            }

        if result.dbt_test_result:
            data["dbt_test"] = {
                "success": result.dbt_test_result.success,
                "tests_passed": result.dbt_test_result.tests_passed,
                "tests_failed": result.dbt_test_result.tests_failed,
                "tests_warned": result.dbt_test_result.tests_warned,
                "tests_skipped": result.dbt_test_result.tests_skipped,
                "failed_tests": result.dbt_test_result.failed_tests,
                "error": result.dbt_test_result.error,
            }

        return data


def deploy_to_warehouse(
    project_path: str,
    warehouse_type: str,
    connection_config: Dict[str, Any],
    run_tests: bool = True,
    full_refresh: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to deploy a dbt project to a warehouse.

    Args:
        project_path: Path to dbt project
        warehouse_type: Type of warehouse (snowflake, bigquery, databricks, redshift, fabric, postgres)
        connection_config: Connection configuration dictionary
        run_tests: Whether to run dbt test
        full_refresh: Whether to do full refresh

    Returns:
        Deployment result as dictionary
    """
    # Create connection object
    connection = WarehouseConnection(
        warehouse_type=WarehouseType(warehouse_type),
        # Snowflake
        account=connection_config.get('account'),
        warehouse=connection_config.get('warehouse'),
        database=connection_config.get('database'),
        schema=connection_config.get('schema'),
        username=connection_config.get('username'),
        password=connection_config.get('password'),
        role=connection_config.get('role'),
        # BigQuery
        project=connection_config.get('project'),
        dataset=connection_config.get('dataset'),
        keyfile=connection_config.get('keyfile'),
        keyfile_json=connection_config.get('keyfile_json'),
        location=connection_config.get('location'),
        # Databricks
        host=connection_config.get('host'),
        http_path=connection_config.get('http_path'),
        token=connection_config.get('token'),
        catalog=connection_config.get('catalog'),
        # Redshift
        redshift_host=connection_config.get('redshift_host'),
        redshift_port=connection_config.get('redshift_port'),
        redshift_database=connection_config.get('redshift_database'),
        redshift_username=connection_config.get('redshift_username'),
        redshift_password=connection_config.get('redshift_password'),
        redshift_schema=connection_config.get('redshift_schema'),
        # Microsoft Fabric / Synapse
        fabric_server=connection_config.get('fabric_server'),
        fabric_port=connection_config.get('fabric_port'),
        fabric_database=connection_config.get('fabric_database'),
        fabric_schema=connection_config.get('fabric_schema'),
        fabric_authentication=connection_config.get('fabric_authentication'),
        fabric_username=connection_config.get('fabric_username'),
        fabric_password=connection_config.get('fabric_password'),
        fabric_tenant_id=connection_config.get('fabric_tenant_id'),
        fabric_client_id=connection_config.get('fabric_client_id'),
        fabric_client_secret=connection_config.get('fabric_client_secret'),
        # Apache Spark
        spark_host=connection_config.get('spark_host'),
        spark_port=connection_config.get('spark_port'),
        spark_cluster=connection_config.get('spark_cluster'),
        spark_method=connection_config.get('spark_method'),
        spark_token=connection_config.get('spark_token'),
        spark_schema=connection_config.get('spark_schema'),
    )

    executor = DbtExecutor(project_path, connection)
    result = executor.deploy(run_tests=run_tests, full_refresh=full_refresh)

    return executor.to_dict(result)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python dbt_executor.py <project_path> <warehouse_type>")
        print("Example: python dbt_executor.py ./dbt_project snowflake")
        sys.exit(1)

    project_path = sys.argv[1]
    warehouse_type = sys.argv[2]

    # Example config for testing
    test_config = {
        "account": "your_account",
        "warehouse": "COMPUTE_WH",
        "database": "DEV_DB",
        "schema": "STAGING",
        "username": "your_user",
        "password": "your_password",
        "role": "TRANSFORM"
    }

    result = deploy_to_warehouse(
        project_path,
        warehouse_type,
        test_config,
        run_tests=True,
        full_refresh=False
    )

    print(json.dumps(result, indent=2))
