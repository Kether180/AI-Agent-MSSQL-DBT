"""
LangGraph Node Functions - Simplified with Adapter

This module provides LangGraph-compatible node functions that use the adapter
to call legacy agents. Much simpler and cleaner than direct integration.
"""

import os
import logging
from typing import Optional
from langchain_anthropic import ChatAnthropic

from .state import MigrationState, get_current_model
from .guardrails import check_rate_limit
from .adapter import adapt_agent_call

# Import legacy agents
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from legacy_agents import (
    AssessmentAgent, PlannerAgent, ExecutorAgent,
    TesterAgent, RebuilderAgent, EvaluatorAgent
)

logger = logging.getLogger(__name__)


def get_llm(model: str = "claude-sonnet-4-5-20250929") -> Optional[ChatAnthropic]:
    """Get LangChain ChatAnthropic instance if API key available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, using fallback logic")
        return None

    try:
        return ChatAnthropic(model=model, api_key=api_key, temperature=0, max_tokens=4096)
    except Exception as e:
        logger.error(f"Failed to initialize ChatAnthropic: {e}")
        return None


def assessment_node(state: MigrationState) -> MigrationState:
    """Assessment Agent Node - Using Adapter"""
    logger.info("Running Assessment Agent")

    if check_rate_limit("assessment_agent", max_requests=10, window_seconds=60):
        logger.warning("Rate limit exceeded")
        state["errors"] = state.get("errors", []) + ["Rate limit exceeded"]
        return state

    try:
        state = adapt_agent_call(AssessmentAgent, state)
    except Exception as e:
        logger.error(f"Assessment error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state


def planner_node(state: MigrationState) -> MigrationState:
    """Planner Agent Node - Using Adapter"""
    logger.info("Running Planner Agent")

    if check_rate_limit("planner_agent", max_requests=10, window_seconds=60):
        logger.warning("Rate limit exceeded")
        state["errors"] = state.get("errors", []) + ["Rate limit exceeded"]
        return state

    try:
        state = adapt_agent_call(PlannerAgent, state)
    except Exception as e:
        logger.error(f"Planner error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state


def executor_node(state: MigrationState) -> MigrationState:
    """Executor Agent Node - Using Adapter"""
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to execute")
        return state

    model_name = current_model["name"]
    logger.info(f"Running Executor Agent for model: {model_name}")

    if check_rate_limit(f"executor_{model_name}", max_requests=5, window_seconds=60):
        logger.warning(f"Rate limit exceeded for {model_name}")
        current_model["errors"].append("Rate limit exceeded")
        return state

    try:
        state = adapt_agent_call(ExecutorAgent, state)
    except Exception as e:
        logger.error(f"Executor error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"

    return state


def tester_node(state: MigrationState) -> MigrationState:
    """Tester Agent Node - Using Adapter"""
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to test")
        return state

    model_name = current_model["name"]
    logger.info(f"Running Tester Agent for model: {model_name}")

    try:
        state = adapt_agent_call(TesterAgent, state)
    except Exception as e:
        logger.error(f"Tester error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"

    return state


def rebuilder_node(state: MigrationState) -> MigrationState:
    """Rebuilder Agent Node - Using Adapter"""
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
        state = adapt_agent_call(RebuilderAgent, state)
    except Exception as e:
        logger.error(f"Rebuilder error: {e}", exc_info=True)
        current_model["errors"].append(str(e))
        current_model["status"] = "failed"
        state["failed_count"] = state.get("failed_count", 0) + 1

    return state


def evaluator_node(state: MigrationState) -> MigrationState:
    """Evaluator Agent Node - Using Adapter"""
    logger.info("Running Evaluator Agent")

    try:
        state = adapt_agent_call(EvaluatorAgent, state)
    except Exception as e:
        logger.error(f"Evaluator error: {e}", exc_info=True)
        state["errors"] = state.get("errors", []) + [str(e)]

    return state
