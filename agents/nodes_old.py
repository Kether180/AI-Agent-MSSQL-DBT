"""
LangGraph Node Functions

This module provides LangGraph-compatible node functions that wrap the existing
agent logic from agents.py. Each node function takes MigrationState as input
and returns updated MigrationState.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from langchain_anthropic import ChatAnthropic

from .state import MigrationState, get_current_model, update_model_state, ModelState
from .guardrails import (
    validate_llm_input, validate_llm_output, sanitize_sql_output,
    check_rate_limit, with_fallback, validate_json_output
)
from .adapter import adapt_agent_call

# Import existing agent logic from root directory
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from legacy_agents import (
    AssessmentAgent, PlannerAgent, ExecutorAgent,
    TesterAgent, RebuilderAgent, EvaluatorAgent
)
from legacy_agent_system import AgentContext

logger = logging.getLogger(__name__)


def get_llm(model: str = "claude-sonnet-4-5-20250929") -> Optional[ChatAnthropic]:
    """
    Get LangChain ChatAnthropic instance if API key available.

    Args:
        model: Model name to use

    Returns:
        ChatAnthropic instance or None if no API key
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, using fallback logic")
        return None

    try:
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0,
            max_tokens=4096
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChatAnthropic: {e}")
        return None


def assessment_node(state: MigrationState) -> MigrationState:
    """
    Assessment Agent Node - Using Adapter

    Evaluates MSSQL metadata and determines what to migrate.

    Args:
        state: Current migration state

    Returns:
        Updated state with assessment data
    """
    logger.info("Running Assessment Agent")

    # Check rate limit
    if check_rate_limit("assessment_agent", max_requests=10, window_seconds=60):
        logger.warning("Rate limit exceeded for assessment agent")
        state["errors"] = state.get("errors", []) + ["Rate limit exceeded"]
        return state

    try:
        # Use adapter to call legacy agent
        state = adapt_agent_call(AssessmentAgent, state)
    except Exception as e:
        logger.error(f"Assessment node error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state


def planner_node(state: MigrationState) -> MigrationState:
    """
    Planner Agent Node - Using Adapter

    Creates detailed migration plan with execution order.

    Args:
        state: Current migration state

    Returns:
        Updated state with planning data and model list
    """
    logger.info("Running Planner Agent")

    # Check rate limit
    if check_rate_limit("planner_agent", max_requests=10, window_seconds=60):
        logger.warning("Rate limit exceeded for planner agent")
        state["errors"] = state.get("errors", []) + ["Rate limit exceeded"]
        return state

    try:
        # Use adapter to call legacy agent
        state = adapt_agent_call(PlannerAgent, state)
    except Exception as e:
        logger.error(f"Planner node error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state


def executor_node(state: MigrationState) -> MigrationState:
    """
    Executor Agent Node - Using Adapter

    Generates dbt model files for the current model.

    Args:
        state: Current migration state

    Returns:
        Updated state with execution results
    """
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to execute")
        return state

    model_name = current_model["name"]
    logger.info(f"Running Executor Agent for model: {model_name}")

    # Check rate limit
    if check_rate_limit(f"executor_{model_name}", max_requests=5, window_seconds=60):
        logger.warning(f"Rate limit exceeded for executor on {model_name}")
        current_model["errors"].append("Rate limit exceeded")
        return state

    try:
        # Use adapter to call legacy agent
        state = adapt_agent_call(ExecutorAgent, state)
    except Exception as e:
        logger.error(f"Executor node error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"

    return state


def tester_node(state: MigrationState) -> MigrationState:
    """
    Tester Agent Node

    Validates the generated dbt model.

    Args:
        state: Current migration state

    Returns:
        Updated state with test results
    """
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to test")
        return state

    model_name = current_model["name"]
    logger.info(f"Running Tester Agent for model: {model_name}")

    try:
        # Create context from state
        context = AgentContext(
            metadata=state.get("metadata", {}),
            migration_state=dict(state),
            dbt_project_path=state.get("project_path", ""),
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        # Set current model in context
        context.migration_state["current_model"] = model_name

        # Run existing tester agent
        agent = TesterAgent()
        agent.initialize(context)
        result = agent.execute(context)

        if result.success:
            # Test passed
            current_model["status"] = "completed"
            current_model["validation_score"] = result.data.get("validation_score", 0.95)
            state["completed_count"] = state.get("completed_count", 0) + 1

            logger.info(f"Testing passed for {model_name}")
        else:
            # Test failed
            current_model["status"] = "failed"
            current_model["errors"].extend(result.errors)

            logger.warning(f"Testing failed for {model_name}: {result.errors}")

    except Exception as e:
        logger.error(f"Tester node error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"

    return state


def rebuilder_node(state: MigrationState) -> MigrationState:
    """
    Rebuilder Agent Node

    Fixes errors and regenerates failed models.

    Args:
        state: Current migration state

    Returns:
        Updated state with rebuild results
    """
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to rebuild")
        return state

    model_name = current_model["name"]
    logger.info(f"Running Rebuilder Agent for model: {model_name}")

    # Check retry count
    if current_model["attempts"] >= state.get("max_retries", 3):
        logger.warning(f"Max retries exceeded for {model_name}")
        current_model["status"] = "failed"
        state["failed_count"] = state.get("failed_count", 0) + 1
        return state

    try:
        # Create context from state
        context = AgentContext(
            metadata=state.get("metadata", {}),
            migration_state=dict(state),
            dbt_project_path=state.get("project_path", ""),
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        # Set current model in context
        context.migration_state["current_model"] = model_name
        context.migration_state["current_errors"] = current_model.get("errors", [])

        # Run existing rebuilder agent
        agent = RebuilderAgent()
        agent.initialize(context)
        result = agent.execute(context)

        if result.success:
            # Clear previous errors
            current_model["errors"] = []
            current_model["status"] = "in_progress"
            current_model["attempts"] += 1

            logger.info(f"Rebuild completed for {model_name}, retrying test")
        else:
            logger.error(f"Rebuild failed for {model_name}")
            current_model["errors"].extend(result.errors)
            current_model["status"] = "failed"
            state["failed_count"] = state.get("failed_count", 0) + 1

    except Exception as e:
        logger.error(f"Rebuilder node error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"
        state["failed_count"] = state.get("failed_count", 0) + 1

    return state


def evaluator_node(state: MigrationState) -> MigrationState:
    """
    Evaluator Agent Node

    Validates correctness of all migrated models.

    Args:
        state: Current migration state

    Returns:
        Updated state with evaluation results
    """
    logger.info("Running Evaluator Agent")

    try:
        # Create context from state
        context = AgentContext(
            metadata=state.get("metadata", {}),
            migration_state=dict(state),
            dbt_project_path=state.get("project_path", ""),
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        # Run existing evaluator agent
        agent = EvaluatorAgent()
        agent.initialize(context)
        result = agent.execute(context)

        if result.success:
            state["phase"] = "complete"
            state["completed_at"] = result.data.get("completed_at")

            logger.info("Evaluation completed successfully")
        else:
            logger.error("Evaluation encountered issues")
            state["errors"] = state.get("errors", []) + result.errors

    except Exception as e:
        logger.error(f"Evaluator node error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state
