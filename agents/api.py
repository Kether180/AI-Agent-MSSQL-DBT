"""
FastAPI Microservice for AI Agents

This service bridges the Go backend with the Python AI agents.
It exposes REST endpoints that the Go backend calls to:
- Extract MSSQL metadata
- Generate dbt projects
- Run the full LangGraph migration workflow
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our agents
from .mssql_extractor import MSSQLExtractor, extract_mssql_metadata
from .dbt_generator import DBTProjectGenerator, create_dbt_project
from .validation_agent import ValidationAgent, validate_migration, enhance_schema_yml, SourceConnectionInfo
from .dbt_executor import (
    DbtExecutor, WarehouseConnection, WarehouseType,
    DeploymentResult, DeploymentStatus, deploy_to_warehouse
)
from .data_quality_agent import DataQualityAgent, scan_source_data_quality

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS
# =============================================================================

class SourceConnection(BaseModel):
    """Source database connection configuration"""
    type: str
    host: str
    port: int
    database: str
    username: str = ""
    password: str = ""
    use_windows_auth: bool = False


class MigrationStartRequest(BaseModel):
    """Request to start a migration"""
    migration_id: int
    source_connection: SourceConnection
    target_project: str
    target_warehouse: str = "snowflake"
    tables: Optional[List[str]] = None
    include_views: bool = False


class MigrationStatusResponse(BaseModel):
    """Response with migration status"""
    migration_id: int
    status: str
    progress: int
    current_phase: Optional[str] = None
    current_model: Optional[str] = None
    error: Optional[str] = None
    completed_models: int = 0
    total_models: int = 0


class MigrationStatus(str, Enum):
    """Migration status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MigrationState:
    """Internal state for tracking migrations"""
    migration_id: int
    status: MigrationStatus
    progress: int = 0
    current_phase: str = ""
    current_model: str = ""
    error: Optional[str] = None
    completed_models: int = 0
    total_models: int = 0
    metadata: Optional[Dict[str, Any]] = None
    dbt_project_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# =============================================================================
# IN-MEMORY STATE STORAGE
# =============================================================================

# Store for active migrations
migrations_store: Dict[int, MigrationState] = {}
migrations_lock = threading.Lock()


def get_migration(migration_id: int) -> Optional[MigrationState]:
    """Get migration state by ID"""
    with migrations_lock:
        return migrations_store.get(migration_id)


def update_migration(migration_id: int, **kwargs) -> None:
    """Update migration state"""
    with migrations_lock:
        if migration_id in migrations_store:
            state = migrations_store[migration_id]
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)


def create_migration(migration_id: int) -> MigrationState:
    """Create a new migration state"""
    with migrations_lock:
        state = MigrationState(
            migration_id=migration_id,
            status=MigrationStatus.PENDING,
            started_at=datetime.now()
        )
        migrations_store[migration_id] = state
        return state


# =============================================================================
# GO BACKEND CALLBACK
# =============================================================================

GO_BACKEND_URL = os.getenv("GO_BACKEND_URL", "http://localhost:8080")


async def notify_go_backend(
    migration_id: int,
    status: str,
    progress: int,
    error: Optional[str] = None,
    tables_count: Optional[int] = None,
    views_count: Optional[int] = None,
    foreign_keys_count: Optional[int] = None,
    models_generated: Optional[int] = None
):
    """Notify Go backend of migration status update"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "status": status,
                "progress": progress
            }
            if error:
                payload["error"] = error
            if tables_count is not None:
                payload["tables_count"] = tables_count
            if views_count is not None:
                payload["views_count"] = views_count
            if foreign_keys_count is not None:
                payload["foreign_keys_count"] = foreign_keys_count
            if models_generated is not None:
                payload["models_generated"] = models_generated

            await client.patch(
                f"{GO_BACKEND_URL}/api/v1/internal/migrations/{migration_id}/status",
                json=payload,
                timeout=10.0
            )
            logger.info(f"Notified Go backend: migration {migration_id} -> {status} ({progress}%)")
    except Exception as e:
        logger.error(f"Failed to notify Go backend: {e}")


# =============================================================================
# MIGRATION WORKFLOW
# =============================================================================

async def run_migration_workflow(
    migration_id: int,
    source_connection: SourceConnection,
    target_project: str,
    target_warehouse: str,
    tables: Optional[List[str]] = None,
    include_views: bool = False
):
    """
    Run the complete migration workflow.

    Phases:
    1. Extract MSSQL metadata
    2. Generate dbt project
    3. (Future) Run AI analysis with LangGraph
    """
    try:
        # Initialize migration state
        update_migration(
            migration_id,
            status=MigrationStatus.RUNNING,
            progress=0,
            current_phase="initializing"
        )
        await notify_go_backend(migration_id, "running", 0)

        # Phase 1: Extract metadata (0-30%)
        logger.info(f"Migration {migration_id}: Starting metadata extraction")
        update_migration(
            migration_id,
            current_phase="extracting_metadata",
            progress=5
        )
        await notify_go_backend(migration_id, "running", 5)

        try:
            extractor = MSSQLExtractor(
                server=source_connection.host,
                database=source_connection.database,
                username=source_connection.username,
                password=source_connection.password,
                port=source_connection.port,
                trusted_connection=source_connection.use_windows_auth
            )

            # Test connection first
            if not extractor.test_connection():
                raise Exception("Failed to connect to source database")

            update_migration(migration_id, progress=10)
            await notify_go_backend(migration_id, "running", 10)

            # Extract metadata
            metadata = extractor.extract_all(
                include_procedures=False,  # Skip for faster extraction
                include_indexes=False
            )

            total_tables = len(metadata.get('tables', []))
            total_views = len(metadata.get('views', []))
            total_foreign_keys = len(metadata.get('foreign_keys', []))

            update_migration(
                migration_id,
                progress=30,
                total_models=total_tables,
                metadata=metadata
            )
            await notify_go_backend(migration_id, "running", 30)

            logger.info(f"Migration {migration_id}: Extracted {total_tables} tables, {total_views} views, {total_foreign_keys} FKs")

        except Exception as e:
            logger.error(f"Migration {migration_id}: Metadata extraction failed: {e}")
            update_migration(
                migration_id,
                status=MigrationStatus.FAILED,
                error=f"Metadata extraction failed: {str(e)}"
            )
            await notify_go_backend(migration_id, "failed", 30, str(e))
            return

        # Phase 2: Generate dbt project (30-70%)
        logger.info(f"Migration {migration_id}: Generating dbt project")
        update_migration(
            migration_id,
            current_phase="generating_dbt_project",
            progress=35
        )
        await notify_go_backend(migration_id, "running", 35)

        try:
            # Create output directory
            output_base = Path("./dbt_projects")
            output_base.mkdir(parents=True, exist_ok=True)

            project_path = output_base / f"migration_{migration_id}_{target_project}"

            generator = DBTProjectGenerator(
                project_name=target_project,
                output_path=str(project_path),
                target_warehouse=target_warehouse
            )

            result = generator.generate_full_project(metadata)

            update_migration(
                migration_id,
                progress=70,
                dbt_project_path=str(project_path),
                completed_models=total_tables
            )
            await notify_go_backend(migration_id, "running", 70)

            logger.info(f"Migration {migration_id}: Generated dbt project at {project_path}")

        except Exception as e:
            logger.error(f"Migration {migration_id}: dbt generation failed: {e}")
            update_migration(
                migration_id,
                status=MigrationStatus.FAILED,
                error=f"dbt generation failed: {str(e)}"
            )
            await notify_go_backend(migration_id, "failed", 70, str(e))
            return

        # Phase 3: Validation (70-100%)
        logger.info(f"Migration {migration_id}: Validating generated models")
        update_migration(
            migration_id,
            current_phase="validating",
            progress=85
        )
        await notify_go_backend(migration_id, "running", 85)

        # TODO: Add actual validation with dbt compile or AI review
        # For now, just mark as complete
        await asyncio.sleep(1)  # Simulate validation

        # Complete!
        update_migration(
            migration_id,
            status=MigrationStatus.COMPLETED,
            progress=100,
            current_phase="completed",
            completed_at=datetime.now()
        )

        # Count generated models (SQL files in models directory)
        models_count = 0
        if project_path.exists():
            models_dir = project_path / "models"
            if models_dir.exists():
                models_count = len(list(models_dir.rglob("*.sql")))

        await notify_go_backend(
            migration_id,
            "completed",
            100,
            tables_count=total_tables,
            views_count=total_views,
            foreign_keys_count=total_foreign_keys,
            models_generated=models_count
        )

        logger.info(f"Migration {migration_id}: Completed successfully! ({total_tables} tables, {total_views} views, {total_foreign_keys} FKs, {models_count} models generated)")

    except Exception as e:
        logger.error(f"Migration {migration_id}: Unexpected error: {e}", exc_info=True)
        update_migration(
            migration_id,
            status=MigrationStatus.FAILED,
            error=str(e)
        )
        await notify_go_backend(migration_id, "failed", 0, str(e))


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="DataMigrate AI Service",
    description="AI-powered MSSQL to dbt migration service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "datamigrate-ai-service",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/migrations/start")
async def start_migration(
    request: MigrationStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a new migration workflow"""
    migration_id = request.migration_id

    # Check if migration already exists
    existing = get_migration(migration_id)
    if existing and existing.status == MigrationStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Migration {migration_id} is already running"
        )

    # Create migration state
    create_migration(migration_id)

    # Start migration workflow in background
    background_tasks.add_task(
        run_migration_workflow,
        migration_id=migration_id,
        source_connection=request.source_connection,
        target_project=request.target_project,
        target_warehouse=request.target_warehouse,
        tables=request.tables,
        include_views=request.include_views
    )

    logger.info(f"Started migration {migration_id}")

    return {
        "message": "Migration started",
        "migration_id": migration_id
    }


@app.get("/migrations/{migration_id}/status", response_model=MigrationStatusResponse)
async def get_migration_status(migration_id: int):
    """Get the current status of a migration"""
    state = get_migration(migration_id)

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Migration {migration_id} not found"
        )

    return MigrationStatusResponse(
        migration_id=state.migration_id,
        status=state.status.value,
        progress=state.progress,
        current_phase=state.current_phase,
        current_model=state.current_model,
        error=state.error,
        completed_models=state.completed_models,
        total_models=state.total_models
    )


@app.post("/migrations/{migration_id}/stop")
async def stop_migration(migration_id: int):
    """Stop a running migration"""
    state = get_migration(migration_id)

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Migration {migration_id} not found"
        )

    if state.status != MigrationStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Migration {migration_id} is not running"
        )

    update_migration(
        migration_id,
        status=MigrationStatus.FAILED,
        error="Stopped by user"
    )

    return {"message": "Migration stopped", "migration_id": migration_id}


def find_migration_project_path(migration_id: int) -> Optional[Path]:
    """Find the dbt project path for a migration, checking both memory and disk"""
    # First check in-memory state
    state = get_migration(migration_id)
    if state and state.dbt_project_path:
        project_path = Path(state.dbt_project_path)
        if project_path.exists():
            return project_path

    # If not in memory, search for existing project directories on disk
    dbt_projects_dir = Path("dbt_projects")
    if dbt_projects_dir.exists():
        # Look for directories matching the pattern migration_<id>_*
        for dir_path in dbt_projects_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith(f"migration_{migration_id}_"):
                # Found a matching project directory - restore state
                with migrations_lock:
                    if migration_id not in migrations_store:
                        migrations_store[migration_id] = MigrationState(
                            migration_id=migration_id,
                            status=MigrationStatus.COMPLETED,
                            progress=100,
                            dbt_project_path=str(dir_path)
                        )
                    else:
                        migrations_store[migration_id].dbt_project_path = str(dir_path)
                return dir_path

    return None


@app.get("/migrations/{migration_id}/files")
async def get_migration_files(migration_id: int):
    """Get the list of generated dbt files for a migration"""
    project_path = find_migration_project_path(migration_id)

    if not project_path:
        raise HTTPException(
            status_code=404,
            detail=f"No dbt project found for migration {migration_id}"
        )

    # Collect all files
    files = []
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(project_path)
            # Use forward slashes for URL compatibility (important on Windows)
            path_str = relative_path.as_posix()
            files.append({
                "path": path_str,
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": file_path.suffix
            })

    return {
        "migration_id": migration_id,
        "project_path": str(project_path),
        "files": files
    }


@app.get("/migrations/{migration_id}/files/{file_path:path}")
async def get_migration_file_content(migration_id: int, file_path: str):
    """Get the content of a specific dbt file"""
    project_path = find_migration_project_path(migration_id)

    if not project_path:
        raise HTTPException(
            status_code=404,
            detail=f"No dbt project found for migration {migration_id}"
        )

    # Convert forward slashes to OS-appropriate path separators
    normalized_path = file_path.replace('/', os.sep)
    full_path = project_path / normalized_path

    if not full_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}"
        )

    if not full_path.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Not a file: {file_path}"
        )

    try:
        content = full_path.read_text(encoding='utf-8')
        return {
            "path": file_path,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )


@app.get("/migrations/{migration_id}/download")
async def download_migration_project(migration_id: int):
    """Download the entire dbt project as a zip file"""
    import io
    import zipfile
    from fastapi.responses import StreamingResponse

    state = get_migration(migration_id)

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Migration {migration_id} not found"
        )

    if not state.dbt_project_path:
        raise HTTPException(
            status_code=400,
            detail="No dbt project generated yet"
        )

    project_path = Path(state.dbt_project_path)
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail="dbt project directory not found"
        )

    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(project_path)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=migration_{migration_id}_dbt_project.zip"
        }
    )


# =============================================================================
# VALIDATION ENDPOINTS
# =============================================================================

class ValidationRequest(BaseModel):
    """Request to validate a migration"""
    run_dbt_compile: bool = False
    validate_row_counts: bool = False
    validate_data_types: bool = True
    generate_dbt_tests: bool = True
    # Optional source connection for row count validation
    source_host: Optional[str] = None
    source_port: Optional[int] = 1433
    source_database: Optional[str] = None
    source_username: Optional[str] = None
    source_password: Optional[str] = None
    use_windows_auth: bool = False


class ValidationResponse(BaseModel):
    """Validation results"""
    migration_id: int
    project_path: str
    overall_status: str
    summary: Dict[str, Any]
    table_results: List[Dict[str, Any]]
    dbt_tests_generated: int = 0
    row_count_validated: bool = False
    syntax_validated: bool = False


@app.post("/migrations/{migration_id}/validate", response_model=ValidationResponse)
async def validate_migration_endpoint(migration_id: int, request: ValidationRequest = None):
    """
    Validate a completed migration's dbt project.

    Checks:
    - Model files exist for all source tables
    - All columns are present in models
    - Source references are correct
    - Constraint information is preserved
    - Data type mappings are valid
    - SQL linting for common issues
    - Optionally validates row counts from source database
    - Optionally runs dbt compile for syntax validation
    - Generates dbt tests (not_null, unique, relationships)
    """
    # Find the project path
    project_path = find_migration_project_path(migration_id)

    if not project_path:
        raise HTTPException(
            status_code=404,
            detail=f"No dbt project found for migration {migration_id}"
        )

    # Get migration state to retrieve metadata
    state = get_migration(migration_id)

    # If we don't have metadata in memory, try to reconstruct from project files
    source_metadata = None
    if state and state.metadata:
        source_metadata = state.metadata
    else:
        # Try to read sources from _sources.yml to reconstruct basic metadata
        sources_file = project_path / "models" / "staging" / "_sources.yml"
        if sources_file.exists():
            try:
                import yaml
                sources_content = yaml.safe_load(sources_file.read_text())
                tables = []
                for source in sources_content.get('sources', []):
                    for table in source.get('tables', []):
                        table_info = {
                            'name': table.get('name', ''),
                            'schema': 'dbo',
                            'columns': []
                        }
                        # Try to get columns from _schema.yml
                        schema_file = project_path / "models" / "staging" / "_schema.yml"
                        if schema_file.exists():
                            schema_content = yaml.safe_load(schema_file.read_text())
                            for model in schema_content.get('models', []):
                                if model.get('name') == f"stg_{table['name'].lower()}":
                                    for col in model.get('columns', []):
                                        table_info['columns'].append({
                                            'name': col.get('name', ''),
                                            'data_type': 'varchar',  # Default type
                                            'is_nullable': True,
                                            'is_primary_key': 'unique' in col.get('tests', [])
                                        })
                        tables.append(table_info)
                source_metadata = {'tables': tables, 'foreign_keys': [], 'views': []}
            except Exception as e:
                logger.warning(f"Failed to reconstruct metadata: {e}")

    if not source_metadata:
        # Create minimal metadata by scanning model files
        models_dir = project_path / "models" / "staging"
        tables = []
        if models_dir.exists():
            for sql_file in models_dir.glob("stg_*.sql"):
                table_name = sql_file.stem.replace('stg_', '')
                tables.append({
                    'name': table_name,
                    'schema': 'dbo',
                    'columns': []
                })
        source_metadata = {'tables': tables, 'foreign_keys': [], 'views': []}

    # Extract request parameters with defaults
    run_compile = request.run_dbt_compile if request else False
    validate_row_counts = request.validate_row_counts if request else False
    validate_data_types = request.validate_data_types if request else True
    generate_dbt_tests = request.generate_dbt_tests if request else True

    # Build source connection if provided for row count validation
    source_connection = None
    if request and request.source_host and request.source_database:
        source_connection = SourceConnectionInfo(
            host=request.source_host,
            port=request.source_port or 1433,
            database=request.source_database,
            username=request.source_username or "",
            password=request.source_password or "",
            use_windows_auth=request.use_windows_auth
        )
        logger.info(f"Migration {migration_id}: Using source connection for row count validation")

    try:
        validation_result = validate_migration(
            str(project_path),
            source_metadata,
            run_compile=run_compile,
            validate_row_counts=validate_row_counts,
            validate_data_types=validate_data_types,
            generate_dbt_tests=generate_dbt_tests,
            source_connection=source_connection
        )

        # Add migration_id to result
        validation_result['migration_id'] = migration_id

        logger.info(f"Migration {migration_id}: Validation completed - {validation_result['overall_status']} (dbt_tests: {validation_result.get('dbt_tests_generated', 0)}, row_counts: {validation_result.get('row_count_validated', False)})")

        return ValidationResponse(
            migration_id=migration_id,
            project_path=validation_result['project_path'],
            overall_status=validation_result['overall_status'],
            summary=validation_result['summary'],
            table_results=validation_result['table_results'],
            dbt_tests_generated=validation_result.get('dbt_tests_generated', 0),
            row_count_validated=validation_result.get('row_count_validated', False),
            syntax_validated=validation_result.get('syntax_validated', False)
        )

    except Exception as e:
        logger.error(f"Validation failed for migration {migration_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@app.post("/migrations/{migration_id}/enhance-schema")
async def enhance_schema_endpoint(migration_id: int):
    """
    Generate enhanced schema.yml with column-level tests based on source constraints.

    This adds:
    - not_null tests for non-nullable columns
    - unique tests for primary key columns
    - relationships tests for foreign key columns
    """
    project_path = find_migration_project_path(migration_id)

    if not project_path:
        raise HTTPException(
            status_code=404,
            detail=f"No dbt project found for migration {migration_id}"
        )

    # Get source metadata
    state = get_migration(migration_id)
    if not state or not state.metadata:
        raise HTTPException(
            status_code=400,
            detail="Source metadata not available. Run validation first or re-run migration."
        )

    try:
        enhanced_yaml = enhance_schema_yml(str(project_path), state.metadata)

        # Write the enhanced schema
        schema_path = project_path / "models" / "staging" / "_schema.yml"
        schema_path.write_text(enhanced_yaml)

        logger.info(f"Migration {migration_id}: Enhanced schema.yml generated")

        return {
            "message": "Enhanced schema.yml generated successfully",
            "path": str(schema_path),
            "content": enhanced_yaml
        }

    except Exception as e:
        logger.error(f"Failed to enhance schema for migration {migration_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate enhanced schema: {str(e)}"
        )


# =============================================================================
# AI SUPPORT CHAT
# =============================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    sources: Optional[List[str]] = None


# Knowledge base for the support assistant
KNOWLEDGE_BASE = {
    "migration": """DataMigrate AI helps you migrate MSSQL databases to dbt projects.
To create a migration:
1. Go to Migrations > New Migration
2. Configure your MSSQL connection (host, database, credentials)
3. Select tables to migrate
4. Choose your target warehouse (Snowflake, BigQuery, Fabric, etc.)
5. Configure dbt project settings
6. Start the migration - AI will generate models, tests, and documentation.""",

    "connection": """Database connections in DataMigrate AI:
- SQL Server Authentication: Use username/password
- Windows Authentication: Use trusted connection (no password needed)
- Default port: 1433
- Ensure SQL Server allows remote connections
- Check firewall rules for port access
Go to Settings > Connections to manage your database connections.""",

    "dbt": """dbt (data build tool) models generated by DataMigrate AI:
- Staging models: Raw data transformations
- Intermediate models: Business logic
- Tests: Data quality checks (unique, not_null, relationships)
- Documentation: Auto-generated from schema metadata
- Sources: YAML definitions for source tables
Target warehouses supported: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",

    "agent": """AI Agents available in DataMigrate AI:
1. DataPrep Agent: Data profiling, deduplication, outlier detection
2. ML Fine-Tuning Agent: Optimize transformations using machine learning
3. Data Quality Agent: Validate data integrity and quality
4. Documentation Agent: Generate comprehensive documentation
5. BI Agent: Business intelligence and analytics
Access agents from the Dashboard or navigate to /agents.""",

    "error": """Common troubleshooting steps:
1. Connection errors: Verify credentials, check network/firewall
2. Permission errors: Ensure user has SELECT permissions on tables
3. Timeout errors: Consider migrating fewer tables at once
4. Migration failures: Check logs in Migration Details view
For persistent issues, check the detailed logs or contact support.""",

    "default": """I'm your DataMigrate AI Support Assistant. I can help with:
- Creating and managing migrations
- Database connection configuration
- Understanding dbt models and transformations
- Using AI agents for data preparation
- Troubleshooting common issues
What would you like to know more about?"""
}


def get_ai_response(message: str, history: Optional[List[ChatMessage]] = None) -> str:
    """
    Generate AI response based on user message.

    In production, this would use the RAG service with Claude/OpenAI.
    For now, uses keyword matching with knowledge base.
    """
    lower_message = message.lower()

    # Try to import and use RAG service if available
    try:
        from .rag_service_v2 import get_rag_service_v2
        rag = get_rag_service_v2()

        # Build context from RAG
        context = rag.build_context(message)

        if context:
            # In production, send to Claude with context
            # For now, return knowledge-based response
            pass
    except Exception as e:
        logger.warning(f"RAG service not available: {e}")

    # Keyword-based response selection
    if any(word in lower_message for word in ['migration', 'migrate', 'create', 'new migration']):
        return KNOWLEDGE_BASE["migration"]

    if any(word in lower_message for word in ['connect', 'connection', 'database', 'mssql', 'sql server', 'credentials']):
        return KNOWLEDGE_BASE["connection"]

    if any(word in lower_message for word in ['dbt', 'model', 'transformation', 'staging', 'warehouse']):
        return KNOWLEDGE_BASE["dbt"]

    if any(word in lower_message for word in ['agent', 'ai', 'dataprep', 'fine-tun', 'quality']):
        return KNOWLEDGE_BASE["agent"]

    if any(word in lower_message for word in ['error', 'fail', 'problem', 'issue', 'help', 'trouble']):
        return KNOWLEDGE_BASE["error"]

    return KNOWLEDGE_BASE["default"]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI Support Chat endpoint.

    Uses RAG service when available, falls back to knowledge base.
    """
    try:
        response = get_ai_response(request.message, request.history)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            response="I apologize, but I'm having trouble processing your request. Please try again or check the Documentation section for help."
        )


# =============================================================================
# WAREHOUSE DEPLOYMENT ENDPOINTS
# =============================================================================

class WarehouseConnectionRequest(BaseModel):
    """Warehouse connection configuration"""
    warehouse_type: str  # snowflake, bigquery, databricks
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    # BigQuery
    project: Optional[str] = None
    dataset: Optional[str] = None
    keyfile: Optional[str] = None
    keyfile_json: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    # Databricks
    host: Optional[str] = None
    http_path: Optional[str] = None
    token: Optional[str] = None
    catalog: Optional[str] = None


class DeployRequest(BaseModel):
    """Request to deploy a migration to a warehouse"""
    connection: WarehouseConnectionRequest
    run_tests: bool = True
    full_refresh: bool = False


class DeployResponse(BaseModel):
    """Deployment result response"""
    deployment_id: Optional[int] = None
    status: str
    dbt_run: Optional[Dict[str, Any]] = None
    dbt_test: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# Store for deployment results
deployments_store: Dict[int, Dict[str, Any]] = {}
deployment_counter = [0]  # Using list to allow mutation in nested function


@app.post("/migrations/{migration_id}/deploy", response_model=DeployResponse)
async def deploy_migration(migration_id: int, request: DeployRequest, background_tasks: BackgroundTasks):
    """
    Deploy a completed migration to a target data warehouse.

    This executes:
    1. dbt run - Creates tables/views in the warehouse
    2. dbt test - Validates data quality (optional)

    Supports: Snowflake, BigQuery, Databricks
    """
    # Find the project path
    project_path = find_migration_project_path(migration_id)

    if not project_path:
        raise HTTPException(
            status_code=404,
            detail=f"No dbt project found for migration {migration_id}"
        )

    # Generate deployment ID
    deployment_counter[0] += 1
    deployment_id = deployment_counter[0]

    # Build connection config
    conn = request.connection
    connection_config = {
        "account": conn.account,
        "warehouse": conn.warehouse,
        "database": conn.database,
        "schema": conn.schema_name,
        "username": conn.username,
        "password": conn.password,
        "role": conn.role,
        "project": conn.project,
        "dataset": conn.dataset,
        "keyfile": conn.keyfile,
        "keyfile_json": conn.keyfile_json,
        "location": conn.location,
        "host": conn.host,
        "http_path": conn.http_path,
        "token": conn.token,
        "catalog": conn.catalog,
    }

    # Initialize deployment record
    deployments_store[deployment_id] = {
        "deployment_id": deployment_id,
        "migration_id": migration_id,
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

    logger.info(f"Starting deployment {deployment_id} for migration {migration_id} to {conn.warehouse_type}")

    # Run deployment in background
    async def run_deployment():
        try:
            result = deploy_to_warehouse(
                project_path=str(project_path),
                warehouse_type=conn.warehouse_type,
                connection_config=connection_config,
                run_tests=request.run_tests,
                full_refresh=request.full_refresh
            )

            deployments_store[deployment_id].update(result)
            deployments_store[deployment_id]["completed_at"] = datetime.now().isoformat()

            logger.info(f"Deployment {deployment_id} completed: {result.get('status')}")

        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}", exc_info=True)
            deployments_store[deployment_id]["status"] = "failed"
            deployments_store[deployment_id]["error"] = str(e)
            deployments_store[deployment_id]["completed_at"] = datetime.now().isoformat()

    background_tasks.add_task(run_deployment)

    return DeployResponse(
        deployment_id=deployment_id,
        status="running",
        started_at=deployments_store[deployment_id]["started_at"]
    )


@app.get("/migrations/{migration_id}/deployments/{deployment_id}", response_model=DeployResponse)
async def get_deployment_status(migration_id: int, deployment_id: int):
    """Get the status of a deployment"""
    if deployment_id not in deployments_store:
        raise HTTPException(
            status_code=404,
            detail=f"Deployment {deployment_id} not found"
        )

    deployment = deployments_store[deployment_id]

    if deployment.get("migration_id") != migration_id:
        raise HTTPException(
            status_code=400,
            detail=f"Deployment {deployment_id} does not belong to migration {migration_id}"
        )

    return DeployResponse(
        deployment_id=deployment.get("deployment_id"),
        status=deployment.get("status", "unknown"),
        dbt_run=deployment.get("dbt_run"),
        dbt_test=deployment.get("dbt_test"),
        error=deployment.get("error"),
        started_at=deployment.get("started_at"),
        completed_at=deployment.get("completed_at")
    )


@app.get("/migrations/{migration_id}/deployments")
async def list_deployments(migration_id: int):
    """List all deployments for a migration"""
    deployments = [
        d for d in deployments_store.values()
        if d.get("migration_id") == migration_id
    ]

    return {
        "migration_id": migration_id,
        "deployments": deployments
    }


# =============================================================================
# DATA QUALITY SCANNING ENDPOINTS
# =============================================================================

class DataQualityScanRequest(BaseModel):
    """Request to scan source database for data quality issues"""
    host: str
    port: int = 1433
    database: str
    username: str = ""
    password: str = ""
    use_windows_auth: bool = False
    tables: Optional[List[str]] = None
    sample_size: int = 10000


class DataQualityScanResponse(BaseModel):
    """Data quality scan results"""
    database_name: str
    server: str
    tables_scanned: int
    total_rows_scanned: int
    total_issues: int
    critical_issues: int
    error_issues: int
    warning_issues: int
    info_issues: int
    overall_score: float
    scan_started_at: Optional[str] = None
    scan_completed_at: Optional[str] = None
    issues_by_severity: Dict[str, List[Dict[str, Any]]]
    tables: List[Dict[str, Any]]


@app.post("/data-quality/scan", response_model=DataQualityScanResponse)
async def scan_data_quality(request: DataQualityScanRequest):
    """
    Scan source MSSQL database for data quality issues.

    This helps users understand what problems exist in their source data
    BEFORE migration, so they can make informed decisions.

    Checks include:
    - Null value analysis (completeness)
    - Duplicate detection (uniqueness)
    - Foreign key violations (referential integrity)
    - Missing primary keys
    - Constant/low-cardinality columns

    Returns a quality score (0-100) and detailed issue report.
    """
    try:
        result = scan_source_data_quality(
            server=request.host,
            database=request.database,
            username=request.username,
            password=request.password,
            port=request.port,
            use_windows_auth=request.use_windows_auth,
            tables=request.tables,
            sample_size=request.sample_size
        )

        logger.info(f"Data quality scan completed: {result['tables_scanned']} tables, score: {result['overall_score']}")

        return DataQualityScanResponse(**result)

    except Exception as e:
        logger.error(f"Data quality scan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Data quality scan failed: {str(e)}"
        )


@app.post("/connections/{connection_id}/scan-quality")
async def scan_connection_data_quality(connection_id: int):
    """
    Scan a saved connection for data quality issues.

    This endpoint would integrate with the Go backend to fetch
    connection details and run a scan. For now, returns a placeholder.
    """
    # In production, this would:
    # 1. Fetch connection details from Go backend
    # 2. Decrypt password
    # 3. Run scan_source_data_quality
    # 4. Return results

    return {
        "message": "This endpoint requires integration with Go backend",
        "connection_id": connection_id,
        "status": "not_implemented"
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the FastAPI server"""
    port = int(os.getenv("AI_SERVICE_PORT", "8081"))
    host = os.getenv("AI_SERVICE_HOST", "0.0.0.0")

    logger.info(f"Starting AI Service on {host}:{port}")

    uvicorn.run(
        "agents.api:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development"
    )


if __name__ == "__main__":
    main()
