"""
Unit Tests for API Endpoints

Tests the FastAPI endpoints for the AI service.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and status endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data

    @pytest.mark.unit
    def test_agents_health(self, client):
        """Test /agents/health endpoint"""
        response = client.get("/agents/health")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "overall_status" in data

    @pytest.mark.unit
    def test_agents_status(self, client):
        """Test /agents/status endpoint"""
        response = client.get("/agents/status")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

        # Check each agent has required fields
        for agent in data["agents"]:
            assert "name" in agent
            assert "status" in agent
            assert "completion" in agent


class TestMigrationEndpoints:
    """Test migration-related endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_migration_not_found(self, client):
        """Test getting status of non-existent migration"""
        response = client.get("/migrations/99999/status")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_migration_files_not_found(self, client):
        """Test getting files of non-existent migration"""
        response = client.get("/migrations/99999/files")
        assert response.status_code == 404


class TestChatEndpoint:
    """Test AI chat endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_chat_basic(self, client):
        """Test basic chat functionality"""
        response = client.post(
            "/chat",
            json={
                "message": "Hello, can you help me with migrations?",
                "language": "en"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

    @pytest.mark.unit
    def test_chat_migration_keyword(self, client):
        """Test chat with migration keywords"""
        response = client.post(
            "/chat",
            json={
                "message": "How do I create a new migration?",
                "language": "en"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "migration" in data["response"].lower() or "create" in data["response"].lower()

    @pytest.mark.unit
    def test_chat_multilingual_danish(self, client):
        """Test chat in Danish"""
        response = client.post(
            "/chat",
            json={
                "message": "Hvordan opretter jeg en migrering?",
                "language": "da"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]) > 0

    @pytest.mark.unit
    def test_chat_multilingual_german(self, client):
        """Test chat in German"""
        response = client.post(
            "/chat",
            json={
                "message": "Wie erstelle ich eine Migration?",
                "language": "de"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["response"]) > 0

    @pytest.mark.unit
    def test_chat_security_keywords(self, client):
        """Test chat responds to security questions"""
        response = client.post(
            "/chat",
            json={
                "message": "Is my data secure? What encryption do you use?",
                "language": "en"
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should mention security-related terms
        response_lower = data["response"].lower()
        assert any(term in response_lower for term in ["encrypt", "secure", "protect", "tls", "aes"])


class TestDataQualityEndpoint:
    """Test data quality scanning endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_data_quality_scan_invalid_connection(self, client):
        """Test data quality scan with invalid connection"""
        response = client.post(
            "/data-quality/scan",
            json={
                "host": "invalid-host",
                "port": 1433,
                "database": "TestDB",
                "username": "test",
                "password": "test"
            }
        )

        # Should fail to connect
        assert response.status_code in [500, 400]


class TestValidationEndpoint:
    """Test migration validation endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_validate_nonexistent_migration(self, client):
        """Test validation of non-existent migration"""
        response = client.post("/migrations/99999/validate")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_enhance_schema_nonexistent(self, client):
        """Test schema enhancement for non-existent migration"""
        response = client.post("/migrations/99999/enhance-schema")
        assert response.status_code == 404


class TestDeploymentEndpoints:
    """Test deployment-related endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    def test_deploy_nonexistent_migration(self, client):
        """Test deployment of non-existent migration"""
        response = client.post(
            "/migrations/99999/deploy",
            json={
                "connection": {
                    "warehouse_type": "snowflake",
                    "account": "test",
                    "warehouse": "test_wh",
                    "database": "test_db"
                },
                "run_tests": False
            }
        )

        assert response.status_code == 404

    @pytest.mark.unit
    def test_get_deployment_not_found(self, client):
        """Test getting non-existent deployment"""
        response = client.get("/migrations/1/deployments/99999")
        assert response.status_code == 404

    @pytest.mark.unit
    def test_list_deployments(self, client):
        """Test listing deployments for a migration"""
        response = client.get("/migrations/1/deployments")

        assert response.status_code == 200
        data = response.json()
        assert "migration_id" in data
        assert "deployments" in data
