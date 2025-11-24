"""
LangGraph Workflow for MSSQL to dbt Migration

This module defines the StateGraph that orchestrates the 6-agent migration workflow.
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from .state import MigrationState, get_current_model, is_migration_complete

logger = logging.getLogger(__name__)


def should_continue_migration(state: MigrationState) -> Literal["execute_model", "complete"]:
    """
    Conditional edge after planner to check if there are models to migrate.

    Args:
        state: Current migration state

    Returns:
        Next node to execute
    """
    models = state.get("models", [])

    if not models:
        logger.warning("No models to migrate")
        return "complete"

    if is_migration_complete(state):
        logger.info("All models processed, moving to evaluation")
        return "complete"

    return "execute_model"


def should_rebuild_or_continue(state: MigrationState) -> Literal["rebuilder", "advance_to_next", "evaluator"]:
    """
    Conditional edge after tester to route based on test results.

    Args:
        state: Current migration state

    Returns:
        Next node to execute
    """
    current_model = get_current_model(state)

    if not current_model:
        return "evaluator"

    status = current_model.get("status")
    attempts = current_model.get("attempts", 0)
    max_retries = state.get("max_retries", 3)

    # If test passed, move to next model
    if status == "completed":
        logger.info(f"Model {current_model.get('name')} passed testing")
        return "advance_to_next"

    # If failed and still have retries, rebuild
    if status == "failed" and attempts < max_retries:
        logger.info(
            f"Model {current_model.get('name')} failed, "
            f"attempting rebuild (attempt {attempts}/{max_retries})"
        )
        return "rebuilder"

    # If exceeded retries, move to next model
    logger.warning(
        f"Model {current_model.get('name')} exceeded max retries, "
        f"moving to next model"
    )
    return "advance_to_next"


def advance_to_next_model(state: MigrationState) -> MigrationState:
    """
    Helper node to advance to the next model in the migration list.

    Args:
        state: Current migration state

    Returns:
        Updated state with incremented model index
    """
    current_index = state.get("current_model_index", 0)
    total_models = len(state.get("models", []))

    state["current_model_index"] = current_index + 1

    # Check if we're done with all models
    if state["current_model_index"] >= total_models:
        logger.info("All models processed")
        state["phase"] = "evaluation"
        return state

    logger.info(
        f"Advancing to model {state['current_model_index'] + 1}/{total_models}"
    )

    # Return to executor for next model
    return state


def after_advance_check(state: MigrationState) -> Literal["execute_model", "evaluator"]:
    """
    Conditional edge after advance_to_next to check if more models exist.

    Args:
        state: Current migration state

    Returns:
        Next node to execute
    """
    if is_migration_complete(state):
        return "evaluator"
    return "execute_model"


def compile_graph(
    assessment_node: callable,
    planner_node: callable,
    executor_node: callable,
    tester_node: callable,
    rebuilder_node: callable,
    evaluator_node: callable,
    checkpointer: Any = None
) -> StateGraph:
    """
    Compile the LangGraph StateGraph for the migration workflow.

    The workflow structure:
    1. assessment → planner
    2. planner → [conditional] execute_model or complete
    3. execute_model → tester
    4. tester → [conditional] rebuilder, advance_to_next, or evaluator
    5. rebuilder → tester (retry loop)
    6. advance_to_next → [conditional] execute_model or evaluator
    7. evaluator → END

    Args:
        assessment_node: Assessment agent function
        planner_node: Planner agent function
        executor_node: Executor agent function
        tester_node: Tester agent function
        rebuilder_node: Rebuilder agent function
        evaluator_node: Evaluator agent function
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(MigrationState)

    # Add all nodes
    workflow.add_node("assessment", assessment_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("execute_model", executor_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("rebuilder", rebuilder_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("advance_to_next", advance_to_next_model)

    # Set entry point
    workflow.set_entry_point("assessment")

    # Add edges
    # assessment → planner
    workflow.add_edge("assessment", "planner")

    # planner → [conditional] execute_model or complete
    workflow.add_conditional_edges(
        "planner",
        should_continue_migration,
        {
            "execute_model": "execute_model",
            "complete": "evaluator"
        }
    )

    # execute_model → tester
    workflow.add_edge("execute_model", "tester")

    # tester → [conditional] rebuilder, advance_to_next, or evaluator
    workflow.add_conditional_edges(
        "tester",
        should_rebuild_or_continue,
        {
            "rebuilder": "rebuilder",
            "advance_to_next": "advance_to_next",
            "evaluator": "evaluator"
        }
    )

    # rebuilder → tester (retry loop)
    workflow.add_edge("rebuilder", "tester")

    # advance_to_next → [conditional] execute_model or evaluator
    workflow.add_conditional_edges(
        "advance_to_next",
        after_advance_check,
        {
            "execute_model": "execute_model",
            "evaluator": "evaluator"
        }
    )

    # evaluator → END
    workflow.add_edge("evaluator", END)

    # Compile with optional checkpointer
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()


def run_migration(
    graph: StateGraph,
    initial_state: MigrationState,
    config: Dict[str, Any] = None
) -> MigrationState:
    """
    Run the migration workflow using the compiled graph.

    Args:
        graph: Compiled StateGraph
        initial_state: Initial migration state
        config: Optional configuration for graph execution

    Returns:
        Final migration state
    """
    logger.info("Starting migration workflow")

    config = config or {"configurable": {"thread_id": "migration-1"}}

    try:
        # Run the graph
        final_state = None
        for output in graph.stream(initial_state, config=config):
            # output is a dict with node name as key
            node_name = list(output.keys())[0]
            node_state = output[node_name]

            logger.info(f"Completed node: {node_name}")
            logger.debug(f"State after {node_name}: {node_state.get('phase')}")

            final_state = node_state

        logger.info("Migration workflow completed")
        return final_state

    except Exception as e:
        logger.error(f"Migration workflow failed: {e}", exc_info=True)
        raise


def create_checkpointer() -> MemorySaver:
    """
    Create a checkpointer for state persistence.

    Returns:
        MemorySaver instance
    """
    return MemorySaver()


def visualize_graph(graph: StateGraph, output_path: str = "migration_graph.png") -> None:
    """
    Visualize the graph structure (requires pygraphviz).

    Args:
        graph: Compiled StateGraph
        output_path: Path to save visualization
    """
    try:
        from IPython.display import Image, display
        display(Image(graph.get_graph().draw_mermaid_png()))
    except ImportError:
        logger.warning("Cannot visualize graph: IPython not available")
    except Exception as e:
        logger.warning(f"Cannot visualize graph: {e}")


# Example usage function
def create_migration_graph(
    assessment_node: callable,
    planner_node: callable,
    executor_node: callable,
    tester_node: callable,
    rebuilder_node: callable,
    evaluator_node: callable,
    use_checkpointer: bool = True
) -> StateGraph:
    """
    Convenience function to create the migration graph with all nodes.

    Args:
        assessment_node: Assessment agent function
        planner_node: Planner agent function
        executor_node: Executor agent function
        tester_node: Tester agent function
        rebuilder_node: Rebuilder agent function
        evaluator_node: Evaluator agent function
        use_checkpointer: Whether to use state persistence

    Returns:
        Compiled StateGraph ready to run
    """
    checkpointer = create_checkpointer() if use_checkpointer else None

    return compile_graph(
        assessment_node=assessment_node,
        planner_node=planner_node,
        executor_node=executor_node,
        tester_node=tester_node,
        rebuilder_node=rebuilder_node,
        evaluator_node=evaluator_node,
        checkpointer=checkpointer
    )
