# MSSQL Extractor Agent

## Status: Production (95%)

## Overview
The MSSQL Extractor Agent connects to SQL Server databases and extracts complete schema metadata including tables, columns, relationships, indexes, views, and stored procedures.

## File Locations
- Main: `agents/mssql_extraction_agent.py`
- API Integration: `agents/api.py`
- Tests: `tests/test_mssql_extraction.py`

## Current Capabilities
- [x] Connect to MSSQL databases via pyodbc
- [x] Extract table schemas (columns, types, constraints)
- [x] Detect primary and foreign key relationships
- [x] Map indexes and their configurations
- [x] Extract views and stored procedures
- [x] Generate metadata JSON output
- [x] Handle multiple schemas
- [x] Connection pooling

## Integration Status
- [x] API endpoint `/migrations/{id}/extract`
- [x] Frontend integration
- [x] Progress tracking
- [x] Error handling
- [x] Retry logic

## TODO
- [ ] Add support for temporal tables
- [ ] Improve handling of computed columns
- [ ] Add schema diffing capability
- [ ] Performance optimization for large databases (1000+ tables)

## Testing Notes
- Tested with SQL Server 2016, 2019, Azure SQL
- Handles databases up to 500 tables efficiently
- Connection timeout set to 30 seconds

## Dependencies
- pyodbc
- SQLAlchemy
- pandas

## Metrics
- Average extraction time: 2-5 minutes (100 tables)
- Success rate: 99%
- Memory usage: ~200MB peak

---
Last Updated: 2024-12-05
