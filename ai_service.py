"""
FastAPI wrapper for the LangGraph Migration Agents.

This service exposes the MSSQL to dbt migration agents via a REST API,
allowing the Go backend to trigger and monitor migrations.

Includes cost tracking for Claude API usage.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx

from agents.state import MigrationState
from agents.graph import create_migration_graph, run_migration
from agents.native_nodes import (
    assessment_node,
    planner_node,
    executor_node,
    tester_node,
    rebuilder_node,
    evaluator_node,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend URL for updating migration status
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# Store active migrations
active_migrations: Dict[int, Dict[str, Any]] = {}


# =============================================================================
# Cost Tracking System
# =============================================================================

@dataclass
class CostTracker:
    """
    Tracks Claude API costs per migration and globally.

    Pricing (per 1M tokens) as of December 2024:
    - Claude Opus 4: $15.00 input, $75.00 output
    - Claude Sonnet 4: $3.00 input, $15.00 output
    - Claude Haiku 3.5: $0.80 input, $4.00 output
    """

    PRICING: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
        # Legacy models
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    })

    # Track costs per migration
    migration_costs: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    # Global totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for a single API call."""
        pricing = self.PRICING.get(model, self.PRICING["claude-sonnet-4-20250514"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def track_usage(
        self,
        migration_id: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "unknown"
    ) -> float:
        """Track token usage for a migration."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Update global totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.total_requests += 1

        # Initialize migration tracking if needed
        if migration_id not in self.migration_costs:
            self.migration_costs[migration_id] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "requests": 0,
                "operations": [],
                "by_model": {},
            }

        mc = self.migration_costs[migration_id]
        mc["input_tokens"] += input_tokens
        mc["output_tokens"] += output_tokens
        mc["total_cost"] += cost
        mc["requests"] += 1
        mc["operations"].append({
            "operation": operation,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Track by model
        if model not in mc["by_model"]:
            mc["by_model"][model] = {"input": 0, "output": 0, "cost": 0.0, "calls": 0}
        mc["by_model"][model]["input"] += input_tokens
        mc["by_model"][model]["output"] += output_tokens
        mc["by_model"][model]["cost"] += cost
        mc["by_model"][model]["calls"] += 1

        logger.info(
            f"[Cost Tracker] Migration {migration_id} | {operation} | "
            f"Model: {model} | Tokens: {input_tokens}/{output_tokens} | Cost: ${cost:.4f}"
        )

        return cost

    def get_migration_cost(self, migration_id: int) -> Optional[Dict[str, Any]]:
        """Get cost summary for a specific migration."""
        return self.migration_costs.get(migration_id)

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global cost statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "total_requests": self.total_requests,
            "migrations_tracked": len(self.migration_costs),
            "avg_cost_per_request": round(self.total_cost / max(1, self.total_requests), 4),
        }

    def select_model(self, task_complexity: str) -> str:
        """
        Select the appropriate model based on task complexity.
        This implements tiered model routing to optimize costs.
        """
        if task_complexity == "simple":
            # Schema extraction, basic SQL parsing
            return "claude-3-5-haiku-20241022"
        elif task_complexity == "medium":
            # dbt model generation, standard transforms
            return "claude-sonnet-4-20250514"
        else:
            # Complex reasoning, multi-step planning, architecture decisions
            return "claude-opus-4-20250514"


# Global cost tracker instance
cost_tracker = CostTracker()


class MigrationRequest(BaseModel):
    """Request to start a new migration."""
    migration_id: int
    source_connection: Dict[str, Any]
    target_project: str
    tables: Optional[List[str]] = None
    include_views: bool = False


class MigrationStatus(BaseModel):
    """Status of a migration."""
    migration_id: int
    status: str
    progress: int
    current_phase: Optional[str] = None
    current_model: Optional[str] = None
    error: Optional[str] = None
    completed_models: int = 0
    total_models: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("AI Service starting up...")
    yield
    logger.info("AI Service shutting down...")
    # Cancel any running migrations
    for migration_id in list(active_migrations.keys()):
        if "task" in active_migrations[migration_id]:
            active_migrations[migration_id]["task"].cancel()


app = FastAPI(
    title="DataMigrate AI Service",
    description="AI agents for MSSQL to dbt migrations",
    version="1.0.0",
    lifespan=lifespan,
)


async def update_backend_status(
    migration_id: int,
    status: str,
    progress: int,
    error: Optional[str] = None
):
    """Update migration status in the Go backend."""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "status": status,
                "progress": progress,
            }
            if error:
                payload["error"] = error

            await client.patch(
                f"{BACKEND_URL}/api/v1/internal/migrations/{migration_id}/status",
                json=payload,
                timeout=10.0,
            )
    except Exception as e:
        logger.error(f"Failed to update backend status: {e}")


async def run_migration_task(
    migration_id: int,
    initial_state: MigrationState
):
    """Background task to run a migration."""
    try:
        active_migrations[migration_id]["status"] = "running"
        await update_backend_status(migration_id, "running", 0)

        # Create the migration graph
        graph = create_migration_graph(
            assessment_node=assessment_node,
            planner_node=planner_node,
            executor_node=executor_node,
            tester_node=tester_node,
            rebuilder_node=rebuilder_node,
            evaluator_node=evaluator_node,
            use_checkpointer=True,
        )

        # Run migration in a thread pool to not block async
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None,
            lambda: run_migration(
                graph,
                initial_state,
                {"configurable": {"thread_id": f"migration-{migration_id}"}}
            )
        )

        # Update final status
        models = final_state.get("models", [])
        completed = sum(1 for m in models if m.get("status") == "completed")
        failed = sum(1 for m in models if m.get("status") == "failed")

        if failed == 0 and completed > 0:
            status = "completed"
            progress = 100
            error = None
        elif completed > 0:
            status = "completed"
            progress = 100
            error = f"{failed} model(s) failed"
        else:
            status = "failed"
            progress = 0
            error = "All models failed"

        active_migrations[migration_id].update({
            "status": status,
            "progress": progress,
            "error": error,
            "final_state": final_state,
        })

        await update_backend_status(migration_id, status, progress, error)

    except asyncio.CancelledError:
        logger.info(f"Migration {migration_id} was cancelled")
        active_migrations[migration_id]["status"] = "failed"
        active_migrations[migration_id]["error"] = "Cancelled by user"
        await update_backend_status(migration_id, "failed", 0, "Cancelled by user")

    except Exception as e:
        logger.error(f"Migration {migration_id} failed: {e}", exc_info=True)
        active_migrations[migration_id]["status"] = "failed"
        active_migrations[migration_id]["error"] = str(e)
        await update_backend_status(migration_id, "failed", 0, str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="datamigrate-ai",
        version="1.0.0",
    )


@app.post("/migrations/start")
async def start_migration(
    request: MigrationRequest,
    background_tasks: BackgroundTasks
):
    """Start a new migration."""
    if request.migration_id in active_migrations:
        existing = active_migrations[request.migration_id]
        if existing.get("status") == "running":
            raise HTTPException(
                status_code=400,
                detail="Migration is already running"
            )

    # Create initial state
    initial_state: MigrationState = {
        "migration_id": request.migration_id,
        "source_connection": request.source_connection,
        "target_project": request.target_project,
        "tables": request.tables or [],
        "include_views": request.include_views,
        "phase": "assessment",
        "models": [],
        "current_model_index": 0,
        "max_retries": 3,
        "errors": [],
        "started_at": datetime.utcnow().isoformat(),
    }

    # Store migration info
    active_migrations[request.migration_id] = {
        "status": "pending",
        "progress": 0,
        "initial_state": initial_state,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Start background task
    background_tasks.add_task(
        run_migration_task,
        request.migration_id,
        initial_state
    )

    return {"message": "Migration started", "migration_id": request.migration_id}


@app.get("/migrations/{migration_id}/status", response_model=MigrationStatus)
async def get_migration_status(migration_id: int):
    """Get the status of a migration."""
    if migration_id not in active_migrations:
        raise HTTPException(
            status_code=404,
            detail="Migration not found"
        )

    migration = active_migrations[migration_id]
    state = migration.get("final_state") or migration.get("initial_state", {})
    models = state.get("models", [])

    return MigrationStatus(
        migration_id=migration_id,
        status=migration.get("status", "unknown"),
        progress=migration.get("progress", 0),
        current_phase=state.get("phase"),
        current_model=state.get("models", [{}])[state.get("current_model_index", 0)].get("name")
        if state.get("models") else None,
        error=migration.get("error"),
        completed_models=sum(1 for m in models if m.get("status") == "completed"),
        total_models=len(models),
    )


@app.post("/migrations/{migration_id}/stop")
async def stop_migration(migration_id: int):
    """Stop a running migration."""
    if migration_id not in active_migrations:
        raise HTTPException(
            status_code=404,
            detail="Migration not found"
        )

    migration = active_migrations[migration_id]

    if migration.get("status") != "running":
        raise HTTPException(
            status_code=400,
            detail="Migration is not running"
        )

    if "task" in migration:
        migration["task"].cancel()

    migration["status"] = "failed"
    migration["error"] = "Stopped by user"

    await update_backend_status(migration_id, "failed", 0, "Stopped by user")

    return {"message": "Migration stopped", "migration_id": migration_id}


@app.get("/migrations")
async def list_migrations():
    """List all migrations tracked by this service."""
    return [
        {
            "migration_id": mid,
            "status": m.get("status"),
            "progress": m.get("progress"),
            "created_at": m.get("created_at"),
            "error": m.get("error"),
        }
        for mid, m in active_migrations.items()
    ]


# =============================================================================
# Cost Tracking Endpoints
# =============================================================================

class CostResponse(BaseModel):
    """Cost information response."""
    migration_id: Optional[int] = None
    input_tokens: int
    output_tokens: int
    total_cost: float
    requests: int
    by_model: Optional[Dict[str, Any]] = None


class GlobalCostResponse(BaseModel):
    """Global cost statistics response."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    total_requests: int
    migrations_tracked: int
    avg_cost_per_request: float


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    tables_count: int
    avg_columns_per_table: int = 10
    complexity: str = "medium"  # simple, medium, complex


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    cost_breakdown: Dict[str, float]
    recommended_model_mix: Dict[str, str]


@app.get("/costs/global", response_model=GlobalCostResponse)
async def get_global_costs():
    """Get global cost statistics across all migrations."""
    stats = cost_tracker.get_global_stats()
    return GlobalCostResponse(**stats)


@app.get("/costs/migration/{migration_id}", response_model=CostResponse)
async def get_migration_costs(migration_id: int):
    """Get cost breakdown for a specific migration."""
    costs = cost_tracker.get_migration_cost(migration_id)
    if not costs:
        raise HTTPException(
            status_code=404,
            detail="No cost data found for this migration"
        )

    return CostResponse(
        migration_id=migration_id,
        input_tokens=costs["input_tokens"],
        output_tokens=costs["output_tokens"],
        total_cost=round(costs["total_cost"], 4),
        requests=costs["requests"],
        by_model=costs["by_model"],
    )


@app.post("/costs/estimate", response_model=CostEstimateResponse)
async def estimate_migration_cost(request: CostEstimateRequest):
    """
    Estimate the cost of a migration before running it.

    This provides a rough estimate based on:
    - Number of tables
    - Average complexity
    - Typical token usage patterns
    """
    tables = request.tables_count
    cols = request.avg_columns_per_table
    complexity = request.complexity

    # Estimate tokens per operation (based on typical usage)
    schema_analysis_tokens = tables * cols * 50  # ~50 tokens per column for schema
    relationship_tokens = tables * 200  # ~200 tokens per table for relationships
    dbt_gen_input = tables * 500  # ~500 input tokens per model
    dbt_gen_output = tables * 1500  # ~1500 output tokens per model (SQL + YAML)
    test_gen_tokens = tables * 300  # ~300 tokens per table for tests

    # Calculate costs by model based on complexity
    if complexity == "simple":
        # Use Haiku for most operations
        schema_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            schema_analysis_tokens,
            int(schema_analysis_tokens * 0.3)
        )
        rel_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            relationship_tokens,
            int(relationship_tokens * 0.5)
        )
        dbt_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            dbt_gen_input,
            dbt_gen_output
        )
        test_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            test_gen_tokens,
            int(test_gen_tokens * 0.8)
        )
        model_mix = {
            "schema_analysis": "Haiku",
            "relationship_detection": "Haiku",
            "dbt_generation": "Haiku",
            "test_generation": "Haiku",
        }
    elif complexity == "medium":
        # Mix of Haiku and Sonnet
        schema_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            schema_analysis_tokens,
            int(schema_analysis_tokens * 0.3)
        )
        rel_cost = cost_tracker.calculate_cost(
            "claude-sonnet-4-20250514",
            relationship_tokens,
            int(relationship_tokens * 0.5)
        )
        dbt_cost = cost_tracker.calculate_cost(
            "claude-sonnet-4-20250514",
            dbt_gen_input,
            dbt_gen_output
        )
        test_cost = cost_tracker.calculate_cost(
            "claude-3-5-haiku-20241022",
            test_gen_tokens,
            int(test_gen_tokens * 0.8)
        )
        model_mix = {
            "schema_analysis": "Haiku",
            "relationship_detection": "Sonnet",
            "dbt_generation": "Sonnet",
            "test_generation": "Haiku",
        }
    else:
        # Complex: Use Opus for planning, Sonnet for execution
        schema_cost = cost_tracker.calculate_cost(
            "claude-sonnet-4-20250514",
            schema_analysis_tokens,
            int(schema_analysis_tokens * 0.3)
        )
        rel_cost = cost_tracker.calculate_cost(
            "claude-opus-4-20250514",
            relationship_tokens,
            int(relationship_tokens * 0.5)
        )
        dbt_cost = cost_tracker.calculate_cost(
            "claude-sonnet-4-20250514",
            dbt_gen_input,
            dbt_gen_output
        )
        test_cost = cost_tracker.calculate_cost(
            "claude-sonnet-4-20250514",
            test_gen_tokens,
            int(test_gen_tokens * 0.8)
        )
        model_mix = {
            "schema_analysis": "Sonnet",
            "relationship_detection": "Opus",
            "dbt_generation": "Sonnet",
            "test_generation": "Sonnet",
        }

    total_input = schema_analysis_tokens + relationship_tokens + dbt_gen_input + test_gen_tokens
    total_output = int(
        schema_analysis_tokens * 0.3 +
        relationship_tokens * 0.5 +
        dbt_gen_output +
        test_gen_tokens * 0.8
    )
    total_cost = schema_cost + rel_cost + dbt_cost + test_cost

    return CostEstimateResponse(
        estimated_input_tokens=total_input,
        estimated_output_tokens=total_output,
        estimated_cost=round(total_cost, 4),
        cost_breakdown={
            "schema_analysis": round(schema_cost, 4),
            "relationship_detection": round(rel_cost, 4),
            "dbt_generation": round(dbt_cost, 4),
            "test_generation": round(test_cost, 4),
        },
        recommended_model_mix=model_mix,
    )


@app.get("/costs/pricing")
async def get_pricing_info():
    """Get current Claude API pricing information."""
    return {
        "pricing_per_million_tokens": cost_tracker.PRICING,
        "last_updated": "2024-12",
        "notes": {
            "opus": "Best for complex reasoning and multi-step planning",
            "sonnet": "Balanced performance for most tasks",
            "haiku": "Fast and cost-effective for simple operations",
        },
        "cost_optimization_tips": [
            "Use tiered model routing based on task complexity",
            "Enable prompt caching for repeated system prompts (90% savings)",
            "Batch similar operations together",
            "Set max_tokens limits on responses",
            "Use Haiku for schema extraction and simple parsing",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
