"""
Pytest Configuration and Fixtures

Provides common fixtures for testing agents.
"""

import pytest
import os
import tempfile
from pathlib import Path
from typing import Dict, Any


# =============================================================================
# MOCK DATA FIXTURES
# =============================================================================

@pytest.fixture
def mock_mssql_metadata() -> Dict[str, Any]:
    """Mock MSSQL metadata for testing"""
    return {
        "database": "TestDB",
        "tables": [
            {
                "schema": "dbo",
                "name": "customers",
                "object_type": "USER_TABLE",
                "columns": [
                    {"name": "customer_id", "data_type": "INT", "is_nullable": False, "is_primary_key": True},
                    {"name": "first_name", "data_type": "VARCHAR(100)", "is_nullable": False, "is_primary_key": False},
                    {"name": "last_name", "data_type": "VARCHAR(100)", "is_nullable": False, "is_primary_key": False},
                    {"name": "email", "data_type": "VARCHAR(255)", "is_nullable": True, "is_primary_key": False},
                    {"name": "created_at", "data_type": "DATETIME", "is_nullable": False, "is_primary_key": False}
                ]
            },
            {
                "schema": "dbo",
                "name": "orders",
                "object_type": "USER_TABLE",
                "columns": [
                    {"name": "order_id", "data_type": "INT", "is_nullable": False, "is_primary_key": True},
                    {"name": "customer_id", "data_type": "INT", "is_nullable": False, "is_primary_key": False},
                    {"name": "order_date", "data_type": "DATE", "is_nullable": False, "is_primary_key": False},
                    {"name": "total_amount", "data_type": "DECIMAL(10,2)", "is_nullable": False, "is_primary_key": False},
                    {"name": "status", "data_type": "VARCHAR(50)", "is_nullable": False, "is_primary_key": False}
                ]
            },
            {
                "schema": "dbo",
                "name": "order_items",
                "object_type": "USER_TABLE",
                "columns": [
                    {"name": "item_id", "data_type": "INT", "is_nullable": False, "is_primary_key": True},
                    {"name": "order_id", "data_type": "INT", "is_nullable": False, "is_primary_key": False},
                    {"name": "product_name", "data_type": "VARCHAR(200)", "is_nullable": False, "is_primary_key": False},
                    {"name": "quantity", "data_type": "INT", "is_nullable": False, "is_primary_key": False},
                    {"name": "unit_price", "data_type": "DECIMAL(10,2)", "is_nullable": False, "is_primary_key": False}
                ]
            }
        ],
        "views": [
            {
                "schema": "dbo",
                "name": "vw_customer_orders",
                "definition": "SELECT c.*, o.order_id FROM customers c JOIN orders o ON c.customer_id = o.customer_id"
            }
        ],
        "foreign_keys": [
            {
                "name": "FK_orders_customers",
                "parent_schema": "dbo",
                "parent_table": "orders",
                "parent_column": "customer_id",
                "referenced_schema": "dbo",
                "referenced_table": "customers",
                "referenced_column": "customer_id"
            },
            {
                "name": "FK_order_items_orders",
                "parent_schema": "dbo",
                "parent_table": "order_items",
                "parent_column": "order_id",
                "referenced_schema": "dbo",
                "referenced_table": "orders",
                "referenced_column": "order_id"
            }
        ],
        "stored_procedures": [],
        "indexes": []
    }


@pytest.fixture
def mock_simple_metadata() -> Dict[str, Any]:
    """Minimal mock metadata for quick tests"""
    return {
        "database": "SimpleDB",
        "tables": [
            {
                "schema": "dbo",
                "name": "users",
                "columns": [
                    {"name": "id", "data_type": "INT", "is_nullable": False, "is_primary_key": True},
                    {"name": "name", "data_type": "VARCHAR(100)", "is_nullable": False, "is_primary_key": False}
                ]
            }
        ],
        "views": [],
        "foreign_keys": [],
        "stored_procedures": []
    }


@pytest.fixture
def temp_dbt_project(tmp_path) -> Path:
    """Create a temporary dbt project directory"""
    project_path = tmp_path / "dbt_project"
    project_path.mkdir()

    # Create basic project structure
    models_dir = project_path / "models" / "staging"
    models_dir.mkdir(parents=True)

    # Create dbt_project.yml
    dbt_project_yml = project_path / "dbt_project.yml"
    dbt_project_yml.write_text("""
name: 'test_project'
version: '1.0.0'
config-version: 2

profile: 'test_profile'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
""")

    return project_path


@pytest.fixture
def sample_stg_model_sql() -> str:
    """Sample staging model SQL"""
    return """
{{ config(materialized='view') }}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    created_at
FROM {{ source('raw', 'customers') }}
"""


# =============================================================================
# API TESTING FIXTURES
# =============================================================================

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    from fastapi.testclient import TestClient
    from agents.api import app

    return TestClient(app)


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("GO_BACKEND_URL", "http://localhost:8080")
    monkeypatch.setenv("AI_SERVICE_PORT", "8081")


@pytest.fixture
def no_api_keys(monkeypatch):
    """Remove API keys for testing fallback behavior"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
