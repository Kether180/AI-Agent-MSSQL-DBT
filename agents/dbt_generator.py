"""
dbt Project Generator

Generates complete dbt project structure including:
- dbt_project.yml
- profiles.yml
- sources.yml
- models/*.sql
- schema.yml files

This creates real, runnable dbt projects from the AI-generated models.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DBTProjectGenerator:
    """
    Generates a complete dbt project structure.

    Usage:
        generator = DBTProjectGenerator(
            project_name="my_migration",
            output_path="./dbt_projects/my_migration"
        )
        generator.generate_full_project(metadata, models)
    """

    def __init__(
        self,
        project_name: str,
        output_path: str,
        target_warehouse: str = "snowflake",
        source_name: str = "mssql_source"
    ):
        """
        Initialize the dbt project generator.

        Args:
            project_name: Name of the dbt project
            output_path: Directory to create the project in
            target_warehouse: Target data warehouse (snowflake, databricks, bigquery)
            source_name: Name for the source in sources.yml
        """
        self.project_name = self._sanitize_name(project_name)
        self.output_path = Path(output_path)
        self.target_warehouse = target_warehouse
        self.source_name = source_name

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name to be valid dbt identifier"""
        # Replace spaces and special chars with underscores
        sanitized = name.lower().replace(" ", "_").replace("-", "_")
        # Remove any remaining non-alphanumeric chars except underscore
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        # Ensure doesn't start with number
        if sanitized and sanitized[0].isdigit():
            sanitized = "prj_" + sanitized
        return sanitized or "dbt_project"

    # =========================================================================
    # PROJECT STRUCTURE CREATION
    # =========================================================================

    def create_project_structure(self) -> None:
        """Create the basic dbt project directory structure"""
        directories = [
            self.output_path,
            self.output_path / "models",
            self.output_path / "models" / "staging",
            self.output_path / "models" / "intermediate",
            self.output_path / "models" / "marts",
            self.output_path / "seeds",
            self.output_path / "snapshots",
            self.output_path / "tests",
            self.output_path / "macros",
            self.output_path / "analyses",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")

        logger.info(f"Project structure created at: {self.output_path}")

    # =========================================================================
    # dbt_project.yml GENERATION
    # =========================================================================

    def generate_dbt_project_yml(
        self,
        version: str = "1.0.0",
        profile_name: Optional[str] = None
    ) -> str:
        """
        Generate the dbt_project.yml file.

        Returns:
            Path to the generated file
        """
        profile = profile_name or self.project_name

        project_config = {
            'name': self.project_name,
            'version': version,
            'config-version': 2,
            'profile': profile,

            'model-paths': ["models"],
            'analysis-paths': ["analyses"],
            'test-paths': ["tests"],
            'seed-paths': ["seeds"],
            'macro-paths': ["macros"],
            'snapshot-paths': ["snapshots"],

            'clean-targets': ["target", "dbt_packages"],

            'models': {
                self.project_name: {
                    'staging': {
                        '+materialized': 'view',
                        '+schema': 'staging'
                    },
                    'intermediate': {
                        '+materialized': 'view',
                        '+schema': 'intermediate'
                    },
                    'marts': {
                        '+materialized': 'table',
                        '+schema': 'marts'
                    }
                }
            }
        }

        file_path = self.output_path / "dbt_project.yml"
        with open(file_path, 'w') as f:
            yaml.dump(project_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generated dbt_project.yml at: {file_path}")
        return str(file_path)

    # =========================================================================
    # profiles.yml GENERATION
    # =========================================================================

    def generate_profiles_yml(
        self,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate a sample profiles.yml file.

        Note: In production, profiles.yml typically goes in ~/.dbt/
        This generates a template for users to customize.

        Args:
            output_dir: Directory to output (defaults to project root)

        Returns:
            Path to the generated file
        """
        out_path = Path(output_dir) if output_dir else self.output_path

        if self.target_warehouse == "snowflake":
            profile_config = {
                self.project_name: {
                    'target': 'dev',
                    'outputs': {
                        'dev': {
                            'type': 'snowflake',
                            'account': '{{ env_var("SNOWFLAKE_ACCOUNT") }}',
                            'user': '{{ env_var("SNOWFLAKE_USER") }}',
                            'password': '{{ env_var("SNOWFLAKE_PASSWORD") }}',
                            'role': '{{ env_var("SNOWFLAKE_ROLE", "TRANSFORMER") }}',
                            'database': '{{ env_var("SNOWFLAKE_DATABASE") }}',
                            'warehouse': '{{ env_var("SNOWFLAKE_WAREHOUSE") }}',
                            'schema': 'public',
                            'threads': 4
                        },
                        'prod': {
                            'type': 'snowflake',
                            'account': '{{ env_var("SNOWFLAKE_ACCOUNT") }}',
                            'user': '{{ env_var("SNOWFLAKE_USER") }}',
                            'password': '{{ env_var("SNOWFLAKE_PASSWORD") }}',
                            'role': '{{ env_var("SNOWFLAKE_ROLE", "TRANSFORMER") }}',
                            'database': '{{ env_var("SNOWFLAKE_DATABASE") }}',
                            'warehouse': '{{ env_var("SNOWFLAKE_WAREHOUSE") }}',
                            'schema': 'public',
                            'threads': 8
                        }
                    }
                }
            }
        elif self.target_warehouse == "databricks":
            profile_config = {
                self.project_name: {
                    'target': 'dev',
                    'outputs': {
                        'dev': {
                            'type': 'databricks',
                            'host': '{{ env_var("DATABRICKS_HOST") }}',
                            'http_path': '{{ env_var("DATABRICKS_HTTP_PATH") }}',
                            'token': '{{ env_var("DATABRICKS_TOKEN") }}',
                            'schema': 'default',
                            'threads': 4
                        }
                    }
                }
            }
        elif self.target_warehouse == "bigquery":
            profile_config = {
                self.project_name: {
                    'target': 'dev',
                    'outputs': {
                        'dev': {
                            'type': 'bigquery',
                            'method': 'service-account',
                            'project': '{{ env_var("GCP_PROJECT") }}',
                            'dataset': 'dbt_dev',
                            'keyfile': '{{ env_var("GCP_KEYFILE") }}',
                            'threads': 4,
                            'location': 'US'
                        }
                    }
                }
            }
        else:
            # Generic/PostgreSQL fallback
            profile_config = {
                self.project_name: {
                    'target': 'dev',
                    'outputs': {
                        'dev': {
                            'type': 'postgres',
                            'host': '{{ env_var("DB_HOST", "localhost") }}',
                            'port': 5432,
                            'user': '{{ env_var("DB_USER") }}',
                            'password': '{{ env_var("DB_PASSWORD") }}',
                            'dbname': '{{ env_var("DB_NAME") }}',
                            'schema': 'public',
                            'threads': 4
                        }
                    }
                }
            }

        file_path = out_path / "profiles.yml"
        with open(file_path, 'w') as f:
            # Add comment header
            f.write("# dbt Profile Configuration\n")
            f.write("# Copy this to ~/.dbt/profiles.yml and update with your credentials\n")
            f.write(f"# Generated by DataMigrate AI on {datetime.now().strftime('%Y-%m-%d')}\n\n")
            yaml.dump(profile_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generated profiles.yml at: {file_path}")
        return str(file_path)

    # =========================================================================
    # sources.yml GENERATION
    # =========================================================================

    def generate_sources_yml(
        self,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate the sources.yml file from MSSQL metadata.

        Args:
            metadata: Extracted MSSQL metadata

        Returns:
            Path to the generated file
        """
        database_name = metadata.get('database', 'mssql_database')

        # Build tables list for sources
        source_tables = []
        for table in metadata.get('tables', []):
            table_config = {
                'name': table.get('name'),
                'description': table.get('description') or f"Source table: {table.get('name')}"
            }

            # Add column definitions if available
            if table.get('columns'):
                table_config['columns'] = [
                    {
                        'name': col.get('name'),
                        'description': col.get('description') or f"Column {col.get('name')} ({col.get('data_type', 'unknown')})"
                    }
                    for col in table.get('columns', [])[:50]  # Limit columns
                ]

            source_tables.append(table_config)

        sources_config = {
            'version': 2,
            'sources': [
                {
                    'name': self.source_name,
                    'description': f"MSSQL source database: {database_name}",
                    'database': '{{ env_var("SOURCE_DATABASE", "raw") }}',
                    'schema': '{{ env_var("SOURCE_SCHEMA", "mssql") }}',
                    'tables': source_tables
                }
            ]
        }

        file_path = self.output_path / "models" / "staging" / "_sources.yml"
        with open(file_path, 'w') as f:
            yaml.dump(sources_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generated sources.yml at: {file_path}")
        return str(file_path)

    # =========================================================================
    # MODEL SQL FILE GENERATION
    # =========================================================================

    def generate_model_file(
        self,
        model_name: str,
        sql_content: str,
        model_type: str = "staging"
    ) -> str:
        """
        Generate a single model SQL file.

        Args:
            model_name: Name of the model (without .sql extension)
            sql_content: SQL content for the model
            model_type: Type of model (staging, intermediate, marts)

        Returns:
            Path to the generated file
        """
        # Determine subdirectory based on model type
        if model_type == "staging":
            model_dir = self.output_path / "models" / "staging"
        elif model_type == "intermediate":
            model_dir = self.output_path / "models" / "intermediate"
        elif model_type in ("marts", "fact", "dimension"):
            model_dir = self.output_path / "models" / "marts"
        else:
            model_dir = self.output_path / "models"

        model_dir.mkdir(parents=True, exist_ok=True)

        file_path = model_dir / f"{model_name}.sql"
        with open(file_path, 'w') as f:
            f.write(sql_content)

        logger.debug(f"Generated model: {file_path}")
        return str(file_path)

    def generate_staging_model(
        self,
        table_name: str,
        schema_name: str = "dbo",
        columns: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a staging model SQL file for a source table.

        Args:
            table_name: Source table name
            schema_name: Source schema name
            columns: Optional list of column definitions

        Returns:
            SQL content for the staging model
        """
        model_name = f"stg_{table_name.lower()}"

        # Build column list
        if columns:
            column_sql = ",\n    ".join([
                f"{col.get('name')}"
                for col in columns
            ])
        else:
            column_sql = "*"

        sql_content = f"""-- Staging model for {schema_name}.{table_name}
-- Generated by DataMigrate AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{{{{ config(
    materialized='view',
    schema='staging'
) }}}}

WITH source AS (

    SELECT
        {column_sql}
    FROM {{{{ source('{self.source_name}', '{table_name}') }}}}

),

staged AS (

    SELECT
        {column_sql}
    FROM source

)

SELECT * FROM staged
"""

        # Save the file
        self.generate_model_file(model_name, sql_content, "staging")

        return sql_content

    # =========================================================================
    # SCHEMA.YML GENERATION
    # =========================================================================

    def generate_schema_yml(
        self,
        models: List[Dict[str, Any]],
        model_type: str = "staging"
    ) -> str:
        """
        Generate schema.yml for a set of models.

        Args:
            models: List of model configurations
            model_type: Type of models (staging, intermediate, marts)

        Returns:
            Path to the generated file
        """
        model_configs = []

        for model in models:
            model_config = {
                'name': model.get('name'),
                'description': model.get('description', f"Model: {model.get('name')}")
            }

            # Add column definitions if available
            if model.get('columns'):
                model_config['columns'] = [
                    {
                        'name': col.get('name'),
                        'description': col.get('description', '')
                    }
                    for col in model.get('columns', [])
                ]

            model_configs.append(model_config)

        schema_config = {
            'version': 2,
            'models': model_configs
        }

        # Determine path based on model type
        if model_type == "staging":
            file_path = self.output_path / "models" / "staging" / "_schema.yml"
        elif model_type == "intermediate":
            file_path = self.output_path / "models" / "intermediate" / "_schema.yml"
        else:
            file_path = self.output_path / "models" / "marts" / "_schema.yml"

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            yaml.dump(schema_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Generated schema.yml at: {file_path}")
        return str(file_path)

    # =========================================================================
    # FULL PROJECT GENERATION
    # =========================================================================

    def generate_full_project(
        self,
        metadata: Dict[str, Any],
        models: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete dbt project from metadata and models.

        Args:
            metadata: Extracted MSSQL metadata
            models: Optional list of model configurations from AI

        Returns:
            Dictionary with paths to all generated files
        """
        logger.info(f"Generating full dbt project: {self.project_name}")

        generated_files = {
            'project_path': str(self.output_path),
            'files': []
        }

        # 1. Create directory structure
        self.create_project_structure()

        # 2. Generate dbt_project.yml
        dbt_project_path = self.generate_dbt_project_yml()
        generated_files['files'].append(dbt_project_path)

        # 3. Generate profiles.yml
        profiles_path = self.generate_profiles_yml()
        generated_files['files'].append(profiles_path)

        # 4. Generate sources.yml
        sources_path = self.generate_sources_yml(metadata)
        generated_files['files'].append(sources_path)

        # 5. Generate staging models for each table
        staging_models = []
        for table in metadata.get('tables', []):
            self.generate_staging_model(
                table_name=table.get('name'),
                schema_name=table.get('schema', 'dbo'),
                columns=table.get('columns')
            )
            staging_models.append({
                'name': f"stg_{table.get('name', '').lower()}",
                'description': table.get('description') or f"Staging model for {table.get('name')}"
            })

        # 6. Generate schema.yml for staging models
        if staging_models:
            schema_path = self.generate_schema_yml(staging_models, "staging")
            generated_files['files'].append(schema_path)

        # 7. If custom models provided from AI, generate those too
        if models:
            for model in models:
                if model.get('file_path') and os.path.exists(model.get('file_path')):
                    # Model already generated by AI, just track it
                    generated_files['files'].append(model.get('file_path'))

        # 8. Generate README
        readme_content = f"""# {self.project_name}

dbt project generated by DataMigrate AI on {datetime.now().strftime('%Y-%m-%d')}.

## Setup

1. Install dbt:
   ```bash
   pip install dbt-{self.target_warehouse}
   ```

2. Copy `profiles.yml` to `~/.dbt/profiles.yml` and update credentials

3. Run dbt:
   ```bash
   cd {self.project_name}
   dbt deps
   dbt run
   ```

## Models

- **staging/**: Raw source data transformations
- **intermediate/**: Business logic layers
- **marts/**: Final analytics-ready tables

## Source Database

- **Server**: {metadata.get('server', 'N/A')}
- **Database**: {metadata.get('database', 'N/A')}
- **Tables**: {metadata.get('summary', {}).get('total_tables', 0)}
- **Views**: {metadata.get('summary', {}).get('total_views', 0)}

## Generated by DataMigrate AI

https://datamigrate.ai
"""

        readme_path = self.output_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        generated_files['files'].append(str(readme_path))

        # Summary
        generated_files['summary'] = {
            'total_files': len(generated_files['files']),
            'staging_models': len(staging_models),
            'target_warehouse': self.target_warehouse
        }

        logger.info(f"Project generation complete: {generated_files['summary']}")

        return generated_files


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_dbt_project(
    project_name: str,
    output_path: str,
    metadata: Dict[str, Any],
    target_warehouse: str = "snowflake"
) -> Dict[str, Any]:
    """
    Convenience function to create a complete dbt project.

    Args:
        project_name: Name of the project
        output_path: Where to create the project
        metadata: MSSQL metadata dictionary
        target_warehouse: Target warehouse type

    Returns:
        Dictionary with generated file paths
    """
    generator = DBTProjectGenerator(
        project_name=project_name,
        output_path=output_path,
        target_warehouse=target_warehouse
    )

    return generator.generate_full_project(metadata)


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    # Example usage with mock metadata
    mock_metadata = {
        'database': 'TestDB',
        'server': 'localhost',
        'tables': [
            {
                'schema': 'dbo',
                'name': 'Customers',
                'columns': [
                    {'name': 'CustomerID', 'data_type': 'int'},
                    {'name': 'CustomerName', 'data_type': 'nvarchar'},
                    {'name': 'Email', 'data_type': 'nvarchar'}
                ]
            },
            {
                'schema': 'dbo',
                'name': 'Orders',
                'columns': [
                    {'name': 'OrderID', 'data_type': 'int'},
                    {'name': 'CustomerID', 'data_type': 'int'},
                    {'name': 'OrderDate', 'data_type': 'datetime'}
                ]
            }
        ],
        'views': [],
        'stored_procedures': [],
        'summary': {
            'total_tables': 2,
            'total_views': 0,
            'total_stored_procedures': 0
        }
    }

    result = create_dbt_project(
        project_name="demo_migration",
        output_path="./demo_dbt_project",
        metadata=mock_metadata,
        target_warehouse="snowflake"
    )

    print(f"Generated project at: {result['project_path']}")
    print(f"Total files: {result['summary']['total_files']}")
