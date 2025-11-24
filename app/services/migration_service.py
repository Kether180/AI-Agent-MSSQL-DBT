"""
Migration Service

Orchestrates MSSQL to dbt migrations using LangGraph agents.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from agents import create_initial_state, create_migration_graph
from agents.native_nodes import (
    assessment_node, planner_node, executor_node,
    tester_node, rebuilder_node, evaluator_node
)
from app.models import Migration, ModelFile

logger = logging.getLogger(__name__)


class MigrationService:
    """
    Service for managing migrations.

    Integrates LangGraph agents with database tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_migration(
        self,
        user_id: int,
        metadata: Dict[str, Any],
        project_name: str,
        project_path: Optional[str] = None,
        api_key_id: Optional[int] = None
    ) -> Migration:
        """
        Create a new migration record.

        Args:
            user_id: User ID
            metadata: MSSQL metadata (tables, views, procedures)
            project_name: Name for the dbt project
            project_path: Path to create dbt project (optional)
            api_key_id: API key used (for FastAPI requests)

        Returns:
            Migration instance
        """
        # Default project path
        if not project_path:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            project_path = f"./migrations/{project_name}_{timestamp}"

        # Create migration record
        migration = Migration(
            user_id=user_id,
            api_key_id=api_key_id,
            project_name=project_name,
            project_path=project_path,
            metadata_json=metadata,
            status='pending',
            phase='assessment'
        )

        self.db.add(migration)
        self.db.commit()
        self.db.refresh(migration)

        logger.info(f"Created migration {migration.id} for user {user_id}")
        return migration

    def start_migration(self, migration_id: int) -> Migration:
        """
        Start running a migration using LangGraph.

        Args:
            migration_id: Migration ID

        Returns:
            Updated migration
        """
        migration = self.db.query(Migration).filter(Migration.id == migration_id).first()
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        if migration.status != 'pending':
            raise ValueError(f"Migration {migration_id} is not in pending status")

        # Update status
        migration.status = 'running'
        migration.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Run migration
            self._run_migration(migration)

            # Update final status
            if migration.failed_models == 0:
                migration.status = 'completed'
            else:
                migration.status = 'completed_with_errors'

            migration.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            logger.error(f"Migration {migration_id} failed: {e}", exc_info=True)
            migration.status = 'failed'
            migration.error_message = str(e)
            migration.completed_at = datetime.utcnow()
            self.db.commit()
            raise

        return migration

    def _run_migration(self, migration: Migration):
        """
        Internal method to run LangGraph migration workflow.
        """
        logger.info(f"Running migration {migration.id}")

        # Create LangGraph initial state
        initial_state = create_initial_state(
            metadata=migration.metadata_json,
            project_path=migration.project_path,
            max_retries=3
        )

        # Create graph
        graph = create_migration_graph(
            assessment_node=assessment_node,
            planner_node=planner_node,
            executor_node=executor_node,
            tester_node=tester_node,
            rebuilder_node=rebuilder_node,
            evaluator_node=evaluator_node,
            use_checkpointer=False  # No checkpointing for now
        )

        # Run migration
        config = {
            "configurable": {"thread_id": f"migration-{migration.id}"},
            "recursion_limit": 100
        }

        final_state = None
        step_count = 0

        for output in graph.stream(initial_state, config=config):
            step_count += 1
            node_name = list(output.keys())[0]
            node_state = output[node_name]

            # Update migration from state
            self._update_from_state(migration, node_state)
            self.db.commit()

            final_state = node_state

            logger.info(
                f"Migration {migration.id} - Step {step_count}: {node_name} "
                f"(phase: {node_state.get('phase')}, completed: {node_state.get('completed_count', 0)})"
            )

        # Store final state
        if final_state:
            migration.state_json = dict(final_state)
            migration.assessment_json = final_state.get('assessment')
            migration.planning_json = final_state.get('planning')
            migration.evaluation_json = final_state.get('evaluation')

            # Create model file records
            self._create_model_files(migration, final_state)

        self.db.commit()
        logger.info(f"Migration {migration.id} completed successfully")

    def _update_from_state(self, migration: Migration, state: Dict[str, Any]):
        """Update migration record from LangGraph state"""
        migration.phase = state.get('phase', 'unknown')
        migration.total_models = len(state.get('models', []))
        migration.completed_models = state.get('completed_count', 0)
        migration.failed_models = state.get('failed_count', 0)
        migration.update_progress()
        migration.errors_json = state.get('errors', [])

    def _create_model_files(self, migration: Migration, state: Dict[str, Any]):
        """Create ModelFile records from final state"""
        for model_dict in state.get('models', []):
            model_file = ModelFile(
                migration_id=migration.id,
                name=model_dict.get('name'),
                model_type=model_dict.get('model_type'),
                status=model_dict.get('status'),
                file_path=model_dict.get('file_path'),
                source_object=model_dict.get('source_object'),
                validation_score=model_dict.get('validation_score'),
                attempts=model_dict.get('attempts', 0)
            )

            # Read SQL code from file if available
            if model_dict.get('file_path'):
                try:
                    with open(model_dict['file_path'], 'r') as f:
                        model_file.sql_code = f.read()
                except Exception as e:
                    logger.warning(f"Could not read SQL file: {e}")

            self.db.add(model_file)

    def get_migration(self, migration_id: int) -> Optional[Migration]:
        """Get migration by ID"""
        return self.db.query(Migration).filter(Migration.id == migration_id).first()

    def get_user_migrations(self, user_id: int, limit: int = 50) -> list:
        """Get all migrations for a user"""
        return (
            self.db.query(Migration)
            .filter(Migration.user_id == user_id)
            .order_by(Migration.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_migration_models(self, migration_id: int) -> list:
        """Get all model files for a migration"""
        return (
            self.db.query(ModelFile)
            .filter(ModelFile.migration_id == migration_id)
            .order_by(ModelFile.name)
            .all()
        )

    def delete_migration(self, migration_id: int):
        """Delete a migration and all associated files"""
        migration = self.get_migration(migration_id)
        if migration:
            self.db.delete(migration)
            self.db.commit()
            logger.info(f"Deleted migration {migration_id}")
