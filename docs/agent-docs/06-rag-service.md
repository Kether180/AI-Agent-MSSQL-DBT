# RAG Service

## Status: Beta (85%)

## Overview
The RAG (Retrieval-Augmented Generation) Service provides intelligent query assistance by indexing schema documentation and enabling natural language questions about data models.

## File Locations
- Service v1: `services/rag_service.py`
- Service v2: `services/rag_service_v2.py`
- Vector Store: `services/vector_store.py`
- API: `agents/api.py`

## Current Capabilities
- [x] Document indexing (schemas, models)
- [x] Semantic search
- [x] Question answering
- [x] SQL query generation
- [x] Context-aware responses
- [x] Embedding generation
- [x] Vector store management
- [ ] Feedback learning
- [ ] Multi-tenant isolation

## Two Implementations Available
1. **v1 (rag_service.py)**: Basic implementation with ChromaDB
2. **v2 (rag_service_v2.py)**: Enhanced with better chunking and retrieval

## Integration Status
- [x] Core RAG engine - COMPLETE
- [x] Vector storage - COMPLETE
- [ ] API endpoint - EXISTS BUT NOT USED
- [ ] Frontend chat interface - NOT CONNECTED
- [ ] Schema auto-indexing - NOT CONNECTED

## TODO - HIGH PRIORITY
1. [ ] Create frontend chat component
2. [ ] Add chat interface to dashboard
3. [ ] Auto-index schemas after extraction
4. [ ] Add conversation history
5. [ ] Implement feedback loop

## Integration Requirements
1. Add `/chat` API endpoint
2. Create ChatWidget component
3. Auto-index on migration completion
4. Add conversation persistence
5. Implement rate limiting

## Dependencies
- LangChain
- ChromaDB
- OpenAI API
- sentence-transformers

## Architecture
```
User Query -> Embedding -> Vector Search -> Context Retrieval -> LLM -> Response
```

## Metrics
- Response time: 2-5 seconds
- Relevance accuracy: ~85%
- Index size: ~10KB per table

---
Last Updated: 2024-12-05
