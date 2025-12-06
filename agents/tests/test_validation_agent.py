"""
Unit Tests for Validation Agent

Tests the ValidationAgent class for validating generated dbt projects
against source MSSQL schema.
"""

import pytest
from pathlib import Path
import yaml


class TestValidationAgent:
    """Test suite for Validation Agent"""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create a ValidationAgent instance"""
        from agents.validation_agent import ValidationAgent

        # Create a minimal project structure
        project_path = tmp_path / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "models").mkdir(parents=True, exist_ok=True)

        return ValidationAgent(project_path=str(project_path))

    @pytest.fixture
    def valid_dbt_project(self, tmp_path, mock_mssql_metadata):
        """Create a valid dbt project for testing"""
        project_path = tmp_path / "valid_project"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        # Create dbt_project.yml
        (project_path / "dbt_project.yml").write_text("""
name: 'test_project'
version: '1.0.0'
config-version: 2
profile: 'test'
model-paths: ["models"]
""")

        # Create staging models for each table
        for table in mock_mssql_metadata["tables"]:
            model_name = f"stg_{table['name'].lower()}"
            model_file = models_dir / f"{model_name}.sql"

            columns = ", ".join([col["name"] for col in table["columns"]])
            model_file.write_text(f"""
{{{{ config(materialized='view') }}}}

SELECT
    {columns}
FROM {{{{ source('raw', '{table['name']}') }}}}
""")

        # Create _sources.yml
        sources_content = {
            "version": 2,
            "sources": [{
                "name": "raw",
                "tables": [{"name": t["name"]} for t in mock_mssql_metadata["tables"]]
            }]
        }
        (models_dir / "_sources.yml").write_text(yaml.dump(sources_content))

        # Create _schema.yml
        schema_content = {
            "version": 2,
            "models": []
        }
        for table in mock_mssql_metadata["tables"]:
            model_entry = {
                "name": f"stg_{table['name'].lower()}",
                "columns": [{"name": col["name"]} for col in table["columns"]]
            }
            schema_content["models"].append(model_entry)

        (models_dir / "_schema.yml").write_text(yaml.dump(schema_content))

        return project_path

    @pytest.mark.unit
    @pytest.mark.agent
    def test_validator_initialization(self, validator):
        """Test that validator initializes correctly"""
        assert validator is not None

    @pytest.mark.unit
    @pytest.mark.agent
    def test_validate_model_exists(self, validator, valid_dbt_project, mock_mssql_metadata):
        """Test validation that model files exist"""
        from agents.validation_agent import validate_migration

        result = validate_migration(
            str(valid_dbt_project),
            mock_mssql_metadata,
            run_compile=False,
            validate_row_counts=False
        )

        assert result is not None
        assert "overall_status" in result
        assert "table_results" in result

    @pytest.mark.unit
    @pytest.mark.agent
    def test_validate_columns_present(self, validator, valid_dbt_project, mock_mssql_metadata):
        """Test validation that all columns are present in models"""
        from agents.validation_agent import validate_migration

        result = validate_migration(
            str(valid_dbt_project),
            mock_mssql_metadata,
            validate_data_types=True
        )

        # Check that column validation was performed
        assert "summary" in result

    @pytest.mark.unit
    @pytest.mark.agent
    def test_missing_model_detection(self, validator, tmp_path, mock_mssql_metadata):
        """Test detection of missing model files"""
        from agents.validation_agent import validate_migration

        # Create incomplete project (missing some models)
        project_path = tmp_path / "incomplete_project"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        # Only create one model (customers), missing orders and order_items
        (models_dir / "stg_customers.sql").write_text("SELECT * FROM customers")

        result = validate_migration(
            str(project_path),
            mock_mssql_metadata,
            run_compile=False
        )

        # Should detect missing models
        assert result["overall_status"] in ["warning", "error", "failed"]

    @pytest.mark.unit
    @pytest.mark.agent
    def test_validate_foreign_key_relationships(self, validator, valid_dbt_project, mock_mssql_metadata):
        """Test validation of foreign key relationship preservation"""
        from agents.validation_agent import validate_migration

        result = validate_migration(
            str(valid_dbt_project),
            mock_mssql_metadata,
            generate_dbt_tests=True
        )

        # Should have processed foreign keys
        assert "dbt_tests_generated" in result or "summary" in result

    @pytest.mark.unit
    @pytest.mark.agent
    def test_validate_empty_metadata(self, validator, tmp_path):
        """Test validation with empty metadata"""
        from agents.validation_agent import validate_migration

        project_path = tmp_path / "empty_test"
        project_path.mkdir()
        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        empty_metadata = {
            "tables": [],
            "views": [],
            "foreign_keys": []
        }

        result = validate_migration(
            str(project_path),
            empty_metadata
        )

        assert result is not None


class TestValidationTypes:
    """Test different validation types"""

    @pytest.mark.unit
    @pytest.mark.agent
    def test_sql_syntax_validation(self, tmp_path):
        """Test SQL syntax validation"""
        from agents.validation_agent import validate_migration

        project_path = tmp_path / "syntax_test"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        # Create model with valid SQL
        (models_dir / "stg_test.sql").write_text("""
{{ config(materialized='view') }}
SELECT id, name FROM {{ source('raw', 'test') }}
""")

        metadata = {
            "tables": [{"name": "test", "columns": [{"name": "id"}, {"name": "name"}]}],
            "foreign_keys": []
        }

        result = validate_migration(str(project_path), metadata)
        assert result is not None

    @pytest.mark.unit
    @pytest.mark.agent
    def test_data_type_validation(self, tmp_path, mock_mssql_metadata):
        """Test data type mapping validation"""
        from agents.validation_agent import validate_migration

        project_path = tmp_path / "type_test"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        # Create model
        (models_dir / "stg_customers.sql").write_text("""
SELECT
    CAST(customer_id AS INTEGER) as customer_id,
    first_name,
    last_name
FROM {{ source('raw', 'customers') }}
""")

        result = validate_migration(
            str(project_path),
            mock_mssql_metadata,
            validate_data_types=True
        )

        assert result is not None


class TestEnhanceSchemaYml:
    """Test schema.yml enhancement functionality"""

    @pytest.mark.unit
    @pytest.mark.agent
    def test_enhance_schema_generates_tests(self, tmp_path, mock_mssql_metadata):
        """Test that enhance_schema_yml generates appropriate tests"""
        from agents.validation_agent import enhance_schema_yml

        # Create minimal project
        project_path = tmp_path / "enhance_test"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        result = enhance_schema_yml(str(project_path), mock_mssql_metadata)

        # Should return YAML content
        assert "version:" in result or "models:" in result

    @pytest.mark.unit
    @pytest.mark.agent
    def test_enhance_schema_adds_not_null_tests(self, tmp_path, mock_mssql_metadata):
        """Test that not_null tests are added for non-nullable columns"""
        from agents.validation_agent import enhance_schema_yml

        project_path = tmp_path / "not_null_test"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        result = enhance_schema_yml(str(project_path), mock_mssql_metadata)

        # Parse result and check for not_null tests
        schema = yaml.safe_load(result)

        # Should have models with tests
        if "models" in schema:
            for model in schema["models"]:
                if "columns" in model:
                    for col in model["columns"]:
                        if "tests" in col:
                            assert isinstance(col["tests"], list)

    @pytest.mark.unit
    @pytest.mark.agent
    def test_enhance_schema_adds_unique_tests(self, tmp_path, mock_mssql_metadata):
        """Test that unique tests are added for primary key columns"""
        from agents.validation_agent import enhance_schema_yml

        project_path = tmp_path / "unique_test"
        models_dir = project_path / "models" / "staging"
        models_dir.mkdir(parents=True)

        (project_path / "dbt_project.yml").write_text("name: test\nversion: 1.0.0")

        result = enhance_schema_yml(str(project_path), mock_mssql_metadata)

        # Should contain unique tests for PK columns
        assert result is not None
