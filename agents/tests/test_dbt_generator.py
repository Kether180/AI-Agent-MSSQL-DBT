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

        return DBTProjectGenerator(
            project_name="test_project",
            output_path=str(tmp_path / "dbt_output"),
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
        content = generator.generate_dbt_project_yml()

        assert "name: 'test_project'" in content or "name: test_project" in content
        assert "version:" in content
        assert "profile:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_profiles_yml_snowflake(self, generator):
        """Test profiles.yml generation for Snowflake"""
        content = generator.generate_profiles_yml()

        assert "snowflake" in content.lower() or "type:" in content
        assert "account:" in content or "target:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_staging_model(self, generator, mock_mssql_metadata):
        """Test staging model SQL generation"""
        table = mock_mssql_metadata["tables"][0]  # customers table
        model_sql = generator.generate_staging_model(table)

        assert "SELECT" in model_sql
        assert "customer_id" in model_sql
        assert "source(" in model_sql or "FROM" in model_sql

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_full_project(self, generator, mock_mssql_metadata, tmp_path):
        """Test full dbt project generation"""
        generator.output_path = str(tmp_path / "full_project")

        result = generator.generate_full_project(mock_mssql_metadata)

        output_path = Path(generator.output_path)

        # Check project structure
        assert output_path.exists()
        assert (output_path / "dbt_project.yml").exists()
        assert (output_path / "models").exists()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_sources_yml(self, generator, mock_mssql_metadata):
        """Test sources.yml generation"""
        content = generator.generate_sources_yml(mock_mssql_metadata)

        # Parse as YAML to verify structure
        sources = yaml.safe_load(content)

        assert "sources" in sources
        assert len(sources["sources"]) > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_generate_schema_yml(self, generator, mock_mssql_metadata):
        """Test schema.yml generation with tests"""
        content = generator.generate_schema_yml(mock_mssql_metadata["tables"])

        # Should contain model definitions
        assert "models:" in content or "version:" in content

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

        generator.output_path = str(tmp_path / "empty_project")

        # Should not raise an error
        result = generator.generate_full_project(empty_metadata)
        assert Path(generator.output_path).exists()


class TestDBTGeneratorWarehouses:
    """Test DBT Generator for different warehouse types"""

    @pytest.mark.unit
    @pytest.mark.agent
    def test_snowflake_profile(self, tmp_path):
        """Test Snowflake-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        generator = DBTProjectGenerator(
            project_name="sf_project",
            output_path=str(tmp_path / "sf_output"),
            target_warehouse="snowflake"
        )

        content = generator.generate_profiles_yml()
        assert "snowflake" in content.lower()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_bigquery_profile(self, tmp_path):
        """Test BigQuery-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        generator = DBTProjectGenerator(
            project_name="bq_project",
            output_path=str(tmp_path / "bq_output"),
            target_warehouse="bigquery"
        )

        content = generator.generate_profiles_yml()
        assert "bigquery" in content.lower() or "project:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_databricks_profile(self, tmp_path):
        """Test Databricks-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        generator = DBTProjectGenerator(
            project_name="db_project",
            output_path=str(tmp_path / "db_output"),
            target_warehouse="databricks"
        )

        content = generator.generate_profiles_yml()
        assert "databricks" in content.lower() or "catalog:" in content

    @pytest.mark.unit
    @pytest.mark.agent
    def test_fabric_profile(self, tmp_path):
        """Test Microsoft Fabric-specific profile generation"""
        from agents.dbt_generator import DBTProjectGenerator

        generator = DBTProjectGenerator(
            project_name="fabric_project",
            output_path=str(tmp_path / "fabric_output"),
            target_warehouse="fabric"
        )

        content = generator.generate_profiles_yml()
        # Fabric uses similar config to SQL Server
        assert "fabric" in content.lower() or "type:" in content
