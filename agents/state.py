"""
LangGraph State Management for MSSQL to dbt Migration

This module defines the typed state structure used by LangGraph for orchestrating
the multi-agent migration workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Pydantic Models for structured data

class TableAssessment(BaseModel):
    """Assessment details for a single table"""
    full_name: str
    schema_name: str = Field(alias="schema")
    name: str
    type: str
    complexity: int
    priority: int
    row_count: int
    column_count: int
    dependency_count: int
    recommendation: str
    migrate: bool

    class Config:
        populate_by_name = True


class ProcedureAssessment(BaseModel):
    """Assessment details for a stored procedure"""
    full_name: str
    schema_name: str = Field(alias="schema")
    name: str
    type: str
    complexity: int
    recommendation: str
    migrate: bool

    class Config:
        populate_by_name = True


class ViewAssessment(BaseModel):
    """Assessment details for a view"""
    full_name: str
    schema_name: str = Field(alias="schema")
    name: str
    type: str
    complexity: int
    priority: int
    dependency_count: int
    recommendation: str
    migrate: bool

    class Config:
        populate_by_name = True


class MigrationStrategy(BaseModel):
    """Overall migration strategy"""
    approach: str
    phases: List[Dict[str, Any]]
    estimated_duration: str
    recommendations: List[str] = Field(default_factory=list)


class AssessmentData(BaseModel):
    """Complete assessment data"""
    total_objects: int
    tables: List[TableAssessment]
    views: List[ViewAssessment] = Field(default_factory=list)
    procedures: List[ProcedureAssessment] = Field(default_factory=list)
    strategy: Optional[MigrationStrategy] = None


class ModelPlan(BaseModel):
    """Migration plan for a single model"""
    name: str
    source_object: str
    target_type: str
    materialization: str
    priority: int
    dependencies: List[str] = Field(default_factory=list)


class PlanningData(BaseModel):
    """Complete planning data"""
    models: List[ModelPlan]
    execution_order: List[str]


class ModelState(BaseModel):
    """State of a single model during migration"""
    name: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    attempts: int = 0
    errors: List[str] = Field(default_factory=list)
    validation_score: float = 0.0
    source_object: Optional[str] = None
    file_path: Optional[str] = None


# TypedDict for LangGraph State

class MigrationState(TypedDict, total=False):
    """
    Main state object for LangGraph migration workflow.

    This matches the structure of migration_state.json and is passed
    between all agent nodes in the graph.
    """
    # Workflow phase
    phase: Literal["assessment", "planning", "execution", "evaluation", "complete"]

    # Model tracking
    models: List[Dict[str, Any]]  # List of ModelState dicts
    current_model_index: int
    completed_count: int
    failed_count: int

    # Phase completion flags
    assessment_complete: bool
    plan_complete: bool

    # Agent outputs
    assessment: Optional[Dict[str, Any]]  # AssessmentData as dict
    planning: Optional[Dict[str, Any]]     # PlanningData as dict

    # Metadata
    metadata: Optional[Dict[str, Any]]
    project_path: Optional[str]

    # Error tracking
    errors: List[str]

    # Timestamps
    started_at: Optional[str]
    completed_at: Optional[str]

    # Retry control
    max_retries: int
    current_retry: int


def create_initial_state(
    metadata: Dict[str, Any],
    project_path: str,
    max_retries: int = 3
) -> MigrationState:
    """
    Create initial migration state.

    Args:
        metadata: MSSQL metadata dictionary
        project_path: Path to dbt project
        max_retries: Maximum retry attempts per model

    Returns:
        Initial MigrationState for the workflow
    """
    return MigrationState(
        phase="assessment",
        models=[],
        current_model_index=0,
        completed_count=0,
        failed_count=0,
        assessment_complete=False,
        plan_complete=False,
        assessment=None,
        planning=None,
        metadata=metadata,
        project_path=project_path,
        errors=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        max_retries=max_retries,
        current_retry=0
    )


def get_current_model(state: MigrationState) -> Optional[Dict[str, Any]]:
    """Get the current model being processed"""
    if state.get("models") and state.get("current_model_index", 0) < len(state["models"]):
        return state["models"][state["current_model_index"]]
    return None


def update_model_state(
    state: MigrationState,
    model_name: str,
    updates: Dict[str, Any]
) -> MigrationState:
    """
    Update a specific model's state.

    Args:
        state: Current migration state
        model_name: Name of model to update
        updates: Dictionary of fields to update

    Returns:
        Updated state
    """
    for model in state.get("models", []):
        if model.get("name") == model_name:
            model.update(updates)
            break
    return state


def advance_model_index(state: MigrationState) -> MigrationState:
    """Move to next model in the list"""
    current_index = state.get("current_model_index", 0)
    state["current_model_index"] = current_index + 1
    return state


def is_migration_complete(state: MigrationState) -> bool:
    """Check if all models have been processed"""
    current_index = state.get("current_model_index", 0)
    total_models = len(state.get("models", []))
    return current_index >= total_models


def get_migration_summary(state: MigrationState) -> Dict[str, Any]:
    """Get summary of migration results"""
    models = state.get("models", [])

    return {
        "total": len(models),
        "completed": state.get("completed_count", 0),
        "failed": state.get("failed_count", 0),
        "pending": sum(1 for m in models if m.get("status") == "pending"),
        "success_rate": (
            state.get("completed_count", 0) / len(models) * 100
            if models else 0
        )
    }
