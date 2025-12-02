"""
RAG (Retrieval-Augmented Generation) Service for DataMigrate AI.

This module provides vector-based semantic search capabilities using pgvector,
enabling the AI agents to learn from past migrations and retrieve relevant
context for better SQL transformations.

What is RAG?
------------
RAG combines retrieval (finding relevant documents) with generation (LLM responses).
Instead of relying solely on the LLM's training data, RAG:
1. Converts queries into vector embeddings
2. Searches a vector database for similar content
3. Provides that context to the LLM for more accurate responses

Benefits for DataMigrate AI:
- Learn from successful past migrations
- Retrieve similar schema transformation patterns
- Apply dbt best practices from knowledge base
- Improve accuracy over time as more migrations complete

Author: Alexander Garcia Angus
Property of: OKO Investments
"""

import os
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Optional: OpenAI for embeddings (can be replaced with local models)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class EmbeddingProvider:
    """
    Generates vector embeddings for text.

    Supports multiple providers:
    - OpenAI (text-embedding-ada-002)
    - Future: Ollama, HuggingFace, etc.
    """

    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = None

        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info(f"OpenAI embedding provider initialized with model: {model}")
        else:
            logger.warning("OpenAI not available. RAG will use mock embeddings.")

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.client:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        else:
            # Mock embedding for development (random-ish but deterministic)
            return self._mock_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.client:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        else:
            return [self._mock_embedding(t) for t in texts]

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to floats between -1 and 1
        embedding = []
        for i in range(0, min(len(hash_bytes) * 48, 1536)):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] / 128.0) - 1.0)
        # Pad to 1536 dimensions
        while len(embedding) < 1536:
            embedding.append(0.0)
        return embedding[:1536]


class RAGService:
    """
    Main RAG service for semantic search and context retrieval.

    Usage:
        rag = RAGService()

        # Store a successful transformation
        rag.store_transformation(
            source_sql="SELECT * FROM dbo.Customers",
            target_sql="SELECT * FROM {{ ref('stg_customers') }}",
            transformation_type="table",
            quality_score=0.95
        )

        # Find similar transformations
        results = rag.search_transformations(
            "SELECT * FROM dbo.Orders WHERE status = 'active'"
        )
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.embedding_provider = EmbeddingProvider(self.config.embedding_model)
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                dbname=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            logger.info("RAG service connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.conn = None

    def is_available(self) -> bool:
        """Check if RAG service is available."""
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM schema_embeddings LIMIT 1")
            return True
        except:
            return False

    # =========================================================================
    # Schema Embeddings
    # =========================================================================

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
        if not self.conn:
            raise RuntimeError("RAG service not connected")

        # Create text representation for embedding
        text = f"{source_type}: {source_name}\n{json.dumps(source_schema, indent=2)}"
        embedding = self.embedding_provider.embed(text)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO schema_embeddings
                (source_type, source_name, source_schema, embedding, metadata, migration_id, organization_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                source_type,
                source_name,
                Json(source_schema),
                embedding,
                Json(metadata) if metadata else None,
                migration_id,
                organization_id
            ))
            self.conn.commit()
            return cur.fetchone()[0]

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
        if not self.conn:
            return []

        top_k = top_k or self.config.top_k
        query_embedding = self.embedding_provider.embed(query)

        filters = []
        params = [query_embedding, top_k]

        if source_type:
            filters.append("source_type = %s")
            params.insert(-1, source_type)

        if organization_id:
            filters.append("organization_id = %s")
            params.insert(-1, organization_id)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT
                    id, source_type, source_name, source_schema, metadata,
                    1 - (embedding <=> %s) as similarity
                FROM schema_embeddings
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
            """, [query_embedding] + params[:-1] + [query_embedding, top_k])
            return cur.fetchall()

    # =========================================================================
    # Transformation Embeddings
    # =========================================================================

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
            migration_id: Associated migration
            organization_id: Associated organization
            metadata: Additional context

        Returns:
            ID of stored transformation
        """
        if not self.conn:
            raise RuntimeError("RAG service not connected")

        embedding = self.embedding_provider.embed(source_sql)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transformation_embeddings
                (source_sql, target_sql, transformation_type, embedding, quality_score,
                 metadata, migration_id, organization_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                source_sql,
                target_sql,
                transformation_type,
                embedding,
                quality_score,
                Json(metadata) if metadata else None,
                migration_id,
                organization_id
            ))
            self.conn.commit()
            return cur.fetchone()[0]

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

        This is the core RAG function - given a source SQL, find the most
        similar past transformations to guide the LLM.

        Args:
            source_sql: The SQL to find similar transformations for
            transformation_type: Filter by type
            min_quality_score: Minimum quality threshold
            organization_id: Filter by organization
            top_k: Number of results

        Returns:
            List of similar transformations with scores
        """
        if not self.conn:
            return []

        # Check cache first
        cached = self._check_cache(source_sql)
        if cached:
            return cached

        top_k = top_k or self.config.top_k
        query_embedding = self.embedding_provider.embed(source_sql)

        filters = ["quality_score >= %s"]
        params = [min_quality_score]

        if transformation_type:
            filters.append("transformation_type = %s")
            params.append(transformation_type)

        if organization_id:
            filters.append("organization_id = %s")
            params.append(organization_id)

        where_clause = f"WHERE {' AND '.join(filters)}"

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT
                    id, source_sql, target_sql, transformation_type,
                    quality_score, metadata,
                    1 - (embedding <=> %s) as similarity
                FROM transformation_embeddings
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
            """, [query_embedding] + params + [query_embedding, top_k])
            results = cur.fetchall()

        # Cache the results
        self._store_cache(source_sql, results)

        return results

    # =========================================================================
    # Knowledge Base
    # =========================================================================

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
        if not self.conn:
            raise RuntimeError("RAG service not connected")

        text = f"{category}: {title}\n{content}"
        embedding = self.embedding_provider.embed(text)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_embeddings
                (category, title, content, embedding, source)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (category, title, content, embedding, source))
            self.conn.commit()
            return cur.fetchone()[0]

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant best practices.

        Args:
            query: Search query
            category: Filter by category
            top_k: Number of results

        Returns:
            List of relevant knowledge items
        """
        if not self.conn:
            return []

        top_k = top_k or self.config.top_k
        query_embedding = self.embedding_provider.embed(query)

        where_clause = ""
        params = []
        if category:
            where_clause = "WHERE category = %s"
            params.append(category)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"""
                SELECT
                    id, category, title, content, source,
                    1 - (embedding <=> %s) as similarity
                FROM knowledge_embeddings
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
            """, [query_embedding] + params + [query_embedding, top_k])
            return cur.fetchall()

    # =========================================================================
    # RAG Context Builder
    # =========================================================================

    def build_context(
        self,
        source_sql: str,
        schema_info: Optional[Dict[str, Any]] = None,
        include_knowledge: bool = True,
        organization_id: Optional[int] = None
    ) -> str:
        """
        Build complete RAG context for LLM prompt.

        This combines:
        1. Similar past transformations
        2. Relevant schema patterns
        3. Applicable best practices

        Args:
            source_sql: The SQL being transformed
            schema_info: Schema context
            include_knowledge: Include best practices
            organization_id: Filter to organization's data

        Returns:
            Formatted context string for LLM prompt
        """
        context_parts = []

        # Find similar transformations
        transformations = self.search_transformations(
            source_sql,
            min_quality_score=0.7,
            organization_id=organization_id,
            top_k=3
        )

        if transformations:
            context_parts.append("## Similar Past Transformations\n")
            for i, t in enumerate(transformations, 1):
                context_parts.append(f"""
### Example {i} (Similarity: {t['similarity']:.2%}, Quality: {t['quality_score']:.2%})
**Source SQL:**
```sql
{t['source_sql']}
```

**dbt SQL:**
```sql
{t['target_sql']}
```
""")

        # Find relevant knowledge
        if include_knowledge:
            knowledge = self.search_knowledge(source_sql, top_k=2)
            if knowledge:
                context_parts.append("\n## Best Practices\n")
                for k in knowledge:
                    context_parts.append(f"- **{k['title']}**: {k['content'][:200]}...\n")

        return "\n".join(context_parts) if context_parts else ""

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.sha256(query.encode()).hexdigest()

    def _check_cache(self, query: str) -> Optional[List[Dict]]:
        """Check if results are cached."""
        if not self.conn:
            return None

        cache_key = self._get_cache_key(query)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE rag_query_cache
                SET hit_count = hit_count + 1
                WHERE query_hash = %s AND expires_at > NOW()
                RETURNING results
            """, (cache_key,))
            row = cur.fetchone()
            self.conn.commit()

            if row:
                return row['results']
        return None

    def _store_cache(self, query: str, results: List[Dict]):
        """Store results in cache."""
        if not self.conn:
            return

        cache_key = self._get_cache_key(query)
        expires_at = datetime.utcnow() + timedelta(hours=self.config.cache_ttl_hours)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rag_query_cache (query_hash, query_text, results, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (query_hash) DO UPDATE
                SET results = EXCLUDED.results, expires_at = EXCLUDED.expires_at
            """, (cache_key, query[:1000], Json(results), expires_at))
            self.conn.commit()

    def clear_expired_cache(self):
        """Remove expired cache entries."""
        if not self.conn:
            return

        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM rag_query_cache WHERE expires_at < NOW()")
            self.conn.commit()

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        if not self.conn:
            return {"available": False}

        stats = {"available": True}

        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM schema_embeddings")
            stats["schema_embeddings"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM transformation_embeddings")
            stats["transformation_embeddings"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM knowledge_embeddings")
            stats["knowledge_embeddings"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*), SUM(hit_count) FROM rag_query_cache WHERE expires_at > NOW()")
            row = cur.fetchone()
            stats["cache_entries"] = row[0]
            stats["cache_hits"] = row[1] or 0

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        config = RAGConfig(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "datamigrate"),
            db_user=os.getenv("DB_USER", "datamigrate"),
            db_password=os.getenv("DB_PASSWORD", "datamigrate123"),
        )
        _rag_service = RAGService(config)
    return _rag_service


# =============================================================================
# Knowledge Base Initialization
# =============================================================================

DBT_BEST_PRACTICES = [
    {
        "category": "materialization",
        "title": "Choose appropriate materialization",
        "content": """Use 'view' for simple transformations, 'table' for heavy
        transformations used frequently, 'incremental' for large fact tables
        with timestamp columns, and 'ephemeral' for CTEs that shouldn't be
        stored."""
    },
    {
        "category": "naming",
        "title": "Use consistent naming conventions",
        "content": """Prefix staging models with 'stg_', intermediate with 'int_',
        and marts with 'fct_' (facts) or 'dim_' (dimensions). Use snake_case
        for all model and column names."""
    },
    {
        "category": "testing",
        "title": "Add tests to all models",
        "content": """At minimum, add unique and not_null tests to primary keys.
        Add accepted_values tests to status/type columns. Add relationships
        tests to foreign keys."""
    },
    {
        "category": "performance",
        "title": "Optimize incremental models",
        "content": """Use is_incremental() macro to filter source data. Add
        appropriate indexes on timestamp columns. Consider partitioning for
        very large tables."""
    },
    {
        "category": "documentation",
        "title": "Document all models",
        "content": """Add descriptions to all models and columns in schema.yml.
        Include business context, not just technical definitions. Document
        any calculations or business rules."""
    },
]


def initialize_knowledge_base():
    """Populate knowledge base with dbt best practices."""
    rag = get_rag_service()
    if not rag.is_available():
        logger.warning("RAG service not available, skipping knowledge base init")
        return

    for practice in DBT_BEST_PRACTICES:
        try:
            rag.store_knowledge(
                category=practice["category"],
                title=practice["title"],
                content=practice["content"],
                source="internal"
            )
            logger.info(f"Added knowledge: {practice['title']}")
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")


if __name__ == "__main__":
    # Test the RAG service
    print("Testing RAG Service...")

    rag = get_rag_service()
    print(f"RAG Available: {rag.is_available()}")
    print(f"Stats: {rag.get_stats()}")

    # Initialize knowledge base
    print("\nInitializing knowledge base...")
    initialize_knowledge_base()

    # Test search
    print("\nSearching for materialization advice...")
    results = rag.search_knowledge("when should I use incremental models")
    for r in results:
        print(f"  - {r['title']} (similarity: {r['similarity']:.2%})")
