#!/usr/bin/env python3
"""
Test LangGraph Migration Workflow

This script tests the new LangGraph-based migration workflow
with mock data.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.state import create_initial_state
from agents.graph import create_migration_graph
from agents.native_nodes import (
    assessment_node, planner_node, executor_node,
    tester_node, rebuilder_node, evaluator_node
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_mock_metadata() -> dict:
    """Load mock MSSQL metadata"""
    metadata_file = Path("mssql_metadata.json")

    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    else:
        logger.warning("mssql_metadata.json not found, using minimal mock")
        return {
            "database": "TestDB",
            "tables": [
                {
                    "schema": "dbo",
                    "name": "customers",
                    "object_type": "USER_TABLE",
                    "columns": [
                        {"name": "customer_id", "type": "INT"},
                        {"name": "name", "type": "VARCHAR"}
                    ]
                }
            ],
            "views": [],
            "stored_procedures": [],
            "dependencies": []
        }


def main():
    """Run LangGraph migration test"""
    print("=" * 60)
    print("LangGraph Migration Workflow Test")
    print("=" * 60)
    print()

    # Load mock metadata
    print("Step 1: Loading mock metadata...")
    metadata = load_mock_metadata()
    print(f"[OK] Loaded metadata: {len(metadata.get('tables', []))} tables, "
          f"{len(metadata.get('views', []))} views, "
          f"{len(metadata.get('stored_procedures', []))} procedures")
    print()

    # Create initial state
    print("Step 2: Creating initial migration state...")
    project_path = "./test_langgraph_project"
    Path(project_path).mkdir(exist_ok=True)

    initial_state = create_initial_state(
        metadata=metadata,
        project_path=project_path,
        max_retries=3
    )
    print(f"[OK] Initial state created: phase={initial_state['phase']}")
    print()

    # Create the LangGraph workflow
    print("Step 3: Creating LangGraph workflow...")
    graph = create_migration_graph(
        assessment_node=assessment_node,
        planner_node=planner_node,
        executor_node=executor_node,
        tester_node=tester_node,
        rebuilder_node=rebuilder_node,
        evaluator_node=evaluator_node,
        use_checkpointer=True
    )
    print("[OK] LangGraph workflow compiled")
    print()

    # Run the migration
    print("Step 4: Running migration workflow...")
    print("-" * 60)

    try:
        config = {
            "configurable": {"thread_id": "test-migration-1"},
            "recursion_limit": 100  # Increase from default 25
        }

        for i, output in enumerate(graph.stream(initial_state, config=config)):
            node_name = list(output.keys())[0]
            node_state = output[node_name]

            phase = node_state.get("phase", "unknown")
            completed = node_state.get("completed_count", 0)
            failed = node_state.get("failed_count", 0)
            errors = node_state.get("errors", [])

            print(f"  Step {i+1}: {node_name}")
            print(f"    Phase: {phase}")
            print(f"    Completed: {completed}, Failed: {failed}")

            if errors:
                print(f"    Errors: {len(errors)}")
                for error in errors[:3]:  # Show first 3 errors
                    print(f"      - {error}")

            final_state = node_state

        print("-" * 60)
        print()

        # Display results
        print("Step 5: Migration Results")
        print("=" * 60)

        models = final_state.get("models", [])
        completed_count = final_state.get("completed_count", 0)
        failed_count = final_state.get("failed_count", 0)
        total = len(models)

        print(f"Total Models: {total}")
        print(f"Completed: {completed_count}")
        print(f"Failed: {failed_count}")

        if total > 0:
            success_rate = (completed_count / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        print()
        print("Model Details:")
        for model in models:
            status_icon = "[OK]" if model["status"] == "completed" else "[FAIL]"
            print(f"  {status_icon} {model['name']}: {model['status']} "
                  f"(attempts: {model['attempts']})")

        print()
        print("=" * 60)

        # Save state to file
        state_file = Path(project_path) / "migration_state_langgraph.json"
        with open(state_file, 'w') as f:
            json.dump(final_state, f, indent=2, default=str)
        print(f"State saved to: {state_file}")

        # Check for success
        if final_state.get("phase") == "complete" and failed_count == 0:
            print()
            print("[SUCCESS] All models migrated successfully!")
            return 0
        else:
            print()
            print("[WARNING] Migration completed with some failures")
            return 1

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print()
        print(f"[ERROR] Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
