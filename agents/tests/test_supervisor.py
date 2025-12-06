"""
Unit Tests for Manager Coordination Supervisor

Tests the supervisor routing logic based on the Manager Coordination
pattern from "Building Applications with AI Agents" (O'Reilly, 2025).
"""

import pytest
from fastapi.testclient import TestClient


class TestSupervisorRouting:
    """Test supervisor query routing"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.fixture
    def supervisor(self):
        """Create supervisor instance"""
        from agents.supervisor import ManagerCoordinationSupervisor
        return ManagerCoordinationSupervisor()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_supervisor_initialization(self, supervisor):
        """Test that supervisor initializes correctly"""
        assert supervisor is not None
        assert supervisor.default_agent is not None
        assert len(supervisor.ROUTING_PATTERNS) > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_extraction_query(self, supervisor):
        """Test routing of extraction queries"""
        decision = supervisor.route_request("Extract schema from my MSSQL database")

        assert decision.primary_agent.value == "mssql_extractor"
        assert decision.category.value == "data_extraction"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_generation_query(self, supervisor):
        """Test routing of dbt generation queries"""
        decision = supervisor.route_request("Generate a dbt staging model for customers")

        assert decision.primary_agent.value == "dbt_generator"
        assert decision.category.value == "generation"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_execution_query(self, supervisor):
        """Test routing of dbt execution queries"""
        decision = supervisor.route_request("Run dbt build on my project")

        assert decision.primary_agent.value == "dbt_executor"
        assert decision.category.value == "generation"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_validation_query(self, supervisor):
        """Test routing of validation queries"""
        decision = supervisor.route_request("Validate my migration results")

        assert decision.primary_agent.value == "validation_agent"
        assert decision.category.value == "quality"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_data_quality_query(self, supervisor):
        """Test routing of data quality queries"""
        decision = supervisor.route_request("Check for null values and data quality")

        assert decision.primary_agent.value == "data_quality_agent"
        assert decision.category.value == "quality"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_security_query(self, supervisor):
        """Test routing of security queries"""
        decision = supervisor.route_request("Perform a security audit of the system")

        assert decision.primary_agent.value == "guardian_agent"
        assert decision.category.value == "security"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_help_query(self, supervisor):
        """Test routing of help/support queries"""
        decision = supervisor.route_request("Help me understand how dbt works")

        assert decision.primary_agent.value == "rag_service"
        assert decision.category.value == "support"
        assert decision.confidence > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_unknown_query_fallback(self, supervisor):
        """Test fallback routing for unrecognized queries"""
        decision = supervisor.route_request("random gibberish xyz123")

        # Should fallback to RAG service
        assert decision.primary_agent.value == "rag_service"
        assert decision.category.value == "support"

    @pytest.mark.unit
    @pytest.mark.agent
    def test_workflow_chain_full_migration(self, supervisor):
        """Test full migration workflow chain trigger"""
        decision = supervisor.route_request("Start a full migration of my database")

        assert decision.requires_chain is True
        assert len(decision.chain_order) > 0
        assert decision.chain_order[0].value == "mssql_extractor"

    @pytest.mark.unit
    @pytest.mark.agent
    def test_workflow_chain_secure_migration(self, supervisor):
        """Test secure migration workflow chain trigger"""
        decision = supervisor.route_request("Perform a secure migration with security checks")

        assert decision.requires_chain is True
        assert decision.chain_order[0].value == "guardian_agent"

    @pytest.mark.unit
    @pytest.mark.agent
    def test_metrics_tracking(self, supervisor):
        """Test that routing metrics are tracked"""
        # Reset metrics first
        supervisor.reset_metrics()

        # Make some routing decisions
        supervisor.route_request("Extract schema")
        supervisor.route_request("Generate dbt model")
        supervisor.route_request("Validate migration")

        metrics = supervisor.get_metrics()

        assert metrics["total_requests"] == 3
        assert len(metrics["routing_decisions"]) > 0

    @pytest.mark.unit
    @pytest.mark.agent
    def test_metrics_reset(self, supervisor):
        """Test that metrics can be reset"""
        # Make some requests
        supervisor.route_request("Test query")

        # Reset metrics
        supervisor.reset_metrics()

        metrics = supervisor.get_metrics()
        assert metrics["total_requests"] == 0


class TestSupervisorEndpoints:
    """Test supervisor API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from agents.api import app
        return TestClient(app)

    @pytest.mark.unit
    @pytest.mark.agent
    def test_route_endpoint(self, client):
        """Test POST /supervisor/route endpoint"""
        response = client.post(
            "/supervisor/route",
            json={
                "query": "How do I extract my database schema?",
                "context": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "primary_agent" in data
        assert "category" in data
        assert "confidence" in data
        assert "reasoning" in data

    @pytest.mark.unit
    @pytest.mark.agent
    def test_metrics_endpoint(self, client):
        """Test GET /supervisor/metrics endpoint"""
        response = client.get("/supervisor/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "routing_decisions" in data
        assert "timestamp" in data

    @pytest.mark.unit
    @pytest.mark.agent
    def test_agents_info_endpoint(self, client):
        """Test GET /supervisor/agents endpoint"""
        response = client.get("/supervisor/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "categories" in data

    @pytest.mark.unit
    @pytest.mark.agent
    def test_reset_metrics_endpoint(self, client):
        """Test POST /supervisor/reset-metrics endpoint"""
        response = client.post("/supervisor/reset-metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestSupervisorIntegration:
    """Integration tests for supervisor with other agents"""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor instance"""
        from agents.supervisor import ManagerCoordinationSupervisor
        return ManagerCoordinationSupervisor()

    @pytest.mark.unit
    @pytest.mark.agent
    def test_get_agent_info(self, supervisor):
        """Test getting agent information"""
        from agents.supervisor import AgentType

        info = supervisor.get_agent_info(AgentType.MSSQL_EXTRACTOR)

        assert info["name"] == "mssql_extractor"
        assert info["category"] == "data_extraction"
        assert "patterns" in info

    @pytest.mark.unit
    @pytest.mark.agent
    def test_all_agents_have_categories(self, supervisor):
        """Test that all agents have assigned categories"""
        from agents.supervisor import AgentType

        for agent_type in AgentType:
            if agent_type in supervisor.AGENT_CATEGORIES:
                category = supervisor.AGENT_CATEGORIES[agent_type]
                assert category is not None

    @pytest.mark.unit
    @pytest.mark.agent
    def test_routing_decision_dataclass(self):
        """Test RoutingDecision dataclass"""
        from agents.supervisor import RoutingDecision, AgentType, AgentCategory

        decision = RoutingDecision(
            primary_agent=AgentType.MSSQL_EXTRACTOR,
            category=AgentCategory.DATA_EXTRACTION,
            confidence=0.95,
            reasoning="Test reasoning"
        )

        assert decision.primary_agent == AgentType.MSSQL_EXTRACTOR
        assert decision.confidence == 0.95
        assert decision.requires_chain is False
        assert len(decision.secondary_agents) == 0
