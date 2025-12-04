"""
Documentation Agent - RAG-Powered Intelligent Documentation

This agent provides automatic documentation generation, semantic search,
knowledge base management, and intelligent Q&A for migration projects.
Part of the DataMigrate AI Eight-Agent Architecture.

Author: DataMigrate AI Team
Version: 1.0.0
"""

import os
import json
import logging
import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Types of documentation"""
    SCHEMA = "schema"
    MODEL = "model"
    PIPELINE = "pipeline"
    TRANSFORMATION = "transformation"
    RUNBOOK = "runbook"
    API = "api"
    USER_GUIDE = "user_guide"
    TECHNICAL = "technical"
    CHANGELOG = "changelog"
    GLOSSARY = "glossary"


class OutputFormat(str, Enum):
    """Output formats for documentation"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"
    PDF = "pdf"
    CONFLUENCE = "confluence"
    NOTION = "notion"


class SourceType(str, Enum):
    """Types of knowledge sources"""
    SQL = "sql"
    DBT_MODEL = "dbt_model"
    YAML = "yaml"
    MARKDOWN = "markdown"
    CODE = "code"
    API_SPEC = "api_spec"
    COMMENT = "comment"
    METADATA = "metadata"


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge for RAG"""
    chunk_id: str
    content: str
    source: str
    source_type: SourceType
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Result from semantic search"""
    chunk: KnowledgeChunk
    score: float
    highlights: List[str] = field(default_factory=list)


@dataclass
class DocumentSection:
    """A section of generated documentation"""
    title: str
    content: str
    level: int = 1
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedDocument:
    """A complete generated document"""
    doc_id: str
    title: str
    doc_type: DocumentType
    sections: List[DocumentSection]
    format: OutputFormat
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    source_references: List[str] = field(default_factory=list)


@dataclass
class QAResponse:
    """Response to a question"""
    question: str
    answer: str
    confidence: float
    sources: List[str] = field(default_factory=list)
    related_questions: List[str] = field(default_factory=list)
    follow_up_actions: List[str] = field(default_factory=list)


class DocumentationAgent:
    """
    Documentation Agent with RAG capabilities.

    Capabilities:
    - Automatic Documentation Generation
    - Semantic Search across Knowledge Base
    - Intelligent Q&A
    - Schema Documentation
    - dbt Model Documentation
    - Transformation Lineage Docs
    - API Documentation
    - Multi-format Export
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the Documentation Agent"""
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            max_tokens=8192
        )

        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # Knowledge base storage
        self.knowledge_base: Dict[str, KnowledgeChunk] = {}
        self.vector_store: Optional[FAISS] = None

        # Document templates
        self.templates = self._initialize_templates()

        # Initialize the LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("Documentation Agent initialized successfully")

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize documentation templates"""
        return {
            DocumentType.SCHEMA.value: """
# Schema Documentation: {name}

## Overview
{description}

## Tables

{tables}

## Relationships

{relationships}

## Indexes

{indexes}

---
*Generated by DataMigrate AI Documentation Agent*
*Last updated: {timestamp}*
""",
            DocumentType.MODEL.value: """
# dbt Model: {name}

## Description
{description}

## Source Tables
{sources}

## Columns

| Column | Type | Description | Tests |
|--------|------|-------------|-------|
{columns}

## SQL Logic
```sql
{sql}
```

## Dependencies
{dependencies}

## Usage Examples
{examples}

---
*Generated by DataMigrate AI Documentation Agent*
""",
            DocumentType.TRANSFORMATION.value: """
# Transformation: {name}

## Purpose
{purpose}

## Source to Target Mapping

| Source Column | Transformation | Target Column |
|--------------|----------------|---------------|
{mappings}

## Business Rules
{business_rules}

## Data Quality Checks
{quality_checks}

---
*Generated by DataMigrate AI Documentation Agent*
""",
            DocumentType.RUNBOOK.value: """
# Runbook: {name}

## Overview
{overview}

## Prerequisites
{prerequisites}

## Step-by-Step Instructions

{steps}

## Troubleshooting

{troubleshooting}

## Contacts
{contacts}

---
*Generated by DataMigrate AI Documentation Agent*
""",
            DocumentType.API.value: """
# API Documentation: {name}

## Base URL
`{base_url}`

## Authentication
{authentication}

## Endpoints

{endpoints}

## Error Codes

| Code | Description |
|------|-------------|
{error_codes}

---
*Generated by DataMigrate AI Documentation Agent*
"""
        }

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for documentation"""
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("ingest_source", self._ingest_source_node)
        workflow.add_node("analyze_content", self._analyze_content_node)
        workflow.add_node("generate_documentation", self._generate_documentation_node)
        workflow.add_node("search_knowledge", self._search_knowledge_node)
        workflow.add_node("answer_question", self._answer_question_node)
        workflow.add_node("format_output", self._format_output_node)

        # Set entry point
        workflow.set_entry_point("ingest_source")

        # Add conditional edges
        workflow.add_conditional_edges(
            "ingest_source",
            self._route_after_ingest,
            {
                "analyze": "analyze_content",
                "search": "search_knowledge",
                "qa": "answer_question",
                "end": END
            }
        )

        workflow.add_edge("analyze_content", "generate_documentation")
        workflow.add_edge("generate_documentation", "format_output")
        workflow.add_edge("search_knowledge", "format_output")
        workflow.add_edge("answer_question", "format_output")
        workflow.add_edge("format_output", END)

        return workflow.compile()

    def _route_after_ingest(self, state: dict) -> str:
        """Route based on operation type"""
        operation = state.get("operation", "analyze")

        if operation == "search":
            return "search"
        elif operation == "qa":
            return "qa"
        elif operation in ["generate", "analyze"]:
            return "analyze"
        else:
            return "end"

    async def _ingest_source_node(self, state: dict) -> dict:
        """Ingest source content into knowledge base"""
        content = state.get("content", "")
        source = state.get("source", "unknown")
        source_type = state.get("source_type", SourceType.CODE.value)

        if not content:
            return state

        # Split content into chunks
        chunks = self.text_splitter.split_text(content)

        # Create knowledge chunks
        knowledge_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = hashlib.md5(f"{source}_{i}_{chunk_text[:50]}".encode()).hexdigest()

            chunk = KnowledgeChunk(
                chunk_id=chunk_id,
                content=chunk_text,
                source=source,
                source_type=SourceType(source_type),
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )

            self.knowledge_base[chunk_id] = chunk
            knowledge_chunks.append(chunk)

        # Update vector store
        if knowledge_chunks:
            texts = [c.content for c in knowledge_chunks]
            metadatas = [{"chunk_id": c.chunk_id, "source": c.source} for c in knowledge_chunks]

            if self.vector_store is None:
                self.vector_store = FAISS.from_texts(
                    texts,
                    self.embeddings,
                    metadatas=metadatas
                )
            else:
                self.vector_store.add_texts(texts, metadatas=metadatas)

        state["chunks_created"] = len(knowledge_chunks)
        state["chunk_ids"] = [c.chunk_id for c in knowledge_chunks]

        return state

    async def _analyze_content_node(self, state: dict) -> dict:
        """Analyze content structure and extract key information"""
        content = state.get("content", "")
        source_type = state.get("source_type", SourceType.CODE.value)
        doc_type = state.get("doc_type", DocumentType.TECHNICAL.value)

        # Use LLM to analyze content
        system_prompt = f"""You are a technical documentation expert. Analyze the following {source_type}
        content and extract key information for generating {doc_type} documentation.

        Return a JSON object with:
        - title: Document title
        - summary: Brief summary (1-2 sentences)
        - key_concepts: List of main concepts/entities
        - structure: Suggested documentation structure
        - technical_details: Important technical details to document
        - relationships: Any relationships between entities
        - examples: Suggested examples to include
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Content to analyze:\n\n{content[:4000]}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            analysis = json.loads(response.content)
            state["analysis"] = analysis
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            state["analysis"] = {"error": str(e)}

        return state

    async def _generate_documentation_node(self, state: dict) -> dict:
        """Generate documentation from analyzed content"""
        analysis = state.get("analysis", {})
        doc_type = state.get("doc_type", DocumentType.TECHNICAL.value)
        content = state.get("content", "")

        # Build documentation prompt based on type
        system_prompt = f"""You are an expert technical writer specializing in data engineering documentation.
        Generate comprehensive {doc_type} documentation based on the provided analysis and content.

        Requirements:
        1. Use clear, concise language
        2. Include practical examples where appropriate
        3. Structure content logically with headers and sections
        4. Add cross-references where relevant
        5. Include best practices and warnings
        6. Use markdown formatting

        Return the documentation as a JSON object with:
        - title: Document title
        - sections: Array of section objects with 'title', 'content', 'level'
        - metadata: Any relevant metadata
        """

        context = {
            "analysis": analysis,
            "content_preview": content[:2000],
            "doc_type": doc_type
        }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate documentation based on:\n{json.dumps(context, indent=2)}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            doc_data = json.loads(response.content)

            sections = [
                DocumentSection(
                    title=s.get("title", "Section"),
                    content=s.get("content", ""),
                    level=s.get("level", 1)
                )
                for s in doc_data.get("sections", [])
            ]

            document = GeneratedDocument(
                doc_id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
                title=doc_data.get("title", "Documentation"),
                doc_type=DocumentType(doc_type),
                sections=sections,
                format=OutputFormat(state.get("output_format", "markdown")),
                source_references=[state.get("source", "unknown")]
            )

            state["document"] = self._document_to_dict(document)

        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            state["document"] = {"error": str(e)}

        return state

    async def _search_knowledge_node(self, state: dict) -> dict:
        """Search knowledge base using semantic search"""
        query = state.get("query", "")
        top_k = state.get("top_k", 5)

        if not query or self.vector_store is None:
            state["search_results"] = []
            return state

        # Perform semantic search
        results = self.vector_store.similarity_search_with_score(query, k=top_k)

        search_results = []
        for doc, score in results:
            chunk_id = doc.metadata.get("chunk_id")
            chunk = self.knowledge_base.get(chunk_id)

            if chunk:
                search_results.append(SearchResult(
                    chunk=chunk,
                    score=1 - score,  # Convert distance to similarity
                    highlights=self._extract_highlights(query, chunk.content)
                ))

        state["search_results"] = [
            {
                "content": r.chunk.content,
                "source": r.chunk.source,
                "score": r.score,
                "highlights": r.highlights
            }
            for r in search_results
        ]

        return state

    async def _answer_question_node(self, state: dict) -> dict:
        """Answer a question using RAG"""
        question = state.get("question", "")

        if not question:
            state["answer"] = {"error": "No question provided"}
            return state

        # Search for relevant context
        context_chunks = []
        if self.vector_store:
            results = self.vector_store.similarity_search(question, k=5)
            context_chunks = [doc.page_content for doc in results]

        # Generate answer using LLM with context
        system_prompt = """You are a knowledgeable data engineering assistant.
        Answer the user's question based on the provided context from the knowledge base.

        If the context doesn't contain enough information, acknowledge this and provide
        general guidance based on best practices.

        Return a JSON object with:
        - answer: Your detailed answer
        - confidence: Confidence level (0-1) based on context relevance
        - sources: List of relevant source references
        - related_questions: 2-3 related questions the user might want to ask
        - follow_up_actions: Suggested next steps if applicable
        """

        context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No relevant context found."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            answer_data = json.loads(response.content)

            qa_response = QAResponse(
                question=question,
                answer=answer_data.get("answer", "Unable to generate answer"),
                confidence=answer_data.get("confidence", 0.5),
                sources=answer_data.get("sources", []),
                related_questions=answer_data.get("related_questions", []),
                follow_up_actions=answer_data.get("follow_up_actions", [])
            )

            state["answer"] = self._qa_response_to_dict(qa_response)

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            state["answer"] = {"error": str(e), "question": question}

        return state

    async def _format_output_node(self, state: dict) -> dict:
        """Format output in the requested format"""
        output_format = state.get("output_format", OutputFormat.MARKDOWN.value)
        document = state.get("document")

        if document and "sections" in document:
            if output_format == OutputFormat.MARKDOWN.value:
                formatted = self._format_as_markdown(document)
            elif output_format == OutputFormat.HTML.value:
                formatted = self._format_as_html(document)
            elif output_format == OutputFormat.JSON.value:
                formatted = json.dumps(document, indent=2)
            else:
                formatted = self._format_as_markdown(document)

            state["formatted_output"] = formatted

        return state

    def _extract_highlights(self, query: str, content: str) -> List[str]:
        """Extract highlighted snippets matching query terms"""
        query_terms = query.lower().split()
        sentences = content.split(". ")
        highlights = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(term in sentence_lower for term in query_terms):
                highlights.append(sentence.strip())
                if len(highlights) >= 3:
                    break

        return highlights

    def _format_as_markdown(self, document: dict) -> str:
        """Format document as Markdown"""
        lines = [f"# {document.get('title', 'Documentation')}", ""]

        for section in document.get("sections", []):
            level = section.get("level", 1)
            header = "#" * (level + 1)
            lines.append(f"{header} {section.get('title', '')}")
            lines.append("")
            lines.append(section.get("content", ""))
            lines.append("")

        lines.extend([
            "---",
            f"*Generated by DataMigrate AI Documentation Agent*",
            f"*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])

        return "\n".join(lines)

    def _format_as_html(self, document: dict) -> str:
        """Format document as HTML"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{document.get('title', 'Documentation')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1, h2, h3 { color: #333; }",
            "code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }",
            "pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }",
            "</style>",
            "</head><body>",
            f"<h1>{document.get('title', 'Documentation')}</h1>"
        ]

        for section in document.get("sections", []):
            level = section.get("level", 1) + 1
            html_parts.append(f"<h{level}>{section.get('title', '')}</h{level}>")
            content = section.get("content", "").replace("\n", "<br>")
            html_parts.append(f"<p>{content}</p>")

        html_parts.extend([
            "<hr>",
            "<footer><em>Generated by DataMigrate AI Documentation Agent</em></footer>",
            "</body></html>"
        ])

        return "\n".join(html_parts)

    def _document_to_dict(self, doc: GeneratedDocument) -> dict:
        """Convert GeneratedDocument to dictionary"""
        return {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "doc_type": doc.doc_type.value,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "level": s.level
                }
                for s in doc.sections
            ],
            "format": doc.format.value,
            "created_at": doc.created_at.isoformat(),
            "version": doc.version,
            "source_references": doc.source_references
        }

    def _qa_response_to_dict(self, response: QAResponse) -> dict:
        """Convert QAResponse to dictionary"""
        return {
            "question": response.question,
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "related_questions": response.related_questions,
            "follow_up_actions": response.follow_up_actions
        }

    # Public API Methods

    async def ingest_document(
        self,
        content: str,
        source: str,
        source_type: SourceType = SourceType.CODE
    ) -> Dict[str, Any]:
        """
        Ingest a document into the knowledge base.

        Args:
            content: Document content
            source: Source identifier (file path, URL, etc.)
            source_type: Type of source content

        Returns:
            Ingestion results with chunk information
        """
        logger.info(f"Ingesting document from {source}")

        state = {
            "content": content,
            "source": source,
            "source_type": source_type.value,
            "operation": "ingest"
        }

        # Only run ingestion
        result = await self._ingest_source_node(state)

        return {
            "source": source,
            "chunks_created": result.get("chunks_created", 0),
            "chunk_ids": result.get("chunk_ids", []),
            "knowledge_base_size": len(self.knowledge_base)
        }

    async def generate_schema_docs(
        self,
        schema: Dict[str, Any],
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Dict[str, Any]:
        """
        Generate documentation for a database schema.

        Args:
            schema: Schema definition (tables, columns, relationships)
            output_format: Desired output format

        Returns:
            Generated schema documentation
        """
        logger.info(f"Generating schema documentation")

        # Format schema content
        content = json.dumps(schema, indent=2)

        state = {
            "content": content,
            "source": "schema",
            "source_type": SourceType.SQL.value,
            "doc_type": DocumentType.SCHEMA.value,
            "output_format": output_format.value,
            "operation": "generate"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "document": result.get("document"),
            "formatted_output": result.get("formatted_output")
        }

    async def generate_dbt_model_docs(
        self,
        model_sql: str,
        model_yaml: Optional[str] = None,
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Dict[str, Any]:
        """
        Generate documentation for a dbt model.

        Args:
            model_sql: SQL content of the model
            model_yaml: Optional YAML schema for the model
            output_format: Desired output format

        Returns:
            Generated model documentation
        """
        logger.info("Generating dbt model documentation")

        content = f"-- SQL Model\n{model_sql}"
        if model_yaml:
            content += f"\n\n-- YAML Schema\n{model_yaml}"

        state = {
            "content": content,
            "source": "dbt_model",
            "source_type": SourceType.DBT_MODEL.value,
            "doc_type": DocumentType.MODEL.value,
            "output_format": output_format.value,
            "operation": "generate"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "document": result.get("document"),
            "formatted_output": result.get("formatted_output")
        }

    async def generate_transformation_docs(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        transformations: List[Dict[str, Any]],
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Dict[str, Any]:
        """
        Generate documentation for data transformations.

        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            transformations: List of transformation rules
            output_format: Desired output format

        Returns:
            Generated transformation documentation
        """
        logger.info("Generating transformation documentation")

        content = json.dumps({
            "source_schema": source_schema,
            "target_schema": target_schema,
            "transformations": transformations
        }, indent=2)

        state = {
            "content": content,
            "source": "transformation",
            "source_type": SourceType.METADATA.value,
            "doc_type": DocumentType.TRANSFORMATION.value,
            "output_format": output_format.value,
            "operation": "generate"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "document": result.get("document"),
            "formatted_output": result.get("formatted_output")
        }

    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search the knowledge base using semantic search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Search results with relevance scores
        """
        logger.info(f"Searching knowledge base: {query[:50]}...")

        state = {
            "query": query,
            "top_k": top_k,
            "operation": "search"
        }

        # Run search directly
        result = await self._search_knowledge_node(state)

        return {
            "query": query,
            "results": result.get("search_results", []),
            "total_results": len(result.get("search_results", []))
        }

    async def ask_question(
        self,
        question: str
    ) -> Dict[str, Any]:
        """
        Ask a question about the knowledge base.

        Args:
            question: Natural language question

        Returns:
            Answer with sources and confidence
        """
        logger.info(f"Answering question: {question[:50]}...")

        state = {
            "question": question,
            "operation": "qa"
        }

        result = await self._answer_question_node(state)

        return result.get("answer", {"error": "Unable to generate answer"})

    async def generate_runbook(
        self,
        process_name: str,
        steps: List[Dict[str, Any]],
        prerequisites: List[str],
        troubleshooting: List[Dict[str, str]],
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Dict[str, Any]:
        """
        Generate a runbook for a process.

        Args:
            process_name: Name of the process
            steps: List of process steps
            prerequisites: Required prerequisites
            troubleshooting: Common issues and solutions
            output_format: Desired output format

        Returns:
            Generated runbook
        """
        logger.info(f"Generating runbook: {process_name}")

        content = json.dumps({
            "process_name": process_name,
            "steps": steps,
            "prerequisites": prerequisites,
            "troubleshooting": troubleshooting
        }, indent=2)

        state = {
            "content": content,
            "source": "runbook",
            "source_type": SourceType.METADATA.value,
            "doc_type": DocumentType.RUNBOOK.value,
            "output_format": output_format.value,
            "operation": "generate"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "document": result.get("document"),
            "formatted_output": result.get("formatted_output")
        }

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        source_counts = {}
        for chunk in self.knowledge_base.values():
            source = chunk.source
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            "total_chunks": len(self.knowledge_base),
            "sources": source_counts,
            "has_vector_store": self.vector_store is not None
        }

    def clear_knowledge_base(self) -> None:
        """Clear the entire knowledge base"""
        self.knowledge_base.clear()
        self.vector_store = None
        logger.info("Knowledge base cleared")


# Example usage and testing
async def main():
    """Example usage of the Documentation Agent"""

    # Sample SQL content
    sample_sql = """
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE orders (
        order_id INT PRIMARY KEY,
        customer_id INT REFERENCES customers(customer_id),
        order_date DATE NOT NULL,
        total_amount DECIMAL(10, 2),
        status VARCHAR(50) DEFAULT 'pending'
    );
    """

    # Sample dbt model
    sample_dbt_model = """
    {{ config(materialized='table') }}

    SELECT
        c.customer_id,
        c.first_name || ' ' || c.last_name AS full_name,
        c.email,
        COUNT(o.order_id) AS total_orders,
        SUM(o.total_amount) AS lifetime_value,
        MAX(o.order_date) AS last_order_date
    FROM {{ ref('stg_customers') }} c
    LEFT JOIN {{ ref('stg_orders') }} o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.email
    """

    try:
        agent = DocumentationAgent()

        # Test document ingestion
        print("Ingesting SQL schema...")
        ingest_result = await agent.ingest_document(
            content=sample_sql,
            source="schema.sql",
            source_type=SourceType.SQL
        )
        print(f"Created {ingest_result['chunks_created']} chunks")

        # Test dbt model documentation
        print("\nGenerating dbt model documentation...")
        model_docs = await agent.generate_dbt_model_docs(sample_dbt_model)
        print(f"Generated document: {model_docs['document'].get('title', 'N/A')}")

        # Test semantic search
        print("\nSearching knowledge base...")
        search_results = await agent.search("customer orders relationship")
        print(f"Found {search_results['total_results']} results")

        # Test Q&A
        print("\nAsking a question...")
        answer = await agent.ask_question("What is the relationship between customers and orders?")
        print(f"Answer confidence: {answer.get('confidence', 0):.0%}")
        print(f"Answer: {answer.get('answer', 'N/A')[:200]}...")

        # Print knowledge base stats
        print("\nKnowledge base stats:")
        stats = agent.get_knowledge_base_stats()
        print(f"Total chunks: {stats['total_chunks']}")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the ANTHROPIC_API_KEY environment variable")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
