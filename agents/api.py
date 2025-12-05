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

# Try to import anthropic for Claude AI chat
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

# Initialize Anthropic client for chat
anthropic_client = None
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
    language: str = "en"  # Language code: en, da, es, pt, no, sv, de


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    sources: Optional[List[str]] = None


# Multilingual knowledge base for the support assistant
KNOWLEDGE_BASE = {
    "en": {
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
        "security": """Your data is protected with enterprise-grade security:
- All data is encrypted in transit (TLS 1.3) and at rest (AES-256)
- Database credentials are encrypted and never stored in plain text
- JWT authentication with secure token management
- Role-based access control (RBAC)
- Audit logging of all operations
- No data is shared with third parties
- SOC 2 Type II compliant infrastructure
- Regular security audits and penetration testing""",
        "default": """I'm your DataMigrate AI Support Assistant. I can help with:
- Creating and managing migrations
- Database connection configuration
- Understanding dbt models and transformations
- Using AI agents for data preparation
- Troubleshooting common issues
What would you like to know more about?"""
    },
    "da": {
        "migration": """DataMigrate AI hjælper dig med at migrere MSSQL-databaser til dbt-projekter.
For at oprette en migrering:
1. Gå til Migreringer > Ny Migrering
2. Konfigurer din MSSQL-forbindelse (host, database, legitimationsoplysninger)
3. Vælg tabeller til migrering
4. Vælg dit mål-warehouse (Snowflake, BigQuery, Fabric, osv.)
5. Konfigurer dbt-projektindstillinger
6. Start migreringen - AI genererer modeller, tests og dokumentation.""",
        "connection": """Databaseforbindelser i DataMigrate AI:
- SQL Server-godkendelse: Brug brugernavn/adgangskode
- Windows-godkendelse: Brug betroet forbindelse (ingen adgangskode påkrævet)
- Standardport: 1433
- Sørg for at SQL Server tillader fjernforbindelser
- Tjek firewall-regler for portadgang
Gå til Indstillinger > Forbindelser for at administrere dine databaseforbindelser.""",
        "dbt": """dbt (data build tool) modeller genereret af DataMigrate AI:
- Staging-modeller: Rå datatransformationer
- Mellemliggende modeller: Forretningslogik
- Tests: Datakvalitetstjek (unik, ikke_null, relationer)
- Dokumentation: Auto-genereret fra skemametadata
- Kilder: YAML-definitioner for kildetabeller
Understøttede mål-warehouses: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """AI-agenter tilgængelige i DataMigrate AI:
1. DataPrep Agent: Dataprofilering, deduplikering, outlier-detektion
2. ML Fine-Tuning Agent: Optimer transformationer ved hjælp af maskinlæring
3. Data Quality Agent: Valider dataintegritet og -kvalitet
4. Documentation Agent: Generer omfattende dokumentation
5. BI Agent: Business intelligence og analyse
Få adgang til agenter fra Dashboard eller naviger til /agents.""",
        "error": """Almindelige fejlfindingstrin:
1. Forbindelsesfejl: Bekræft legitimationsoplysninger, tjek netværk/firewall
2. Tilladelsesfejl: Sørg for at brugeren har SELECT-tilladelser på tabeller
3. Timeout-fejl: Overvej at migrere færre tabeller ad gangen
4. Migreringsfejl: Tjek logs i Migration Details-visningen
Ved vedvarende problemer, tjek de detaljerede logs eller kontakt support.""",
        "security": """Dine data er beskyttet med sikkerhed på virksomhedsniveau:
- Alle data er krypteret under transport (TLS 1.3) og i hvile (AES-256)
- Database-legitimationsoplysninger er krypteret og gemmes aldrig i klartekst
- JWT-godkendelse med sikker token-håndtering
- Rollebaseret adgangskontrol (RBAC)
- Revisionslogning af alle operationer
- Ingen data deles med tredjeparter
- SOC 2 Type II-kompatibel infrastruktur
- Regelmæssige sikkerhedsrevisioner og penetrationstest""",
        "default": """Jeg er din DataMigrate AI Support Assistent. Jeg kan hjælpe med:
- Oprettelse og administration af migreringer
- Konfiguration af databaseforbindelse
- Forståelse af dbt-modeller og transformationer
- Brug af AI-agenter til dataforberedelse
- Fejlfinding af almindelige problemer
Hvad vil du gerne vide mere om?"""
    },
    "de": {
        "migration": """DataMigrate AI hilft Ihnen bei der Migration von MSSQL-Datenbanken zu dbt-Projekten.
Um eine Migration zu erstellen:
1. Gehen Sie zu Migrationen > Neue Migration
2. Konfigurieren Sie Ihre MSSQL-Verbindung (Host, Datenbank, Anmeldedaten)
3. Wählen Sie zu migrierende Tabellen aus
4. Wählen Sie Ihr Ziel-Warehouse (Snowflake, BigQuery, Fabric, usw.)
5. Konfigurieren Sie dbt-Projekteinstellungen
6. Starten Sie die Migration - KI generiert Modelle, Tests und Dokumentation.""",
        "connection": """Datenbankverbindungen in DataMigrate AI:
- SQL Server-Authentifizierung: Benutzername/Passwort verwenden
- Windows-Authentifizierung: Vertrauenswürdige Verbindung nutzen (kein Passwort erforderlich)
- Standard-Port: 1433
- Stellen Sie sicher, dass SQL Server Remoteverbindungen erlaubt
- Firewall-Regeln für Portzugriff prüfen
Gehen Sie zu Einstellungen > Verbindungen, um Ihre Datenbankverbindungen zu verwalten.""",
        "dbt": """dbt (data build tool) Modelle, generiert von DataMigrate AI:
- Staging-Modelle: Rohdaten-Transformationen
- Zwischenmodelle: Geschäftslogik
- Tests: Datenqualitätsprüfungen (unique, not_null, Beziehungen)
- Dokumentation: Auto-generiert aus Schema-Metadaten
- Quellen: YAML-Definitionen für Quelltabellen
Unterstützte Ziel-Warehouses: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """KI-Agenten in DataMigrate AI verfügbar:
1. DataPrep Agent: Datenprofilierung, Deduplizierung, Ausreißer-Erkennung
2. ML Fine-Tuning Agent: Transformationen mit maschinellem Lernen optimieren
3. Data Quality Agent: Datenintegrität und -qualität validieren
4. Documentation Agent: Umfassende Dokumentation generieren
5. BI Agent: Business Intelligence und Analysen
Zugriff auf Agenten über das Dashboard oder navigieren Sie zu /agents.""",
        "error": """Häufige Fehlerbehebungsschritte:
1. Verbindungsfehler: Anmeldedaten überprüfen, Netzwerk/Firewall prüfen
2. Berechtigungsfehler: Sicherstellen, dass Benutzer SELECT-Berechtigungen für Tabellen hat
3. Timeout-Fehler: Erwägen Sie, weniger Tabellen gleichzeitig zu migrieren
4. Migrationsfehler: Logs in der Migrations-Detailansicht prüfen
Bei anhaltenden Problemen, detaillierte Logs prüfen oder Support kontaktieren.""",
        "security": """Ihre Daten sind mit Enterprise-Sicherheit geschützt:
- Alle Daten sind während der Übertragung (TLS 1.3) und im Ruhezustand (AES-256) verschlüsselt
- Datenbank-Anmeldedaten sind verschlüsselt und werden nie im Klartext gespeichert
- JWT-Authentifizierung mit sicherer Token-Verwaltung
- Rollenbasierte Zugriffskontrolle (RBAC)
- Audit-Protokollierung aller Operationen
- Keine Daten werden mit Dritten geteilt
- SOC 2 Type II-konforme Infrastruktur
- Regelmäßige Sicherheitsaudits und Penetrationstests""",
        "default": """Ich bin Ihr DataMigrate AI Support-Assistent. Ich kann helfen bei:
- Erstellen und Verwalten von Migrationen
- Konfiguration von Datenbankverbindungen
- Verstehen von dbt-Modellen und Transformationen
- Nutzung von KI-Agenten für Datenvorbereitung
- Fehlerbehebung bei häufigen Problemen
Worüber möchten Sie mehr erfahren?"""
    },
    "es": {
        "migration": """DataMigrate AI te ayuda a migrar bases de datos MSSQL a proyectos dbt.
Para crear una migración:
1. Ve a Migraciones > Nueva Migración
2. Configura tu conexión MSSQL (host, base de datos, credenciales)
3. Selecciona las tablas a migrar
4. Elige tu almacén de destino (Snowflake, BigQuery, Fabric, etc.)
5. Configura los ajustes del proyecto dbt
6. Inicia la migración - la IA generará modelos, tests y documentación.""",
        "connection": """Conexiones de base de datos en DataMigrate AI:
- Autenticación SQL Server: Usa usuario/contraseña
- Autenticación Windows: Usa conexión de confianza (sin contraseña)
- Puerto por defecto: 1433
- Asegúrate de que SQL Server permite conexiones remotas
- Verifica las reglas del firewall para acceso al puerto
Ve a Configuración > Conexiones para gestionar tus conexiones de base de datos.""",
        "dbt": """Modelos dbt (data build tool) generados por DataMigrate AI:
- Modelos staging: Transformaciones de datos sin procesar
- Modelos intermedios: Lógica de negocio
- Tests: Verificaciones de calidad de datos (unique, not_null, relaciones)
- Documentación: Auto-generada desde metadatos del esquema
- Fuentes: Definiciones YAML para tablas de origen
Almacenes destino soportados: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """Agentes de IA disponibles en DataMigrate AI:
1. DataPrep Agent: Perfilado de datos, deduplicación, detección de outliers
2. ML Fine-Tuning Agent: Optimizar transformaciones usando aprendizaje automático
3. Data Quality Agent: Validar integridad y calidad de datos
4. Documentation Agent: Generar documentación completa
5. BI Agent: Business intelligence y análisis
Accede a los agentes desde el Dashboard o navega a /agents.""",
        "error": """Pasos comunes de solución de problemas:
1. Errores de conexión: Verificar credenciales, revisar red/firewall
2. Errores de permisos: Asegurar que el usuario tiene permisos SELECT en las tablas
3. Errores de timeout: Considera migrar menos tablas a la vez
4. Fallos de migración: Revisa los logs en la vista de Detalles de Migración
Para problemas persistentes, revisa los logs detallados o contacta soporte.""",
        "security": """Tus datos están protegidos con seguridad de nivel empresarial:
- Todos los datos están cifrados en tránsito (TLS 1.3) y en reposo (AES-256)
- Las credenciales de base de datos están cifradas y nunca se almacenan en texto plano
- Autenticación JWT con gestión segura de tokens
- Control de acceso basado en roles (RBAC)
- Registro de auditoría de todas las operaciones
- No se comparten datos con terceros
- Infraestructura compatible con SOC 2 Type II
- Auditorías de seguridad regulares y pruebas de penetración""",
        "default": """Soy tu Asistente de Soporte DataMigrate AI. Puedo ayudarte con:
- Crear y gestionar migraciones
- Configuración de conexiones de base de datos
- Entender modelos dbt y transformaciones
- Usar agentes de IA para preparación de datos
- Solucionar problemas comunes
¿Qué te gustaría saber más?"""
    },
    "pt": {
        "migration": """DataMigrate AI ajuda você a migrar bancos de dados MSSQL para projetos dbt.
Para criar uma migração:
1. Vá para Migrações > Nova Migração
2. Configure sua conexão MSSQL (host, banco de dados, credenciais)
3. Selecione as tabelas para migrar
4. Escolha seu warehouse de destino (Snowflake, BigQuery, Fabric, etc.)
5. Configure as configurações do projeto dbt
6. Inicie a migração - a IA gerará modelos, testes e documentação.""",
        "connection": """Conexões de banco de dados no DataMigrate AI:
- Autenticação SQL Server: Use usuário/senha
- Autenticação Windows: Use conexão confiável (sem senha necessária)
- Porta padrão: 1433
- Certifique-se de que o SQL Server permite conexões remotas
- Verifique as regras do firewall para acesso à porta
Vá para Configurações > Conexões para gerenciar suas conexões de banco de dados.""",
        "dbt": """Modelos dbt (data build tool) gerados pelo DataMigrate AI:
- Modelos de staging: Transformações de dados brutos
- Modelos intermediários: Lógica de negócios
- Testes: Verificações de qualidade de dados (unique, not_null, relacionamentos)
- Documentação: Auto-gerada a partir de metadados do schema
- Fontes: Definições YAML para tabelas de origem
Warehouses de destino suportados: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """Agentes de IA disponíveis no DataMigrate AI:
1. DataPrep Agent: Perfilamento de dados, deduplicação, detecção de outliers
2. ML Fine-Tuning Agent: Otimizar transformações usando aprendizado de máquina
3. Data Quality Agent: Validar integridade e qualidade de dados
4. Documentation Agent: Gerar documentação abrangente
5. BI Agent: Business intelligence e análises
Acesse os agentes pelo Dashboard ou navegue para /agents.""",
        "error": """Passos comuns de solução de problemas:
1. Erros de conexão: Verificar credenciais, checar rede/firewall
2. Erros de permissão: Garantir que o usuário tem permissões SELECT nas tabelas
3. Erros de timeout: Considere migrar menos tabelas de cada vez
4. Falhas de migração: Verifique os logs na visualização de Detalhes da Migração
Para problemas persistentes, verifique os logs detalhados ou contate o suporte.""",
        "security": """Seus dados são protegidos com segurança de nível empresarial:
- Todos os dados são criptografados em trânsito (TLS 1.3) e em repouso (AES-256)
- Credenciais de banco de dados são criptografadas e nunca armazenadas em texto simples
- Autenticação JWT com gerenciamento seguro de tokens
- Controle de acesso baseado em funções (RBAC)
- Registro de auditoria de todas as operações
- Nenhum dado é compartilhado com terceiros
- Infraestrutura compatível com SOC 2 Type II
- Auditorias de segurança regulares e testes de penetração""",
        "default": """Sou seu Assistente de Suporte DataMigrate AI. Posso ajudar com:
- Criar e gerenciar migrações
- Configuração de conexões de banco de dados
- Entender modelos dbt e transformações
- Usar agentes de IA para preparação de dados
- Solucionar problemas comuns
O que você gostaria de saber mais?"""
    },
    "no": {
        "migration": """DataMigrate AI hjelper deg med å migrere MSSQL-databaser til dbt-prosjekter.
For å opprette en migrering:
1. Gå til Migreringer > Ny Migrering
2. Konfigurer MSSQL-tilkoblingen din (host, database, legitimasjon)
3. Velg tabeller for migrering
4. Velg mål-warehouse (Snowflake, BigQuery, Fabric, osv.)
5. Konfigurer dbt-prosjektinnstillinger
6. Start migreringen - AI genererer modeller, tester og dokumentasjon.""",
        "connection": """Databasetilkoblinger i DataMigrate AI:
- SQL Server-autentisering: Bruk brukernavn/passord
- Windows-autentisering: Bruk betrodd tilkobling (ingen passord nødvendig)
- Standardport: 1433
- Sørg for at SQL Server tillater fjerntilkoblinger
- Sjekk brannmurregler for porttilgang
Gå til Innstillinger > Tilkoblinger for å administrere databasetilkoblingene dine.""",
        "dbt": """dbt (data build tool) modeller generert av DataMigrate AI:
- Staging-modeller: Rådatatransformasjoner
- Mellommodeller: Forretningslogikk
- Tester: Datakvalitetssjekker (unik, ikke_null, relasjoner)
- Dokumentasjon: Auto-generert fra skjemametadata
- Kilder: YAML-definisjoner for kildetabeller
Støttede mål-warehouses: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """AI-agenter tilgjengelig i DataMigrate AI:
1. DataPrep Agent: Dataprofilering, deduplisering, outlier-deteksjon
2. ML Fine-Tuning Agent: Optimaliser transformasjoner med maskinlæring
3. Data Quality Agent: Valider dataintegritet og -kvalitet
4. Documentation Agent: Generer omfattende dokumentasjon
5. BI Agent: Business intelligence og analyse
Få tilgang til agenter fra Dashboard eller naviger til /agents.""",
        "error": """Vanlige feilsøkingstrinn:
1. Tilkoblingsfeil: Bekreft legitimasjon, sjekk nettverk/brannmur
2. Tillatelsesfeil: Sørg for at brukeren har SELECT-tillatelser på tabeller
3. Timeout-feil: Vurder å migrere færre tabeller om gangen
4. Migreringsfeil: Sjekk logger i Migreringsdetaljer-visningen
Ved vedvarende problemer, sjekk de detaljerte loggene eller kontakt support.""",
        "security": """Dataene dine er beskyttet med sikkerhet på bedriftsnivå:
- Alle data er kryptert under overføring (TLS 1.3) og i hvile (AES-256)
- Database-legitimasjon er kryptert og lagres aldri i klartekst
- JWT-autentisering med sikker token-håndtering
- Rollebasert tilgangskontroll (RBAC)
- Revisjonslogging av alle operasjoner
- Ingen data deles med tredjeparter
- SOC 2 Type II-kompatibel infrastruktur
- Regelmessige sikkerhetsrevisjoner og penetrasjonstester""",
        "default": """Jeg er din DataMigrate AI Support-assistent. Jeg kan hjelpe med:
- Opprette og administrere migreringer
- Konfigurering av databasetilkobling
- Forstå dbt-modeller og transformasjoner
- Bruke AI-agenter for dataforberedelse
- Feilsøke vanlige problemer
Hva vil du vite mer om?"""
    },
    "sv": {
        "migration": """DataMigrate AI hjälper dig att migrera MSSQL-databaser till dbt-projekt.
För att skapa en migrering:
1. Gå till Migreringar > Ny Migrering
2. Konfigurera din MSSQL-anslutning (host, databas, inloggningsuppgifter)
3. Välj tabeller att migrera
4. Välj ditt mål-warehouse (Snowflake, BigQuery, Fabric, etc.)
5. Konfigurera dbt-projektinställningar
6. Starta migreringen - AI genererar modeller, tester och dokumentation.""",
        "connection": """Databasanslutningar i DataMigrate AI:
- SQL Server-autentisering: Använd användarnamn/lösenord
- Windows-autentisering: Använd betrodd anslutning (inget lösenord krävs)
- Standardport: 1433
- Se till att SQL Server tillåter fjärranslutningar
- Kontrollera brandväggsregler för portåtkomst
Gå till Inställningar > Anslutningar för att hantera dina databasanslutningar.""",
        "dbt": """dbt (data build tool) modeller genererade av DataMigrate AI:
- Staging-modeller: Rådatatransformationer
- Mellanmodeller: Affärslogik
- Tester: Datakvalitetskontroller (unik, inte_null, relationer)
- Dokumentation: Auto-genererad från schemametadata
- Källor: YAML-definitioner för källtabeller
Stödda mål-warehouses: Snowflake, BigQuery, Microsoft Fabric, Databricks, Redshift.""",
        "agent": """AI-agenter tillgängliga i DataMigrate AI:
1. DataPrep Agent: Dataprofilering, deduplicering, outlier-detektering
2. ML Fine-Tuning Agent: Optimera transformationer med maskininlärning
3. Data Quality Agent: Validera dataintegritet och kvalitet
4. Documentation Agent: Generera omfattande dokumentation
5. BI Agent: Business intelligence och analys
Åtkomst till agenter från Dashboard eller navigera till /agents.""",
        "error": """Vanliga felsökningssteg:
1. Anslutningsfel: Verifiera inloggningsuppgifter, kontrollera nätverk/brandvägg
2. Behörighetsfel: Se till att användaren har SELECT-behörigheter på tabeller
3. Timeout-fel: Överväg att migrera färre tabeller åt gången
4. Migreringsfel: Kontrollera loggar i Migreringsdetaljer-vyn
Vid ihållande problem, kontrollera de detaljerade loggarna eller kontakta support.""",
        "security": """Dina data skyddas med säkerhet på företagsnivå:
- All data är krypterad under överföring (TLS 1.3) och i vila (AES-256)
- Databasuppgifter är krypterade och lagras aldrig i klartext
- JWT-autentisering med säker token-hantering
- Rollbaserad åtkomstkontroll (RBAC)
- Revisionsloggning av alla operationer
- Ingen data delas med tredje part
- SOC 2 Type II-kompatibel infrastruktur
- Regelbundna säkerhetsrevisioner och penetrationstester""",
        "default": """Jag är din DataMigrate AI Support-assistent. Jag kan hjälpa med:
- Skapa och hantera migreringar
- Konfigurering av databasanslutning
- Förstå dbt-modeller och transformationer
- Använda AI-agenter för dataförberedelse
- Felsöka vanliga problem
Vad vill du veta mer om?"""
    }
}


def get_claude_response(message: str, history: Optional[List[ChatMessage]], language: str) -> Optional[str]:
    """
    Get response from Claude AI with DataMigrate context and multilingual support.
    Returns None if Claude is not available.
    """
    if not anthropic_client:
        return None

    # Language-specific instructions
    language_instructions = {
        "en": "Respond in English.",
        "es": "Responde en español.",
        "da": "Svar på dansk.",
        "de": "Antworte auf Deutsch.",
        "pt": "Responda em português.",
        "no": "Svar på norsk.",
        "sv": "Svara på svenska."
    }

    lang_instruction = language_instructions.get(language, language_instructions["en"])

    system_prompt = f"""You are the AI Support Assistant for DataMigrate AI, a platform that helps migrate MSSQL databases to dbt projects.

{lang_instruction}

## About DataMigrate AI
DataMigrate AI is an enterprise platform that automates database migrations from Microsoft SQL Server to modern data warehouses using AI-powered dbt project generation.

## Services & Features
1. **Automated Migration**: Convert MSSQL databases to production-ready dbt projects
2. **AI Agents**:
   - DataPrep Agent: Data profiling, deduplication, outlier detection
   - ML Fine-Tuning Agent: Optimize transformations using machine learning
   - Data Quality Agent: Validate data integrity and quality
   - Documentation Agent: Auto-generate comprehensive documentation
   - BI Agent: Business intelligence and analytics
3. **Supported Target Warehouses**: Snowflake, Google BigQuery, Microsoft Fabric, Databricks, Amazon Redshift
4. **Database Connections**: SQL Server Authentication, Windows Authentication, Azure AD

## Pricing
We offer flexible pricing plans tailored to your specific needs:
- **Free Trial**: Start with a 14-day free trial to explore the platform
- **Starter, Professional, and Enterprise plans** are available with different features

For detailed pricing information and to find the best plan for your needs, please contact our sales team:
- Email: sales@datamigrate.ai
- Phone: +45 6127 5393
- Or click "Request Callback" in the chat to schedule a call

We'll be happy to discuss your requirements and provide a personalized quote.

## Security
- Enterprise-grade security with TLS 1.3 and AES-256 encryption
- Database credentials encrypted, never stored in plain text
- JWT authentication with secure token management
- Role-based access control (RBAC)
- Audit logging of all operations
- SOC 2 Type II compliant infrastructure
- No data shared with third parties

## Data Types Supported
All SQL Server data types: VARCHAR, NVARCHAR, INT, BIGINT, DECIMAL, FLOAT, DATE, DATETIME, BIT, VARBINARY, IMAGE, TEXT, NTEXT, XML, spatial types, and custom user-defined types.

## Contact Information
- Email: support@datamigrate.ai
- Phone: +45 6127 5393
- Website: datamigrate.ai

Be helpful, concise, and friendly. Answer any questions about our services, pricing, features, or technical capabilities."""

    # Build messages for Claude
    messages = []

    # Add conversation history if provided
    if history:
        for msg in history:
            messages.append({
                "role": msg.role if msg.role in ["user", "assistant"] else "user",
                "content": msg.content
            })

    # Add current message
    messages.append({"role": "user", "content": message})

    try:
        logger.info(f"Sending request to Claude API (language: {language})...")
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        logger.info("Claude API responded successfully")
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None


def get_ai_response(message: str, history: Optional[List[ChatMessage]] = None, language: str = "en") -> str:
    """
    Generate AI response based on user message in the specified language.

    Uses Claude AI if available, otherwise falls back to keyword matching.
    """
    # Try Claude AI first for intelligent responses
    claude_response = get_claude_response(message, history, language)
    if claude_response:
        return claude_response

    # Fallback to keyword-based responses
    logger.info("Using fallback keyword-based responses (Claude not available)")
    lower_message = message.lower()

    # Get the knowledge base for the specified language, fallback to English
    kb = KNOWLEDGE_BASE.get(language, KNOWLEDGE_BASE["en"])

    # Multilingual keyword detection
    migration_keywords = {
        'en': ['migration', 'migrate', 'create', 'new migration'],
        'da': ['migrering', 'migrer', 'opret', 'ny migrering'],
        'de': ['migration', 'migrieren', 'erstellen', 'neue migration'],
        'es': ['migración', 'migrar', 'crear', 'nueva migración'],
        'pt': ['migração', 'migrar', 'criar', 'nova migração'],
        'no': ['migrering', 'migrere', 'opprette', 'ny migrering'],
        'sv': ['migrering', 'migrera', 'skapa', 'ny migrering']
    }

    connection_keywords = {
        'en': ['connect', 'connection', 'database', 'mssql', 'sql server', 'credentials'],
        'da': ['forbindelse', 'database', 'mssql', 'sql server', 'legitimation'],
        'de': ['verbindung', 'datenbank', 'mssql', 'sql server', 'anmeldedaten'],
        'es': ['conexión', 'conectar', 'base de datos', 'mssql', 'sql server', 'credenciales'],
        'pt': ['conexão', 'conectar', 'banco de dados', 'mssql', 'sql server', 'credenciais'],
        'no': ['tilkobling', 'database', 'mssql', 'sql server', 'legitimasjon'],
        'sv': ['anslutning', 'databas', 'mssql', 'sql server', 'inloggning']
    }

    dbt_keywords = ['dbt', 'model', 'transformation', 'staging', 'warehouse']

    agent_keywords = {
        'en': ['agent', 'ai', 'dataprep', 'fine-tun', 'quality'],
        'da': ['agent', 'ai', 'dataprep', 'kvalitet'],
        'de': ['agent', 'ki', 'dataprep', 'qualität'],
        'es': ['agente', 'ia', 'dataprep', 'calidad'],
        'pt': ['agente', 'ia', 'dataprep', 'qualidade'],
        'no': ['agent', 'ai', 'dataprep', 'kvalitet'],
        'sv': ['agent', 'ai', 'dataprep', 'kvalitet']
    }

    error_keywords = {
        'en': ['error', 'fail', 'problem', 'issue', 'help', 'trouble'],
        'da': ['fejl', 'problem', 'hjælp'],
        'de': ['fehler', 'problem', 'hilfe'],
        'es': ['error', 'fallo', 'problema', 'ayuda'],
        'pt': ['erro', 'falha', 'problema', 'ajuda'],
        'no': ['feil', 'problem', 'hjelp'],
        'sv': ['fel', 'problem', 'hjälp']
    }

    security_keywords = {
        'en': ['security', 'secure', 'protect', 'safe', 'privacy', 'encrypt', 'data protection'],
        'da': ['sikker', 'beskyt', 'privat', 'krypter', 'databeskyttelse'],
        'de': ['sicher', 'schutz', 'schützen', 'privat', 'verschlüssel', 'datenschutz'],
        'es': ['segur', 'proteg', 'privac', 'cifra', 'encript', 'datos protegidos'],
        'pt': ['segur', 'proteg', 'privac', 'criptograf', 'dados protegidos'],
        'no': ['sikker', 'beskyt', 'privat', 'krypter', 'databeskyttelse'],
        'sv': ['säker', 'skydda', 'privat', 'krypter', 'dataskydd']
    }

    usage_keywords = {
        'en': ['how to use', 'platform', 'getting started', 'start', 'begin', 'what can'],
        'da': ['hvordan bruger', 'platform', 'kom i gang', 'start', 'begynde', 'hvad kan'],
        'de': ['wie benutze', 'plattform', 'anfangen', 'starten', 'beginnen', 'was kann'],
        'es': ['cómo usar', 'plataforma', 'utilizar', 'empezar', 'comenzar', 'qué puede'],
        'pt': ['como usar', 'plataforma', 'utilizar', 'começar', 'iniciar', 'o que pode'],
        'no': ['hvordan bruke', 'plattform', 'komme i gang', 'starte', 'begynne', 'hva kan'],
        'sv': ['hur använder', 'plattform', 'komma igång', 'starta', 'börja', 'vad kan']
    }

    # Get keywords for current language (with English fallback)
    mig_kw = migration_keywords.get(language, migration_keywords['en']) + migration_keywords['en']
    conn_kw = connection_keywords.get(language, connection_keywords['en']) + connection_keywords['en']
    agent_kw = agent_keywords.get(language, agent_keywords['en']) + agent_keywords['en']
    error_kw = error_keywords.get(language, error_keywords['en']) + error_keywords['en']
    security_kw = security_keywords.get(language, security_keywords['en']) + security_keywords['en']
    usage_kw = usage_keywords.get(language, usage_keywords['en']) + usage_keywords['en']

    # Keyword-based response selection - security first (most specific)
    if any(word in lower_message for word in security_kw):
        return kb["security"]

    if any(word in lower_message for word in mig_kw):
        return kb["migration"]

    if any(word in lower_message for word in conn_kw):
        return kb["connection"]

    if any(word in lower_message for word in dbt_keywords):
        return kb["dbt"]

    if any(word in lower_message for word in agent_kw):
        return kb["agent"]

    if any(word in lower_message for word in error_kw):
        return kb["error"]

    # Usage/platform questions return the default which explains capabilities
    if any(word in lower_message for word in usage_kw):
        return kb["default"]

    return kb["default"]


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI Support Chat endpoint.

    Uses RAG service when available, falls back to knowledge base.
    Supports multilingual responses based on the language parameter.
    """
    try:
        response = get_ai_response(request.message, request.history, request.language)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        # Multilingual error messages
        error_messages = {
            "en": "I apologize, but I'm having trouble processing your request. Please try again or check the Documentation section for help.",
            "da": "Beklager, men jeg har problemer med at behandle din anmodning. Prøv igen eller tjek dokumentationssektionen for hjælp.",
            "de": "Es tut mir leid, aber ich habe Probleme bei der Verarbeitung Ihrer Anfrage. Bitte versuchen Sie es erneut oder schauen Sie in der Dokumentation nach.",
            "es": "Lo siento, pero tengo problemas para procesar tu solicitud. Por favor, inténtalo de nuevo o consulta la sección de Documentación para obtener ayuda.",
            "pt": "Desculpe, mas estou tendo problemas para processar sua solicitação. Por favor, tente novamente ou consulte a seção de Documentação para obter ajuda.",
            "no": "Beklager, men jeg har problemer med å behandle forespørselen din. Vennligst prøv igjen eller sjekk dokumentasjonsseksjonen for hjelp.",
            "sv": "Jag ber om ursäkt, men jag har problem med att behandla din förfrågan. Vänligen försök igen eller kolla dokumentationssektionen för hjälp."
        }
        return ChatResponse(
            response=error_messages.get(request.language, error_messages["en"])
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
