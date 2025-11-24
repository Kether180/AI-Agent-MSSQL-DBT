"""
Adapter Layer for Legacy Agents

This module provides a bridge between the new LangGraph state structure
and the legacy agent system. It translates between MigrationState (LangGraph)
and AgentContext (legacy), allowing us to reuse existing agent logic.

Why we need this:
- Legacy agents expect AgentContext with specific fields
- LangGraph uses MigrationState TypedDict
- Different naming conventions (dbt_project_path vs project_path)
- Different ways of tracking current model
- Different result formats (AgentResult vs MigrationState)

Benefits:
- Reuse 800+ lines of existing agent code
- Gradual migration path
- Both systems can coexist
- Single source of truth for business logic
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .state import MigrationState, get_current_model
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from legacy_agent_system import AgentContext, AgentResult

logger = logging.getLogger(__name__)


def state_to_context(state: MigrationState, current_model_name: Optional[str] = None) -> AgentContext:
    """
    Convert LangGraph MigrationState to legacy AgentContext.

    Args:
        state: LangGraph migration state
        current_model_name: Optional model name to set as current

    Returns:
        AgentContext for legacy agents
    """
    # Build migration_state dict that legacy agents expect
    legacy_migration_state = {
        'phase': state.get('phase', 'assessment'),
        'models': state.get('models', []),
        'current_model_index': state.get('current_model_index', 0),
        'completed_count': state.get('completed_count', 0),
        'failed_count': state.get('failed_count', 0),
        'assessment_complete': state.get('assessment_complete', False),
        'plan_complete': state.get('plan_complete', False),
    }

    # Add assessment and planning data if available
    if state.get('assessment'):
        legacy_migration_state['assessment'] = state['assessment']
    if state.get('planning'):
        legacy_migration_state['planning'] = state['planning']

    # Set current model if provided
    if current_model_name:
        legacy_migration_state['current_model'] = current_model_name

    # Create context
    context = AgentContext(
        metadata=state.get('metadata', {}),
        dbt_project_path=state.get('project_path', ''),
        current_model=current_model_name,
        migration_state=legacy_migration_state,
        api_key=state.get('api_key')
    )

    return context


def result_to_state(result: AgentResult, state: MigrationState) -> MigrationState:
    """
    Update LangGraph MigrationState from legacy AgentResult.

    Args:
        result: Result from legacy agent
        state: Current LangGraph state to update

    Returns:
        Updated MigrationState
    """
    if result.success:
        # Update based on agent role
        agent_role = result.role.value

        if agent_role == 'assessment':
            state['assessment'] = result.data
            state['assessment_complete'] = True
            state['phase'] = 'planning'
            logger.info("Assessment completed, moving to planning phase")

        elif agent_role == 'planner':
            state['planning'] = result.data
            state['plan_complete'] = True
            state['phase'] = 'execution'

            # Initialize model list from planning data
            if 'models' in result.data:
                state['models'] = [
                    {
                        'name': model['name'],
                        'status': 'pending',
                        'attempts': 0,
                        'errors': [],
                        'validation_score': 0.0,
                        'source_object': model.get('source_object'),
                        'file_path': None
                    }
                    for model in result.data['models']
                ]
                state['current_model_index'] = 0
                logger.info(f"Planning completed, {len(state['models'])} models to migrate")

        elif agent_role == 'executor':
            # Update current model with file path and status
            current_model = get_current_model(state)
            if current_model:
                current_model['status'] = 'in_progress'
                current_model['attempts'] = current_model.get('attempts', 0) + 1

                # Extract file path from result data
                if result.data and 'file_path' in result.data:
                    current_model['file_path'] = result.data['file_path']
                    logger.info(f"Model {current_model['name']} generated at {result.data['file_path']}")

        elif agent_role == 'tester':
            # Update current model based on test results
            current_model = get_current_model(state)
            if current_model:
                current_model['status'] = 'completed'
                current_model['validation_score'] = result.data.get('validation_score', 0.95)
                state['completed_count'] = state.get('completed_count', 0) + 1
                logger.info(f"Model {current_model['name']} passed testing")

        elif agent_role == 'rebuilder':
            # Rebuilder clears errors and allows retry
            current_model = get_current_model(state)
            if current_model:
                current_model['errors'] = []
                current_model['status'] = 'in_progress'
                logger.info(f"Model {current_model['name']} rebuilt, ready for retry")

        elif agent_role == 'evaluator':
            state['phase'] = 'complete'
            logger.info("Evaluation completed, migration finished")

    else:
        # Handle failure
        if result.errors:
            state['errors'] = state.get('errors', []) + result.errors

        # For executor/tester failures, update current model
        current_model = get_current_model(state)
        if current_model and result.role.value in ['executor', 'tester', 'rebuilder']:
            current_model['status'] = 'failed'
            current_model['errors'].extend(result.errors)
            logger.warning(f"Model {current_model['name']} failed: {result.errors}")

    return state


def adapt_agent_call(agent_class, state: MigrationState) -> MigrationState:
    """
    High-level adapter function to call any legacy agent.

    This is the main entry point for using legacy agents with LangGraph.

    Args:
        agent_class: Legacy agent class (e.g., AssessmentAgent)
        state: Current LangGraph state

    Returns:
        Updated LangGraph state

    Example:
        from legacy_agents import AssessmentAgent
        state = adapt_agent_call(AssessmentAgent, state)
    """
    # Get current model name if we're in execution phase
    current_model = get_current_model(state)
    current_model_name = current_model['name'] if current_model else None

    # Convert state to context
    context = state_to_context(state, current_model_name)

    # Initialize and run agent
    agent = agent_class()
    agent.initialize(context)
    result = agent.execute(context)

    # Convert result back to state
    updated_state = result_to_state(result, state)

    return updated_state
