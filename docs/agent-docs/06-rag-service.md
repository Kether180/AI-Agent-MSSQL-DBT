# RAG Service

## Status: Beta (85%)

## Overview
The RAG (Retrieval-Augmented Generation) Service provides intelligent query assistance using vector-based semantic search. It indexes schema documentation, past transformations, and best practices to enhance LLM responses with relevant context.

## File Locations
- Main Service: `services/rag_service.py`
- Vector Store: PostgreSQL with pgvector extension
- API Integration: `agents/api.py`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Service                               │
│                                                                   │
│  ┌───────────────┐    ┌───────────────┐    ┌─────────────────┐  │
│  │    Schema     │    │Transformation │    │   Knowledge     │  │
│  │  Embeddings   │    │  Embeddings   │    │  Embeddings     │  │
│  └───────┬───────┘    └───────┬───────┘    └───────┬─────────┘  │
│          │                    │                    │             │
│          └────────────────────┼────────────────────┘             │
│                               │                                  │
│                    ┌──────────▼──────────┐                       │
│                    │   Vector Search     │                       │
│                    │   (pgvector)        │                       │
│                    └──────────┬──────────┘                       │
│                               │                                  │
│                    ┌──────────▼──────────┐                       │
│                    │  Context Builder    │                       │
│                    │  (combines results) │                       │
│                    └──────────┬──────────┘                       │
│                               │                                  │
│                    ┌──────────▼──────────┐                       │
│                    │      LLM Call       │                       │
│                    │  (with RAG context) │                       │
│                    └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Key Classes

### Configuration

```python
@dataclass
class RAGConfig:
    """Configuration for RAG service."""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "datamigrate"
    db_user: str = "datamigrate"
    db_password: str = "datamigrate123"
    embedding_model: str = "text-embedding-ada-002"  # OpenAI model
    embedding_dimension: int = 1536
    cache_ttl_hours: int = 24
    top_k: int = 5  # Number of results to return
```

### Embedding Provider

```python
class EmbeddingProvider:
    """
    Generates vector embeddings for text.

    Supports multiple providers:
    - OpenAI (text-embedding-ada-002)
    - Mock embeddings for development
    """

    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        # Uses OPENAI_API_KEY environment variable

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
```

## Main Class: RAGService

### Initialization

```python
from services.rag_service import RAGService, RAGConfig, get_rag_service

# Using default configuration
rag = get_rag_service()  # Singleton

# Custom configuration
config = RAGConfig(
    db_host="localhost",
    db_name="datamigrate",
    embedding_model="text-embedding-ada-002",
    top_k=5
)
rag = RAGService(config)

# Check availability
if rag.is_available():
    print("RAG service ready")
```

### Core Methods

#### 1. Store Schema Patterns

```python
def store_schema(
    self,
    source_type: str,
    source_name: str,
    source_schema: Dict[str, Any],
    migration_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Store a schema pattern with its embedding.

    Args:
        source_type: 'table', 'column', 'relationship', 'procedure'
        source_name: Original name (e.g., 'dbo.Customers')
        source_schema: Full schema definition as dict
        migration_id: Associated migration ID
        organization_id: Associated organization ID
        metadata: Additional context

    Returns:
        ID of the stored embedding
    """

# Usage:
schema_id = rag.store_schema(
    source_type="table",
    source_name="dbo.Customers",
    source_schema={
        "columns": [
            {"name": "id", "type": "int", "primary_key": True},
            {"name": "email", "type": "varchar(255)"}
        ]
    },
    migration_id=123
)
```

#### 2. Search Similar Schemas

```python
def search_schemas(
    self,
    query: str,
    source_type: Optional[str] = None,
    organization_id: Optional[int] = None,
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar schema patterns.

    Args:
        query: Search query (schema description or SQL)
        source_type: Filter by type
        organization_id: Filter by organization
        top_k: Number of results

    Returns:
        List of similar schemas with similarity scores
    """

# Usage:
results = rag.search_schemas(
    query="customer table with email and phone",
    source_type="table",
    top_k=5
)

for r in results:
    print(f"{r['source_name']}: {r['similarity']:.2%}")
```

#### 3. Store SQL Transformations

```python
def store_transformation(
    self,
    source_sql: str,
    target_sql: str,
    transformation_type: str,
    quality_score: float = 0.0,
    migration_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Store a successful SQL transformation pattern.

    Args:
        source_sql: Original MSSQL
        target_sql: Generated dbt SQL
        transformation_type: 'table', 'view', 'procedure', 'function'
        quality_score: Validation score (0-1)

    Returns:
        ID of stored transformation
    """

# Usage:
rag.store_transformation(
    source_sql="SELECT * FROM dbo.Customers WHERE active = 1",
    target_sql="""
    {{ config(materialized='view') }}

    SELECT * FROM {{ source('mssql', 'customers') }}
    WHERE active = 1
    """,
    transformation_type="view",
    quality_score=0.95
)
```

#### 4. Search Similar Transformations

```python
def search_transformations(
    self,
    source_sql: str,
    transformation_type: Optional[str] = None,
    min_quality_score: float = 0.0,
    organization_id: Optional[int] = None,
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Find similar SQL transformations.

    This is the core RAG function - given a source SQL, find
    similar past transformations to guide the LLM.

    Returns:
        List of similar transformations with scores
    """

# Usage:
similar = rag.search_transformations(
    source_sql="SELECT * FROM dbo.Orders WHERE status = 'active'",
    min_quality_score=0.7,
    top_k=3
)

for t in similar:
    print(f"Similarity: {t['similarity']:.2%}")
    print(f"Target SQL: {t['target_sql'][:100]}...")
```

#### 5. Store Knowledge Base Items

```python
def store_knowledge(
    self,
    category: str,
    title: str,
    content: str,
    source: str = "internal"
) -> int:
    """
    Store dbt best practice or knowledge item.

    Args:
        category: 'materialization', 'testing', 'naming', 'performance'
        title: Short title
        content: Full content/best practice
        source: 'dbt_docs', 'community', 'internal'

    Returns:
        ID of stored knowledge
    """

# Usage:
rag.store_knowledge(
    category="materialization",
    title="When to use incremental models",
    content="Use incremental for large fact tables with timestamp columns...",
    source="dbt_docs"
)
```

#### 6. Build Complete RAG Context

```python
def build_context(
    self,
    source_sql: str,
    schema_info: Optional[Dict[str, Any]] = None,
    include_knowledge: bool = True,
    organization_id: Optional[int] = None
) -> str:
    """
    Build complete RAG context for LLM prompt.

    Combines:
    1. Similar past transformations
    2. Relevant schema patterns
    3. Applicable best practices

    Returns:
        Formatted context string for LLM prompt
    """

# Usage:
context = rag.build_context(
    source_sql="SELECT * FROM dbo.Orders JOIN dbo.Customers...",
    include_knowledge=True
)

# Use in LLM prompt
prompt = f"""
{context}

Now transform this SQL to dbt:
{source_sql}
"""
```

## Built-in Best Practices

The service includes default dbt best practices:

```python
DBT_BEST_PRACTICES = [
    {
        "category": "materialization",
        "title": "Choose appropriate materialization",
        "content": """Use 'view' for simple transformations, 'table' for heavy
        transformations used frequently, 'incremental' for large fact tables
        with timestamp columns, and 'ephemeral' for CTEs."""
    },
    {
        "category": "naming",
        "title": "Use consistent naming conventions",
        "content": """Prefix staging models with 'stg_', intermediate with 'int_',
        and marts with 'fct_' (facts) or 'dim_' (dimensions)."""
    },
    {
        "category": "testing",
        "title": "Add tests to all models",
        "content": """At minimum, add unique and not_null tests to primary keys.
        Add accepted_values tests to status/type columns."""
    },
    {
        "category": "performance",
        "title": "Optimize incremental models",
        "content": """Use is_incremental() macro to filter source data.
        Add appropriate indexes on timestamp columns."""
    },
    {
        "category": "documentation",
        "title": "Document all models",
        "content": """Add descriptions to all models and columns in schema.yml.
        Include business context, not just technical definitions."""
    }
]
```

## Database Schema Required

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Schema embeddings table
CREATE TABLE schema_embeddings (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50),
    source_name VARCHAR(255),
    source_schema JSONB,
    embedding vector(1536),
    metadata JSONB,
    migration_id INTEGER,
    organization_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transformation embeddings table
CREATE TABLE transformation_embeddings (
    id SERIAL PRIMARY KEY,
    source_sql TEXT,
    target_sql TEXT,
    transformation_type VARCHAR(50),
    embedding vector(1536),
    quality_score FLOAT,
    metadata JSONB,
    migration_id INTEGER,
    organization_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge embeddings table
CREATE TABLE knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50),
    title VARCHAR(255),
    content TEXT,
    embedding vector(1536),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query cache table
CREATE TABLE rag_query_cache (
    query_hash VARCHAR(64) PRIMARY KEY,
    query_text TEXT,
    results JSONB,
    hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Integration with API

```python
@router.post("/chat")
async def chat_endpoint(
    query: str,
    migration_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """RAG-powered chat endpoint"""
    rag = get_rag_service()

    # Build context from past migrations
    context = rag.build_context(
        source_sql=query,
        include_knowledge=True
    )

    # Call LLM with context
    response = await llm.ainvoke([
        SystemMessage(content=f"You are a dbt expert. Use this context:\n{context}"),
        HumanMessage(content=query)
    ])

    return {"response": response.content}


@router.post("/migrations/{migration_id}/index")
async def index_migration(
    migration_id: int,
    db: Session = Depends(get_db)
):
    """Index completed migration for RAG"""
    migration = db.query(Migration).filter(Migration.id == migration_id).first()

    rag = get_rag_service()

    # Index all tables
    for table in migration.extracted_metadata.get('tables', []):
        rag.store_schema(
            source_type="table",
            source_name=f"{table['schema']}.{table['name']}",
            source_schema=table,
            migration_id=migration_id
        )

    # Index successful transformations
    if migration.validation_status == "passed":
        rag.store_transformation(
            source_sql=migration.source_sql,
            target_sql=migration.generated_dbt,
            transformation_type="migration",
            quality_score=0.95,
            migration_id=migration_id
        )

    return {"indexed": True}
```

## Statistics

```python
stats = rag.get_stats()
# Returns:
{
    "available": True,
    "schema_embeddings": 150,
    "transformation_embeddings": 75,
    "knowledge_embeddings": 10,
    "cache_entries": 25,
    "cache_hits": 500
}
```

## Current Capabilities
- [x] Schema embedding storage and search
- [x] Transformation embedding storage and search
- [x] Knowledge base with best practices
- [x] Context building for LLM prompts
- [x] Query caching with TTL
- [x] Mock embeddings for development
- [x] OpenAI embedding integration
- [ ] Feedback learning from user corrections
- [ ] Multi-tenant data isolation
- [ ] Streaming responses

## Integration Status
- [x] Core RAG engine - COMPLETE
- [x] Vector storage (pgvector) - COMPLETE
- [x] Embedding generation - COMPLETE
- [ ] API endpoint - EXISTS BUT NOT USED
- [ ] Frontend chat interface - NOT CONNECTED
- [ ] Auto-indexing after migration - NOT CONNECTED

## TODO - HIGH PRIORITY
1. [ ] Create `/chat` API endpoint
2. [ ] Create ChatWidget Vue component
3. [ ] Auto-index schemas after extraction
4. [ ] Add chat to dashboard
5. [ ] Implement conversation history

## Dependencies
```
psycopg2
openai
```

---
Last Updated: 2024-12-05
