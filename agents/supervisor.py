"""
Manager Coordination Supervisor Node

Implements the Manager Coordination pattern from "Building Applications with AI Agents"
(O'Reilly, 2025) - Chapter on Multi-Agent Coordination Patterns.

The Supervisor acts as the central routing node that:
1. Analyzes incoming queries/requests
2. Routes to appropriate specialist agents
3. Aggregates results from multiple agents when needed
4. Manages the overall workflow orchestration

Architecture:
                    ┌─────────────────┐
                    │   Supervisor    │  <- Routes queries to specialists
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Data Extract  │   │  Generation   │   │   Quality     │
│  Specialists  │   │  Specialists  │   │  Specialists  │
│ ─────────────-│   │ ─────────────-│   │ ─────────────-│
│ MSSQL Extract │   │ dbt Generator │   │ Validation    │
│               │   │ dbt Executor  │   │ Data Quality  │
└───────────────┘   └───────────────┘   └───────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Support     │   │   Security    │   │  Observability│
│  Specialists  │   │  Specialist   │   │               │
│ ─────────────-│   │ ─────────────-│   │ ─────────────-│
│ RAG Service   │   │ Guardian      │   │ Metrics/Logs  │
│ Documentation │   │ Agent         │   │ Tracing       │
└───────────────┘   └───────────────┘   └───────────────┘

Author: Alexander Garcia Angus (kether180)
Property of: OKO Investments
"""

from typing import Dict, Any, List, Literal, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import re

from .state import MigrationState

logger = logging.getLogger(__name__)


class AgentCategory(Enum):
    """Categories of specialized agents"""
    DATA_EXTRACTION = "data_extraction"
    GENERATION = "generation"
    QUALITY = "quality"
    SUPPORT = "support"
    SECURITY = "security"
    OBSERVABILITY = "observability"


class AgentType(Enum):
    """All available agent types"""
    # Data Extraction Specialists
    MSSQL_EXTRACTOR = "mssql_extractor"

    # Generation Specialists
    DBT_GENERATOR = "dbt_generator"
    DBT_EXECUTOR = "dbt_executor"

    # Quality Specialists
    VALIDATION = "validation_agent"
    DATA_QUALITY = "data_quality_agent"

    # Support Specialists
    RAG_SERVICE = "rag_service"
    DOCUMENTATION = "documentation_agent"

    # Security Specialist
    GUARDIAN = "guardian_agent"

    # Coming Soon
    DATAPREP = "dataprep_agent"
    BI_ANALYTICS = "bi_agent"
    ML_FINETUNING = "ml_finetuning_agent"


@dataclass
class RoutingDecision:
    """Result of supervisor routing decision"""
    primary_agent: AgentType
    category: AgentCategory
    confidence: float  # 0.0 to 1.0
    secondary_agents: List[AgentType] = field(default_factory=list)
    reasoning: str = ""
    requires_chain: bool = False
    chain_order: List[AgentType] = field(default_factory=list)


@dataclass
class SupervisorMetrics:
    """Tracking metrics for supervisor decisions"""
    total_requests: int = 0
    routing_decisions: Dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    chain_invocations: int = 0
    fallback_count: int = 0


class ManagerCoordinationSupervisor:
    """
    Central supervisor node implementing Manager Coordination pattern.

    This supervisor:
    1. Analyzes incoming requests using keyword matching and intent detection
    2. Routes to the most appropriate specialist agent
    3. Can invoke chains of agents for complex requests
    4. Tracks metrics for continuous improvement

    Based on: "Building Applications with AI Agents" (O'Reilly, 2025)
    """

    # Keyword patterns for routing
    ROUTING_PATTERNS = {
        AgentType.MSSQL_EXTRACTOR: [
            r'\b(extract|schema|metadata|table|column|foreign\s*key|mssql|sql\s*server)\b',
            r'\b(database|connection|connect|source)\b',
            r'\b(analyze|scan|discover)\s*(database|schema|tables?)\b'
        ],
        AgentType.DBT_GENERATOR: [
            r'\b(generate|create|build)\s*(dbt|model|staging|marts?)\b',
            r'\b(dbt\s*(project|model|source))\b',
            r'\b(transform|transformation)\b',
            r'\bstaging\s*(model|layer)\b',
            r'\b(model|staging)\s*(for|of)\b'
        ],
        AgentType.DBT_EXECUTOR: [
            r'\b(run|execute|deploy)\s*dbt\b',
            r'\bdbt\s*(run|build|test|docs)\b',
            r'\b(materialize|compile)\b'
        ],
        AgentType.VALIDATION: [
            r'\b(validate|validation|check|verify)\b',
            r'\b(quality\s*gate|actor.critic)\b',
            r'\b(test|testing)\s*(migration|model)\b'
        ],
        AgentType.DATA_QUALITY: [
            r'\b(data\s*quality|dq|profiling)\b',
            r'\b(null|duplicate|anomal|outlier)\b',
            r'\b(scan|assess)\s*data\b'
        ],
        AgentType.RAG_SERVICE: [
            r'\b(help|assist|explain|how\s*to|what\s*is)\b',
            r'\b(documentation|docs|guide)\b',
            r'\b(best\s*practice|recommend)\b'
        ],
        AgentType.DOCUMENTATION: [
            r'\b(document|describe|annotate)\b',
            r'\b(generate|create)\s*(docs|documentation|readme)\b',
            r'\b(lineage|catalog)\b'
        ],
        AgentType.GUARDIAN: [
            r'\b(security|secure|protect|encrypt)\b',
            r'\b(audit|compliance|maestro)\b',
            r'\b(threat|vulnerability|risk)\b'
        ]
    }

    # Category mappings
    AGENT_CATEGORIES = {
        AgentType.MSSQL_EXTRACTOR: AgentCategory.DATA_EXTRACTION,
        AgentType.DBT_GENERATOR: AgentCategory.GENERATION,
        AgentType.DBT_EXECUTOR: AgentCategory.GENERATION,
        AgentType.VALIDATION: AgentCategory.QUALITY,
        AgentType.DATA_QUALITY: AgentCategory.QUALITY,
        AgentType.RAG_SERVICE: AgentCategory.SUPPORT,
        AgentType.DOCUMENTATION: AgentCategory.SUPPORT,
        AgentType.GUARDIAN: AgentCategory.SECURITY,
    }

    # Common workflow chains
    WORKFLOW_CHAINS = {
        "full_migration": [
            AgentType.MSSQL_EXTRACTOR,
            AgentType.DBT_GENERATOR,
            AgentType.VALIDATION,
            AgentType.DBT_EXECUTOR
        ],
        "quality_check": [
            AgentType.DATA_QUALITY,
            AgentType.VALIDATION
        ],
        "secure_migration": [
            AgentType.GUARDIAN,
            AgentType.MSSQL_EXTRACTOR,
            AgentType.DBT_GENERATOR,
            AgentType.VALIDATION,
            AgentType.DBT_EXECUTOR,
            AgentType.GUARDIAN  # Post-migration security check
        ]
    }

    def __init__(self):
        """Initialize the supervisor with default settings"""
        self.metrics = SupervisorMetrics()
        self.default_agent = AgentType.RAG_SERVICE
        self._compiled_patterns = self._compile_patterns()
        logger.info("Manager Coordination Supervisor initialized")

    def _compile_patterns(self) -> Dict[AgentType, List[re.Pattern]]:
        """Pre-compile regex patterns for efficiency"""
        compiled = {}
        for agent_type, patterns in self.ROUTING_PATTERNS.items():
            compiled[agent_type] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]
        return compiled

    def route_request(self, query: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Main routing function - analyzes query and routes to appropriate agent.

        Args:
            query: User's request/query text
            context: Optional context (current state, migration_id, etc.)

        Returns:
            RoutingDecision with primary agent and optional chain
        """
        self.metrics.total_requests += 1

        # Normalize query
        query_lower = query.lower().strip()

        # Score each agent based on pattern matches
        scores: Dict[AgentType, float] = {}
        for agent_type, patterns in self._compiled_patterns.items():
            score = self._calculate_agent_score(query_lower, patterns)
            if score > 0:
                scores[agent_type] = score

        # Check for workflow chain triggers
        chain_decision = self._check_for_chain(query_lower, context)
        if chain_decision:
            return chain_decision

        # Select primary agent based on highest score
        if scores:
            primary_agent = max(scores, key=scores.get)
            confidence = min(scores[primary_agent], 1.0)

            # Find secondary agents (other high-scoring agents)
            secondary = [
                agent for agent, score in scores.items()
                if agent != primary_agent and score > 0.3
            ]

            decision = RoutingDecision(
                primary_agent=primary_agent,
                category=self.AGENT_CATEGORIES.get(primary_agent, AgentCategory.SUPPORT),
                confidence=confidence,
                secondary_agents=secondary[:2],  # Max 2 secondary
                reasoning=f"Matched patterns for {primary_agent.value} with confidence {confidence:.2f}"
            )
        else:
            # Fallback to default agent
            self.metrics.fallback_count += 1
            decision = RoutingDecision(
                primary_agent=self.default_agent,
                category=AgentCategory.SUPPORT,
                confidence=0.5,
                reasoning="No strong pattern match, using default RAG service"
            )

        # Update metrics
        agent_name = decision.primary_agent.value
        self.metrics.routing_decisions[agent_name] = \
            self.metrics.routing_decisions.get(agent_name, 0) + 1

        # Update running average confidence
        total = self.metrics.total_requests
        self.metrics.avg_confidence = (
            (self.metrics.avg_confidence * (total - 1) + decision.confidence) / total
        )

        logger.info(
            f"Routed query to {decision.primary_agent.value} "
            f"(confidence: {decision.confidence:.2f})"
        )

        return decision

    def _calculate_agent_score(
        self,
        query: str,
        patterns: List[re.Pattern]
    ) -> float:
        """Calculate match score for an agent based on pattern matches"""
        matches = 0
        for pattern in patterns:
            if pattern.search(query):
                matches += 1

        # Normalize by number of patterns
        return matches / len(patterns) if patterns else 0

    def _check_for_chain(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[RoutingDecision]:
        """Check if query requires a workflow chain"""

        # Full migration chain
        if any(kw in query for kw in ['full migration', 'complete migration', 'migrate everything']):
            self.metrics.chain_invocations += 1
            return RoutingDecision(
                primary_agent=AgentType.MSSQL_EXTRACTOR,
                category=AgentCategory.DATA_EXTRACTION,
                confidence=0.9,
                requires_chain=True,
                chain_order=self.WORKFLOW_CHAINS["full_migration"],
                reasoning="Full migration workflow chain triggered"
            )

        # Secure migration chain
        if any(kw in query for kw in ['secure migration', 'security', 'compliant migration']):
            self.metrics.chain_invocations += 1
            return RoutingDecision(
                primary_agent=AgentType.GUARDIAN,
                category=AgentCategory.SECURITY,
                confidence=0.9,
                requires_chain=True,
                chain_order=self.WORKFLOW_CHAINS["secure_migration"],
                reasoning="Secure migration workflow chain triggered"
            )

        # Quality check chain
        if any(kw in query for kw in ['quality check', 'full validation', 'complete check']):
            self.metrics.chain_invocations += 1
            return RoutingDecision(
                primary_agent=AgentType.DATA_QUALITY,
                category=AgentCategory.QUALITY,
                confidence=0.85,
                requires_chain=True,
                chain_order=self.WORKFLOW_CHAINS["quality_check"],
                reasoning="Quality check workflow chain triggered"
            )

        return None

    def supervisor_node(self, state: MigrationState) -> str:
        """
        LangGraph node function for supervisor routing.

        This is the main entry point when used as a LangGraph node.
        Routes to appropriate agent based on current state and phase.

        Args:
            state: Current migration state

        Returns:
            Name of the next agent node to execute
        """
        phase = state.get("phase", "assessment")

        # Phase-based routing for workflow progression
        phase_routing = {
            "assessment": AgentType.MSSQL_EXTRACTOR.value,
            "planning": AgentType.DBT_GENERATOR.value,
            "execution": AgentType.DBT_EXECUTOR.value,
            "testing": AgentType.VALIDATION.value,
            "evaluation": AgentType.VALIDATION.value,
            "complete": "end"
        }

        # Get metadata for context-aware routing
        metadata = state.get("metadata", {})

        # Check for errors requiring special handling
        errors = state.get("errors", [])
        if errors:
            logger.warning(f"Errors detected in state: {errors}")
            # Route to validation for error analysis
            return AgentType.VALIDATION.value

        # Default phase-based routing
        next_node = phase_routing.get(phase, AgentType.RAG_SERVICE.value)

        logger.info(f"Supervisor routing: phase={phase} -> {next_node}")
        return next_node

    def get_agent_info(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get information about a specific agent"""
        return {
            "name": agent_type.value,
            "category": self.AGENT_CATEGORIES.get(agent_type, AgentCategory.SUPPORT).value,
            "patterns": [p.pattern for p in self._compiled_patterns.get(agent_type, [])],
            "routing_count": self.metrics.routing_decisions.get(agent_type.value, 0)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get supervisor metrics"""
        return {
            "total_requests": self.metrics.total_requests,
            "routing_decisions": self.metrics.routing_decisions,
            "average_confidence": round(self.metrics.avg_confidence, 3),
            "chain_invocations": self.metrics.chain_invocations,
            "fallback_count": self.metrics.fallback_count,
            "fallback_rate": (
                self.metrics.fallback_count / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            )
        }

    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = SupervisorMetrics()
        logger.info("Supervisor metrics reset")


# Global supervisor instance
_supervisor: Optional[ManagerCoordinationSupervisor] = None


def get_supervisor() -> ManagerCoordinationSupervisor:
    """Get or create the global supervisor instance"""
    global _supervisor
    if _supervisor is None:
        _supervisor = ManagerCoordinationSupervisor()
    return _supervisor


def supervisor_node(state: MigrationState) -> str:
    """
    LangGraph-compatible supervisor node function.

    This is the function to use directly in LangGraph workflows:

    ```python
    from agents.supervisor import supervisor_node

    workflow = StateGraph(MigrationState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.set_entry_point("supervisor")

    # Add conditional edges based on supervisor decision
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_node,
        {
            "mssql_extractor": "mssql_extractor",
            "dbt_generator": "dbt_generator",
            "dbt_executor": "dbt_executor",
            "validation_agent": "validation_agent",
            ...
        }
    )
    ```

    Args:
        state: Current migration state

    Returns:
        Name of the next agent node
    """
    supervisor = get_supervisor()
    return supervisor.supervisor_node(state)


def route_query(query: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
    """
    Route a query to the appropriate agent.

    Convenience function for API-level routing:

    ```python
    from agents.supervisor import route_query

    decision = route_query("How do I extract my database schema?")
    print(f"Route to: {decision.primary_agent.value}")
    print(f"Confidence: {decision.confidence}")
    ```

    Args:
        query: User's query text
        context: Optional context dictionary

    Returns:
        RoutingDecision with primary agent and metadata
    """
    supervisor = get_supervisor()
    return supervisor.route_request(query, context)


# Example usage and testing
if __name__ == "__main__":
    # Test the supervisor
    supervisor = ManagerCoordinationSupervisor()

    test_queries = [
        "How do I extract schema from my MSSQL database?",
        "Generate a dbt staging model for customers",
        "Run dbt build on production",
        "Validate my migration results",
        "Check data quality for null values",
        "Help me understand how dbt works",
        "Perform a security audit",
        "Start a full migration of my database"
    ]

    print("Testing Manager Coordination Supervisor\n" + "="*50)

    for query in test_queries:
        decision = supervisor.route_request(query)
        print(f"\nQuery: {query}")
        print(f"  -> Agent: {decision.primary_agent.value}")
        print(f"  -> Category: {decision.category.value}")
        print(f"  -> Confidence: {decision.confidence:.2f}")
        if decision.requires_chain:
            print(f"  -> Chain: {[a.value for a in decision.chain_order]}")

    print("\n" + "="*50)
    print("Supervisor Metrics:")
    print(supervisor.get_metrics())
