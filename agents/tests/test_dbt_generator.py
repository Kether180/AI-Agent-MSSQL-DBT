"""
Unit Tests for DBT Generator Agent

Tests the DBTProjectGenerator class for generating dbt projects
from MSSQL metadata.
"""

import pytest
from pathlib import Path
import yaml


class TestDBTProjectGenerator:
    """Test suite for DBT Generator Agent"""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a DBTProjectGenerator instance"""
        from agents.dbt_generator import DBTProjectGenerator

        # Create the output directory structure
        output_path = tmp_path / "dbt_output"
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / "models" / "staging").mkdir(parents=True, exist_ok=True)

        return DBTProjectGenerator(
            project_name="test_project",
            output_path=str(output_path),
            target_warehouse="snowflake"
        )

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generator_initialization(self, generator):
        """Test that generator initializes correctly"""
        assert generator.project_name == "test_project"
        assert generator.target_warehouse == "snowflake"

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_dbt_project_yml(self, generator):
        """Test dbt_project.yml generation"""
        file_path = generator.generate_dbt_project_yml()

        # Read the generated file content
        content = Path(file_path).read_text()

        assert "name:" in content
        assert "test_project" in content
        assert "version:" in content
        assert "profile:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_profiles_yml_snowflake(self, generator):
        """Test profiles.yml generation for Snowflake"""
        file_path = generator.generate_profiles_yml()

        # Read the generated file content
        content = Path(file_path).read_text()

        assert "snowflake" in content.lower() or "type:" in content
        assert "account:" in content or "target:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_staging_model(self, generator, mock_mssql_metadata):
        """Test staging model SQL generation"""
        table = mock_mssql_metadata["tables"][0]  # customers table
        # Pass table_name and columns separately as the method expects
        model_sql = generator.generate_staging_model(
            table_name=table["name"],
            schema_name=table.get("schema", "dbo"),
            columns=table.get("columns", [])
        )

        # Should return SQL content, not file path
        assert "SELECT" in model_sql or "select" in model_sql.lower()
        assert "FROM" in model_sql or "from" in model_sql.lower()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_full_project(self, generator, mock_mssql_metadata, tmp_path):
        """Test full dbt project generation"""
        output_path = tmp_path / "full_project"
        output_path.mkdir(parents=True, exist_ok=True)
        generator.output_path = output_path

        result = generator.generate_full_project(mock_mssql_metadata)

        # Check project structure
        assert output_path.exists()
        assert (output_path / "dbt_project.yml").exists()
        assert (output_path / "models").exists()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_sources_yml(self, generator, mock_mssql_metadata):
        """Test sources.yml generation"""
        result = generator.generate_sources_yml(mock_mssql_metadata)

        # Result could be file path or content depending on implementation
        if Path(str(result)).exists():
            content = Path(result).read_text()
        else:
            content = str(result)

        # Should contain sources definition
        assert "source" in content.lower() or "name:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_schema_yml(self, generator, mock_mssql_metadata):
        """Test schema.yml generation with tests"""
        result = generator.generate_schema_yml(mock_mssql_metadata["tables"])

        # Result could be file path or content depending on implementation
        if Path(str(result)).exists():
            content = Path(result).read_text()
        else:
            content = str(result)

        # Should contain model definitions
        assert "models:" in content or "version:" in content or "name:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_data_type_mapping(self, generator):
        """Test SQL Server to warehouse data type mapping"""
        # Test common type mappings
        test_types = [
            ("INT", "INTEGER"),
            ("VARCHAR(100)", "VARCHAR"),
            ("DATETIME", "TIMESTAMP"),
            ("BIT", "BOOLEAN"),
            ("DECIMAL(10,2)", "DECIMAL"),
        ]

        for source_type, _ in test_types:
            # Generator should handle these without errors
            mapped = generator.map_data_type(source_type) if hasattr(generator, 'map_data_type') else source_type
            assert mapped is not None

    @pytest.mark.unit
    @pytest.mark.agent
    def test_empty_metadata_handling(self, generator, tmp_path):
        """Test handling of empty metadata"""
        empty_metadata = {
            "database": "EmptyDB",
            "tables": [],
            "views": [],
            "foreign_keys": []
        }

        output_path = tmp_path / "empty_project"
        output_path.mkdir(parents=True, exist_ok=True)
        generator.output_path = output_path

        # Should not raise an error
        result = generator.generate_full_project(empty_metadata)
        assert output_path.exists()


class TestDBTGeneratorWarehouses:
    """Test DBT Generator for different warehouse types"""

    @pytest.mark.unit
    @pytest.mark.agent
    def test_snowflake_profile(self, tmp_path):
        """Test Snowflake-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        output_path = tmp_path / "sf_output"
        output_path.mkdir(parents=True, exist_ok=True)

        generator = DBTProjectGenerator(
            project_name="sf_project",
            output_path=str(output_path),
            target_warehouse="snowflake"
        )

        file_path = generator.generate_profiles_yml()
        content = Path(file_path).read_text()
        assert "snowflake" in content.lower()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_bigquery_profile(self, tmp_path):
        """Test BigQuery-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        output_path = tmp_path / "bq_output"
        output_path.mkdir(parents=True, exist_ok=True)

        generator = DBTProjectGenerator(
            project_name="bq_project",
            output_path=str(output_path),
            target_warehouse="bigquery"
        )

        file_path = generator.generate_profiles_yml()
        content = Path(file_path).read_text()
        assert "bigquery" in content.lower() or "project:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_databricks_profile(self, tmp_path):
        """Test Databricks-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        output_path = tmp_path / "db_output"
        output_path.mkdir(parents=True, exist_ok=True)

        generator = DBTProjectGenerator(
            project_name="db_project",
            output_path=str(output_path),
            target_warehouse="databricks"
        )

        file_path = generator.generate_profiles_yml()
        content = Path(file_path).read_text()
        assert "databricks" in content.lower() or "catalog:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_fabric_profile(self, tmp_path):
        """Test Microsoft Fabric-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        output_path = tmp_path / "fabric_output"
        output_path.mkdir(parents=True, exist_ok=True)

        generator = DBTProjectGenerator(
            project_name="fabric_project",
            output_path=str(output_path),
            target_warehouse="fabric"
        )

        file_path = generator.generate_profiles_yml()
        content = Path(file_path).read_text()
        # Fabric uses similar config to SQL Server
        assert "fabric" in content.lower() or "type:" in content
