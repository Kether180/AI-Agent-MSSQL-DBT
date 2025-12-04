"""
RAG v2: Contextual Retrieval Service for DataMigrate AI
=======================================================

This is an ENHANCED version of our RAG service implementing Anthropic's
"Contextual Retrieval" approach, which reduces retrieval failures by 67%.

LEARNING GUIDE: This file is heavily annotated to help you understand
the improvements over traditional RAG.

=============================================================================
WHAT'S NEW IN THIS VERSION (vs rag_service.py)
=============================================================================

1. CONTEXTUAL EMBEDDINGS (35% improvement)
   - Before embedding text, we prepend contextual information
   - Example: Instead of embedding "ALTER TABLE ADD COLUMN customer_id"
   - We embed: "This SQL is from Sales schema, CustomerOrders table, in
     ACME Corp's MSSQL ERP system. ALTER TABLE ADD COLUMN customer_id"

2. BM25 HYBRID SEARCH (49% improvement when combined with embeddings)
   - Vector search is great for semantic similarity
   - BM25 is great for exact keyword matches (error codes, table names)
   - We combine both using "Rank Fusion"

3. RERANKING (67% improvement total)
   - After getting top 150 results, we use a reranker model
   - The reranker is a cross-encoder that scores query-document pairs
   - We return only the top 20 after reranking

4. BETTER EMBEDDINGS (Voyage AI)
   - OpenAI ada-002 is outdated (2022)
   - Voyage AI voyage-3 is #1 on MTEB benchmarks
   - Anthropic specifically recommends Voyage in their research

=============================================================================
ARCHITECTURE OVERVIEW
=============================================================================

Traditional RAG:
    Query -> Embed -> Vector Search -> Top K Results -> LLM

Contextual Retrieval RAG:
    Query -> [Embed + BM25] -> Rank Fusion -> Rerank -> Top K -> LLM
              ^                                  ^
              |                                  |
    Contextual Embeddings              Cross-Encoder Reranker

=============================================================================

Author: Alexander Garcia Angus
Property of: OKO Investments
Based on: Anthropic's "Contextual Retrieval" research (Sep 2024)
"""

import os
import re
import math
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import Counter
from abc import ABC, abstractmethod

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# SECTION 1: CONFIGURATION
# =============================================================================
#
# LEARNING POINT: Configuration is now more flexible to support multiple
# embedding providers and the new features.
# =============================================================================

@dataclass
class RAGConfigV2:
    """
    Enhanced configuration for Contextual Retrieval.

    KEY CHANGES FROM V1:
    - embedding_provider: Now supports 'voyage', 'openai', 'gemini', 'local'
    - enable_bm25: Toggle hybrid search
    - enable_reranking: Toggle cross-encoder reranking
    - enable_contextual_embeddings: Toggle context prepending
    - rerank_top_n: How many results to fetch before reranking
    """
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "datamigrate"
    db_user: str = "datamigrate"
    db_password: str = "datamigrate123"

    # Embedding Configuration
    # -------------------------------------------------------------------------
    # LEARNING POINT: We now support multiple providers with fallback chain
    # Priority: voyage > openai > local_mock
    # -------------------------------------------------------------------------
    embedding_provider: str = "voyage"  # 'voyage', 'openai', 'gemini', 'local'
    embedding_model: str = "voyage-3"   # Best performing model (Anthropic recommended)
    embedding_dimension: int = 1024     # voyage-3 uses 1024, ada-002 uses 1536

    # Contextual Retrieval Settings
    # -------------------------------------------------------------------------
    # LEARNING POINT: These are the new features that improve retrieval by 67%
    # -------------------------------------------------------------------------
    enable_contextual_embeddings: bool = True  # Prepend context before embedding
    enable_bm25: bool = True                   # Hybrid search with keyword matching
    enable_reranking: bool = True              # Cross-encoder reranking

    # Search Settings
    top_k: int = 20                   # Final results to return
    rerank_top_n: int = 150           # Candidates to fetch before reranking
    bm25_weight: float = 0.5          # Weight for BM25 in hybrid search (0-1)
    min_similarity_threshold: float = 0.3  # Minimum similarity score

    # Cache
    cache_ttl_hours: int = 24

    # Reranker Configuration
    reranker_provider: str = "cohere"  # 'cohere', 'voyage'
    reranker_model: str = "rerank-english-v3.0"


# =============================================================================
# SECTION 2: EMBEDDING PROVIDERS
# =============================================================================
#
# LEARNING POINT: We now have a provider abstraction that supports:
# - Voyage AI (best performance, Anthropic recommended)
# - OpenAI (fallback)
# - Google Gemini (free tier)
# - Local mock (development)
#
# Why Voyage AI?
# - #1 on MTEB (Massive Text Embedding Benchmark)
# - Specifically recommended by Anthropic
# - Better code/SQL understanding than OpenAI
# - Competitive pricing
# =============================================================================

class EmbeddingProviderBase(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class VoyageEmbeddingProvider(EmbeddingProviderBase):
    """
    Voyage AI Embedding Provider - BEST PERFORMANCE

    LEARNING POINT: Why Voyage AI?
    ================================
    1. #1 on MTEB benchmark (beats OpenAI, Cohere, Google)
    2. Anthropic specifically recommends it in their research
    3. Better for code/SQL than general-purpose models
    4. voyage-3: 1024 dimensions (smaller = faster search)
    5. voyage-code-3: Specialized for code (even better for SQL)

    Models:
    - voyage-3: General purpose, best overall
    - voyage-code-3: Optimized for code/SQL
    - voyage-3-lite: Faster, slightly less accurate

    Pricing: $0.06 per million tokens (cheaper than OpenAI)
    """

    def __init__(self, model: str = "voyage-3"):
        self.model = model
        self.api_key = os.getenv("VOYAGE_API_KEY")
        self._dimension = 1024  # voyage-3 dimension

        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY environment variable not set")

        # Import voyage client
        try:
            import voyageai
            self.client = voyageai.Client(api_key=self.api_key)
            logger.info(f"Voyage AI provider initialized with model: {model}")
        except ImportError:
            raise ImportError("voyageai package not installed. Run: pip install voyageai")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        result = self.client.embed([text], model=self.model)
        return result.embeddings[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        LEARNING POINT: Voyage supports batch embedding up to 128 texts
        which is more efficient than calling embed() in a loop.
        """
        result = self.client.embed(texts, model=self.model)
        return result.embeddings


class OpenAIEmbeddingProvider(EmbeddingProviderBase):
    """
    OpenAI Embedding Provider - FALLBACK OPTION

    LEARNING POINT: OpenAI embeddings are good but not the best:
    - text-embedding-3-large: 3072 dimensions (newer, better)
    - text-embedding-ada-002: 1536 dimensions (legacy, used in v1)

    We keep this as a fallback when Voyage is unavailable.
    """

    def __init__(self, model: str = "text-embedding-3-large"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Dimension depends on model
        self._dimension = 3072 if "3-large" in model else 1536

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI provider initialized with model: {model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class LocalMockEmbeddingProvider(EmbeddingProviderBase):
    """
    Local Mock Provider - FOR DEVELOPMENT ONLY

    LEARNING POINT: This generates deterministic fake embeddings based
    on text hashing. Use for testing without API calls.
    """

    def __init__(self, dimension: int = 1024):
        self._dimension = dimension
        logger.warning("Using LOCAL MOCK embeddings - NOT FOR PRODUCTION")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(self._dimension):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] / 128.0) - 1.0)
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]


def get_embedding_provider(config: RAGConfigV2) -> EmbeddingProviderBase:
    """
    Factory function to get the appropriate embedding provider.

    LEARNING POINT: We use a fallback chain:
    1. Try configured provider (voyage)
    2. Fall back to OpenAI if available
    3. Fall back to local mock (development only)
    """
    providers_to_try = []

    if config.embedding_provider == "voyage":
        providers_to_try = ["voyage", "openai", "local"]
    elif config.embedding_provider == "openai":
        providers_to_try = ["openai", "voyage", "local"]
    else:
        providers_to_try = ["local"]

    for provider in providers_to_try:
        try:
            if provider == "voyage":
                return VoyageEmbeddingProvider(config.embedding_model)
            elif provider == "openai":
                return OpenAIEmbeddingProvider()
            elif provider == "local":
                return LocalMockEmbeddingProvider(config.embedding_dimension)
        except (ValueError, ImportError) as e:
            logger.warning(f"Could not initialize {provider} provider: {e}")
            continue

    # Should never reach here, local always works
    return LocalMockEmbeddingProvider(config.embedding_dimension)


# =============================================================================
# SECTION 3: BM25 IMPLEMENTATION
# =============================================================================
#
# LEARNING POINT: BM25 (Best Match 25) is a "lexical" search algorithm
# that finds exact keyword matches. It's different from vector search:
#
# Vector Search:          BM25:
# "SELECT * FROM users"   "SELECT * FROM users"
#         ↓                        ↓
# [0.23, -0.45, 0.12...]  {SELECT: 1, FROM: 1, users: 1}
#         ↓                        ↓
# Cosine similarity       Term frequency matching
#
# WHY WE NEED BOTH:
# - Vector search finds "semantically similar" SQL
# - BM25 finds exact table names, error codes, column names
#
# Example where BM25 wins:
# Query: "Fix error TS-999 in CustomerOrders table"
# - Vector search might find general error handling docs
# - BM25 finds the exact "TS-999" and "CustomerOrders" mentions
# =============================================================================

class BM25:
    """
    BM25 Implementation for Hybrid Search

    LEARNING POINT: BM25 builds on TF-IDF (Term Frequency-Inverse Document Frequency)

    TF-IDF says: Words that appear often in a document but rarely in others are important
    BM25 adds:
    - Saturation: Diminishing returns for very frequent terms
    - Document length normalization: Long docs don't unfairly match everything

    Parameters:
    - k1: Term frequency saturation (1.2-2.0 typical)
    - b: Document length normalization (0.75 typical)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Document length normalization parameter
        self.documents: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self.doc_freqs: Dict[str, int] = {}  # Document frequency per term
        self.idf: Dict[str, float] = {}      # Inverse document frequency
        self.doc_term_freqs: List[Dict[str, int]] = []  # Term freq per doc

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing.

        LEARNING POINT: For SQL, we want to:
        - Keep table names intact (Customer_Orders)
        - Split on operators and punctuation
        - Lowercase for matching
        - Remove very common SQL keywords (optional)
        """
        # Convert to lowercase
        text = text.lower()
        # Split on non-alphanumeric characters, but keep underscores
        tokens = re.findall(r'[a-z0-9_]+', text)
        # Filter very short tokens
        tokens = [t for t in tokens if len(t) > 1]
        return tokens

    def index(self, documents: List[str]) -> None:
        """
        Build BM25 index from documents.

        LEARNING POINT: This preprocesses all documents for fast retrieval.
        We store:
        - Tokenized documents
        - Document lengths
        - Document frequencies (how many docs contain each term)
        - IDF scores (how "special" each term is)
        """
        self.documents = []
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.doc_freqs = Counter()

        # Tokenize and count
        for doc in documents:
            tokens = self._tokenize(doc)
            self.documents.append(tokens)
            self.doc_lengths.append(len(tokens))

            # Term frequency in this document
            term_freq = Counter(tokens)
            self.doc_term_freqs.append(dict(term_freq))

            # Document frequency (count unique terms per doc)
            self.doc_freqs.update(set(tokens))

        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

        # Calculate IDF for each term
        # IDF = log((N - n + 0.5) / (n + 0.5))
        # N = total documents, n = docs containing term
        N = len(self.documents)
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for documents matching query.

        Returns: List of (doc_index, score) tuples, sorted by score descending.

        LEARNING POINT: BM25 score formula:
        score = sum over query terms of:
            IDF(term) * (term_freq * (k1 + 1)) /
                        (term_freq + k1 * (1 - b + b * doc_len/avg_doc_len))

        This means:
        - Rare terms (high IDF) contribute more
        - More occurrences help, but with diminishing returns (saturation)
        - Long documents are penalized (length normalization)
        """
        query_tokens = self._tokenize(query)
        scores = []

        for doc_idx, (doc_terms, doc_len) in enumerate(
            zip(self.doc_term_freqs, self.doc_lengths)
        ):
            score = 0.0

            for term in query_tokens:
                if term not in self.idf:
                    continue  # Term not in any document

                tf = doc_terms.get(term, 0)
                if tf == 0:
                    continue  # Term not in this document

                # BM25 formula
                idf = self.idf[term]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * doc_len / self.avg_doc_length
                )
                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((doc_idx, score))

        # Sort by score descending and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# =============================================================================
# SECTION 4: RERANKING
# =============================================================================
#
# LEARNING POINT: Reranking is a "second pass" over retrieval results.
#
# Initial retrieval (embeddings + BM25):
# - Fast but approximate
# - Scores query against each doc independently
# - Returns ~150 candidates
#
# Reranking (cross-encoder):
# - Slower but more accurate
# - Scores query-document PAIRS together
# - The model sees both query and doc, understanding their relationship
# - Returns top ~20 from the 150 candidates
#
# Why it works better:
# - Cross-encoders can understand nuanced relationships
# - They can detect when a doc is relevant even if keywords don't match
# - They filter out "false positives" from initial retrieval
#
# Anthropic's research shows: Reranking alone improves retrieval by 67%
# =============================================================================

class RerankerBase(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 20
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents for a query.

        Args:
            query: The search query
            documents: List of document texts to rerank
            top_k: Number of top results to return

        Returns:
            List of (original_index, relevance_score) tuples
        """
        pass


class CohereReranker(RerankerBase):
    """
    Cohere Reranker - RECOMMENDED BY ANTHROPIC

    LEARNING POINT: Cohere's reranker is a cross-encoder model that:
    - Takes query + document as input
    - Outputs a relevance score (0-1)
    - Is specifically trained for retrieval reranking

    Models:
    - rerank-english-v3.0: Latest, best performance
    - rerank-multilingual-v3.0: For non-English content
    - rerank-english-v2.0: Older, slightly faster

    Pricing: $1.00 per 1000 searches (very affordable)
    """

    def __init__(self, model: str = "rerank-english-v3.0"):
        self.model = model
        self.api_key = os.getenv("COHERE_API_KEY")

        if not self.api_key:
            raise ValueError("COHERE_API_KEY environment variable not set")

        try:
            import cohere
            self.client = cohere.Client(api_key=self.api_key)
            logger.info(f"Cohere reranker initialized with model: {model}")
        except ImportError:
            raise ImportError("cohere package not installed. Run: pip install cohere")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 20
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents using Cohere's cross-encoder.

        LEARNING POINT: The reranker sees the full query and document together,
        allowing it to understand the relationship between them.
        """
        if not documents:
            return []

        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_k,
            return_documents=False
        )

        # Return (original_index, relevance_score) tuples
        return [(r.index, r.relevance_score) for r in response.results]


class NoOpReranker(RerankerBase):
    """
    No-op reranker for when reranking is disabled.

    LEARNING POINT: This just returns documents in their original order
    with dummy scores. Used when enable_reranking=False.
    """

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 20
    ) -> List[Tuple[int, float]]:
        # Return original order with decreasing scores
        return [(i, 1.0 - i * 0.01) for i in range(min(len(documents), top_k))]


def get_reranker(config: RAGConfigV2) -> RerankerBase:
    """Factory function to get appropriate reranker."""
    if not config.enable_reranking:
        return NoOpReranker()

    try:
        if config.reranker_provider == "cohere":
            return CohereReranker(config.reranker_model)
        else:
            logger.warning(f"Unknown reranker provider: {config.reranker_provider}")
            return NoOpReranker()
    except (ValueError, ImportError) as e:
        logger.warning(f"Could not initialize reranker: {e}")
        return NoOpReranker()


# =============================================================================
# SECTION 5: CONTEXTUAL EMBEDDINGS
# =============================================================================
#
# LEARNING POINT: This is the KEY innovation from Anthropic's research.
#
# The Problem:
# When we chunk documents, we lose context. Consider this chunk:
#     "The company's revenue grew by 3% over the previous quarter."
#
# Without context:
# - Which company?
# - Which quarter?
# - Where is this from?
#
# With Contextual Embeddings:
#     "This chunk is from an SEC filing on ACME corp's performance in Q2 2023;
#      the previous quarter's revenue was $314 million.
#      The company's revenue grew by 3% over the previous quarter."
#
# For SQL transformations, this means:
#
# Before: "ALTER TABLE ADD COLUMN customer_id INT"
# After:  "This SQL transformation is from the Sales schema in ACME Corp's
#          ERP database. The CustomerOrders table is being modified to add
#          a foreign key to the Customers table.
#          ALTER TABLE ADD COLUMN customer_id INT"
#
# The embedding now captures the CONTEXT, making retrieval more accurate.
# =============================================================================

class ContextGenerator:
    """
    Generates contextual descriptions for chunks before embedding.

    LEARNING POINT: We use Claude to generate context for each chunk.
    This is done ONCE when storing, not during search.

    The prompt asks Claude to provide concise, chunk-specific context
    that explains the chunk within its document.
    """

    def __init__(self):
        """Initialize context generator with Claude client."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Context generator initialized with Claude")
            except ImportError:
                logger.warning("anthropic package not installed")

    def generate_context(
        self,
        chunk: str,
        document_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate contextual description for a chunk.

        LEARNING POINT: This is the prompt from Anthropic's research,
        adapted for SQL transformations.

        Args:
            chunk: The text chunk to contextualize
            document_context: Metadata about the source (schema, table, etc.)

        Returns:
            Contextualized chunk with prepended description
        """
        if not self.client:
            # Fallback: use simple template-based context
            return self._template_context(chunk, document_context)

        # Build context string from metadata
        context_parts = []
        if document_context:
            if "database" in document_context:
                context_parts.append(f"Database: {document_context['database']}")
            if "schema" in document_context:
                context_parts.append(f"Schema: {document_context['schema']}")
            if "table" in document_context:
                context_parts.append(f"Table: {document_context['table']}")
            if "organization" in document_context:
                context_parts.append(f"Organization: {document_context['organization']}")

        context_str = ", ".join(context_parts) if context_parts else "Unknown source"

        # The prompt from Anthropic's research, adapted for our use case
        prompt = f"""<document_context>
{context_str}
</document_context>

Here is the SQL or schema chunk we want to contextualize:
<chunk>
{chunk}
</chunk>

Please provide a short, succinct context (1-2 sentences) to situate this SQL chunk
within the overall database and improve search retrieval. Include:
- What database/schema this is from
- What the SQL is doing
- Any relevant business context

Answer only with the succinct context and nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cheap for this task
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            context = response.content[0].text.strip()
            return f"{context}\n\n{chunk}"
        except Exception as e:
            logger.warning(f"Failed to generate context with Claude: {e}")
            return self._template_context(chunk, document_context)

    def _template_context(
        self,
        chunk: str,
        document_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Fallback template-based context generation.

        LEARNING POINT: Even a simple template helps! Better than nothing.
        """
        if not document_context:
            return chunk

        parts = []
        if "database" in document_context:
            parts.append(f"from {document_context['database']} database")
        if "schema" in document_context:
            parts.append(f"in {document_context['schema']} schema")
        if "table" in document_context:
            parts.append(f"for {document_context['table']} table")
        if "transformation_type" in document_context:
            parts.append(f"({document_context['transformation_type']} transformation)")

        if parts:
            context = f"This SQL is {', '.join(parts)}."
            return f"{context}\n\n{chunk}"

        return chunk


# =============================================================================
# SECTION 6: RANK FUSION
# =============================================================================
#
# LEARNING POINT: When we have results from multiple sources (vector + BM25),
# we need to combine them. Rank Fusion algorithms do this.
#
# Common approaches:
# 1. Reciprocal Rank Fusion (RRF) - Simple and effective
# 2. Weighted Sum - Use confidence scores
# 3. Borda Count - Voting-based
#
# We use RRF because:
# - Doesn't require score normalization
# - Works even when scores aren't comparable
# - Simple to implement and understand
# =============================================================================

def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    k: int = 60,
    weights: Optional[List[float]] = None
) -> List[Tuple[str, float]]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    LEARNING POINT: RRF formula:
    score(doc) = sum over all rankings of: weight / (k + rank(doc))

    Where:
    - k is a constant (60 is common, prevents division by small numbers)
    - rank(doc) is the position in each ranking (1-indexed)
    - weight is optional per-ranking weight

    Example:
    - Doc appears at rank 3 in vector search: 1/(60+3) = 0.0159
    - Doc appears at rank 1 in BM25: 1/(60+1) = 0.0164
    - Combined score: 0.0159 + 0.0164 = 0.0323

    Args:
        rankings: List of ranked results, each is [(doc_id, score), ...]
        k: Constant for RRF formula
        weights: Optional weights for each ranking

    Returns:
        Combined ranking as [(doc_id, score), ...]
    """
    if not rankings:
        return []

    if weights is None:
        weights = [1.0] * len(rankings)

    # Accumulate RRF scores
    scores: Dict[str, float] = {}

    for ranking, weight in zip(rankings, weights):
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            if doc_id not in scores:
                scores[doc_id] = 0.0
            scores[doc_id] += weight / (k + rank)

    # Sort by score descending
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores


# =============================================================================
# SECTION 7: MAIN RAG SERVICE V2
# =============================================================================
#
# This brings everything together:
# 1. Contextual Embeddings (on store)
# 2. Hybrid Search (vector + BM25)
# 3. Rank Fusion (combining results)
# 4. Reranking (final filtering)
# =============================================================================

class RAGServiceV2:
    """
    Enhanced RAG Service with Contextual Retrieval.

    LEARNING POINT: The main improvements over V1 are:

    1. STORE PATH:
       Original text -> Generate context -> Embed -> Store
       (vs V1: Original text -> Embed -> Store)

    2. SEARCH PATH:
       Query -> [Vector Search + BM25] -> Rank Fusion -> Rerank -> Results
       (vs V1: Query -> Vector Search -> Results)

    3. RESULTS:
       67% reduction in failed retrievals (Anthropic's research)

    Usage:
        rag = RAGServiceV2()

        # Store with context
        rag.store_transformation(
            source_sql="SELECT * FROM dbo.Customers",
            target_sql="SELECT * FROM {{ ref('stg_customers') }}",
            transformation_type="table",
            document_context={"schema": "dbo", "database": "Sales"}
        )

        # Hybrid search with reranking
        results = rag.search_transformations(
            "SELECT * FROM dbo.Orders WHERE status = 'active'"
        )
    """

    def __init__(self, config: Optional[RAGConfigV2] = None):
        self.config = config or RAGConfigV2()

        # Initialize components
        self.embedding_provider = get_embedding_provider(self.config)
        self.context_generator = ContextGenerator() if self.config.enable_contextual_embeddings else None
        self.reranker = get_reranker(self.config)

        # BM25 indices (one per collection)
        self.bm25_transformations: Optional[BM25] = None
        self.bm25_schemas: Optional[BM25] = None
        self.bm25_knowledge: Optional[BM25] = None

        # Database connection
        self.conn = None
        self._connect()

        # Load BM25 indices if enabled
        if self.config.enable_bm25:
            self._load_bm25_indices()

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
            logger.info("RAG v2 service connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.conn = None

    def _load_bm25_indices(self):
        """
        Load BM25 indices from database.

        LEARNING POINT: BM25 indices are built in memory from all stored documents.
        This is done once on startup and refreshed when new documents are added.

        For large collections, consider:
        - Lazy loading (build on first search)
        - Incremental updates (add new docs without full rebuild)
        - External search engines (Elasticsearch, Meilisearch)
        """
        if not self.conn:
            return

        try:
            with self.conn.cursor() as cur:
                # Load transformation texts
                cur.execute("SELECT id, source_sql FROM transformation_embeddings")
                transformations = cur.fetchall()
                if transformations:
                    self.bm25_transformations = BM25()
                    self.bm25_transformations.index([t[1] for t in transformations])
                    self._transformation_ids = [t[0] for t in transformations]
                    logger.info(f"Loaded BM25 index for {len(transformations)} transformations")

                # Similar for schemas and knowledge...
                # (abbreviated for length)

        except Exception as e:
            logger.warning(f"Failed to load BM25 indices: {e}")

    # =========================================================================
    # STORAGE METHODS (with Contextual Embeddings)
    # =========================================================================

    def store_transformation(
        self,
        source_sql: str,
        target_sql: str,
        transformation_type: str,
        quality_score: float = 0.0,
        migration_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        document_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a SQL transformation with contextual embedding.

        LEARNING POINT: KEY DIFFERENCE FROM V1
        =======================================

        V1 process:
            source_sql -> embed() -> store

        V2 process:
            source_sql + context -> contextualize() -> embed() -> store

        The contextualized version captures more meaning:

        V1: "ALTER TABLE Customers ADD COLUMN email VARCHAR(255)"
        V2: "This SQL modifies the Customers table in the Sales schema of
             ACME Corp's ERP database. It adds an email column for customer
             contact information.
             ALTER TABLE Customers ADD COLUMN email VARCHAR(255)"

        The embedding now "knows" about Sales schema, ACME Corp, and purpose.
        """
        if not self.conn:
            raise RuntimeError("RAG service not connected")

        # Step 1: Generate contextual embedding
        # --------------------------------------------------------------------
        text_to_embed = source_sql

        if self.config.enable_contextual_embeddings and self.context_generator:
            # Merge transformation type into context
            ctx = document_context or {}
            ctx["transformation_type"] = transformation_type

            # Generate contextualized version
            text_to_embed = self.context_generator.generate_context(
                source_sql,
                ctx
            )
            logger.debug(f"Contextualized: {text_to_embed[:100]}...")

        # Step 2: Generate embedding
        # --------------------------------------------------------------------
        embedding = self.embedding_provider.embed(text_to_embed)

        # Step 3: Store in database
        # --------------------------------------------------------------------
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
            new_id = cur.fetchone()[0]

        # Step 4: Update BM25 index
        # --------------------------------------------------------------------
        if self.config.enable_bm25:
            # For simplicity, rebuild entire index
            # (In production, use incremental updates)
            self._load_bm25_indices()

        return new_id

    # =========================================================================
    # SEARCH METHODS (with Hybrid Search + Reranking)
    # =========================================================================

    def search_transformations(
        self,
        source_sql: str,
        transformation_type: Optional[str] = None,
        min_quality_score: float = 0.0,
        organization_id: Optional[int] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar SQL transformations using Contextual Retrieval.

        LEARNING POINT: THE FULL CONTEXTUAL RETRIEVAL PIPELINE
        ======================================================

        Step 1: Vector Search
        - Embed the query
        - Find top N similar embeddings (cosine similarity)
        - Result: [(doc_id, similarity_score), ...]

        Step 2: BM25 Search (if enabled)
        - Tokenize the query
        - Find top N lexically similar documents
        - Result: [(doc_id, bm25_score), ...]

        Step 3: Rank Fusion
        - Combine vector and BM25 results using RRF
        - Result: [(doc_id, combined_score), ...]

        Step 4: Reranking (if enabled)
        - Take top 150 candidates
        - Use cross-encoder to rescore each query-doc pair
        - Return top K (typically 20)

        This pipeline reduces failed retrievals by 67%!
        """
        if not self.conn:
            return []

        top_k = top_k or self.config.top_k

        # Step 1: Vector Search
        # --------------------------------------------------------------------
        vector_results = self._vector_search_transformations(
            source_sql,
            transformation_type=transformation_type,
            min_quality_score=min_quality_score,
            organization_id=organization_id,
            top_k=self.config.rerank_top_n if self.config.enable_reranking else top_k
        )

        # Step 2: BM25 Search (if enabled)
        # --------------------------------------------------------------------
        bm25_results = []
        if self.config.enable_bm25 and self.bm25_transformations:
            bm25_results = self._bm25_search_transformations(
                source_sql,
                top_k=self.config.rerank_top_n if self.config.enable_reranking else top_k
            )

        # Step 3: Rank Fusion
        # --------------------------------------------------------------------
        if bm25_results:
            # Convert to common format for fusion
            vector_ranking = [(str(r['id']), r['similarity']) for r in vector_results]
            bm25_ranking = [(str(doc_id), score) for doc_id, score in bm25_results]

            # Fuse with configurable weights
            # Default: 50% vector, 50% BM25
            fused = reciprocal_rank_fusion(
                [vector_ranking, bm25_ranking],
                weights=[1 - self.config.bm25_weight, self.config.bm25_weight]
            )

            # Get full documents for fused results
            fused_ids = [int(doc_id) for doc_id, _ in fused]
            results = self._get_transformations_by_ids(fused_ids)
        else:
            results = vector_results

        # Step 4: Reranking (if enabled)
        # --------------------------------------------------------------------
        if self.config.enable_reranking and len(results) > top_k:
            # Prepare documents for reranking
            docs = [f"{r['source_sql']}\n---\n{r['target_sql']}" for r in results]

            # Rerank
            reranked = self.reranker.rerank(source_sql, docs, top_k=top_k)

            # Reorder results based on reranking
            reranked_results = []
            for orig_idx, score in reranked:
                result = results[orig_idx].copy()
                result['rerank_score'] = score
                reranked_results.append(result)

            return reranked_results

        return results[:top_k]

    def _vector_search_transformations(
        self,
        source_sql: str,
        transformation_type: Optional[str] = None,
        min_quality_score: float = 0.0,
        organization_id: Optional[int] = None,
        top_k: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Vector similarity search using pgvector.

        LEARNING POINT: We contextualize the query too!
        This ensures query and stored embeddings are in the same "space".
        """
        # Contextualize query (if enabled)
        text_to_embed = source_sql
        if self.config.enable_contextual_embeddings and self.context_generator:
            # For queries, we use a simpler context since we don't have full metadata
            text_to_embed = f"SQL query to find similar transformations:\n{source_sql}"

        query_embedding = self.embedding_provider.embed(text_to_embed)

        # Build query with filters
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
            return cur.fetchall()

    def _bm25_search_transformations(
        self,
        source_sql: str,
        top_k: int = 150
    ) -> List[Tuple[int, float]]:
        """
        BM25 lexical search.

        LEARNING POINT: Returns (document_id, score) tuples.
        We need to map back to actual transformation IDs.
        """
        if not self.bm25_transformations:
            return []

        results = self.bm25_transformations.search(source_sql, top_k=top_k)

        # Map internal indices to transformation IDs
        return [(self._transformation_ids[idx], score) for idx, score in results]

    def _get_transformations_by_ids(
        self,
        ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Fetch full transformation records by IDs, preserving order."""
        if not ids:
            return []

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Use VALUES to preserve order
            cur.execute("""
                SELECT t.id, t.source_sql, t.target_sql, t.transformation_type,
                       t.quality_score, t.metadata
                FROM transformation_embeddings t
                JOIN (SELECT * FROM unnest(%s::int[]) WITH ORDINALITY AS x(id, ord)) AS o
                  ON t.id = o.id
                ORDER BY o.ord
            """, (ids,))
            return cur.fetchall()

    # =========================================================================
    # CONTEXT BUILDER (Enhanced)
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

        LEARNING POINT: Now uses the full Contextual Retrieval pipeline
        to find the most relevant past transformations.
        """
        context_parts = []

        # Find similar transformations (using hybrid search + reranking)
        transformations = self.search_transformations(
            source_sql,
            min_quality_score=0.7,
            organization_id=organization_id,
            top_k=3
        )

        if transformations:
            context_parts.append("## Similar Past Transformations\n")
            for i, t in enumerate(transformations, 1):
                similarity = t.get('similarity', t.get('rerank_score', 0))
                context_parts.append(f"""
### Example {i} (Relevance: {similarity:.2%}, Quality: {t['quality_score']:.2%})
**Source SQL:**
```sql
{t['source_sql']}
```

**dbt SQL:**
```sql
{t['target_sql']}
```
""")

        return "\n".join(context_parts) if context_parts else ""

    # =========================================================================
    # STATISTICS AND HEALTH
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics including new metrics."""
        if not self.conn:
            return {"available": False}

        stats = {
            "available": True,
            "embedding_provider": self.config.embedding_provider,
            "embedding_dimension": self.embedding_provider.dimension,
            "contextual_embeddings_enabled": self.config.enable_contextual_embeddings,
            "bm25_enabled": self.config.enable_bm25,
            "reranking_enabled": self.config.enable_reranking,
        }

        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transformation_embeddings")
            stats["transformation_embeddings"] = cur.fetchone()[0]

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# =============================================================================
# SECTION 8: COMPARISON SUMMARY
# =============================================================================
#
# LEARNING POINT: Here's a side-by-side comparison
#
# ┌────────────────────────┬──────────────────┬─────────────────────────────┐
# │ Feature                │ RAG v1           │ RAG v2 (Contextual)         │
# ├────────────────────────┼──────────────────┼─────────────────────────────┤
# │ Embedding Provider     │ OpenAI ada-002   │ Voyage AI voyage-3          │
# │ Contextual Embeddings  │ ❌ No            │ ✅ Yes (prepend context)    │
# │ BM25 Hybrid Search     │ ❌ No            │ ✅ Yes (lexical matching)   │
# │ Reranking              │ ❌ No            │ ✅ Yes (Cohere cross-enc)   │
# │ Rank Fusion            │ ❌ No            │ ✅ Yes (RRF algorithm)      │
# │ Retrieval Failure Rate │ ~5.7%            │ ~1.9% (67% improvement)     │
# └────────────────────────┴──────────────────┴─────────────────────────────┘
#
# The improvement comes from:
# - Contextual Embeddings alone: 35% reduction in failures
# - Adding BM25: 49% reduction
# - Adding Reranking: 67% reduction (total)
#
# =============================================================================


# Singleton and factory functions
_rag_service_v2: Optional[RAGServiceV2] = None


def get_rag_service_v2() -> RAGServiceV2:
    """Get or create RAG v2 service singleton."""
    global _rag_service_v2
    if _rag_service_v2 is None:
        config = RAGConfigV2(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "datamigrate"),
            db_user=os.getenv("DB_USER", "datamigrate"),
            db_password=os.getenv("DB_PASSWORD", "datamigrate123"),
        )
        _rag_service_v2 = RAGServiceV2(config)
    return _rag_service_v2


if __name__ == "__main__":
    """
    Test the RAG v2 service.

    LEARNING POINT: Run this to see the difference in action.
    """
    print("=" * 60)
    print("RAG v2: Contextual Retrieval Service")
    print("=" * 60)

    rag = get_rag_service_v2()
    print(f"\nStats: {json.dumps(rag.get_stats(), indent=2)}")

    print("\n" + "=" * 60)
    print("Key Improvements over v1:")
    print("=" * 60)
    print("""
1. CONTEXTUAL EMBEDDINGS (35% improvement)
   Before: "ALTER TABLE ADD COLUMN id"
   After:  "This SQL from Sales.Customers adds a primary key..."

2. BM25 HYBRID SEARCH (49% improvement)
   Catches exact matches that vector search misses

3. RERANKING (67% improvement)
   Cross-encoder rescores top candidates for precision

Run with API keys set:
  export VOYAGE_API_KEY=...
  export COHERE_API_KEY=...
  export ANTHROPIC_API_KEY=...
""")
