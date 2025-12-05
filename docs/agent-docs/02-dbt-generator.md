# dbt Generator Agent

## Status: Production (95%)

## Overview
The dbt Generator Agent transforms extracted MSSQL schemas into complete dbt projects with staging models, tests, and documentation following dbt best practices.

## File Locations
- Main: `agents/dbt_generator_agent.py`
- Templates: `agents/templates/`
- API Integration: `agents/api.py`

## Current Capabilities
- [x] Generate staging models from source tables
- [x] Create source YAML definitions
- [x] Generate dbt tests (not_null, unique, relationships)
- [x] Create schema.yml documentation
- [x] Apply correct data type mappings
- [x] Generate project configuration (dbt_project.yml)
- [x] Create profiles.yml templates
- [x] Handle incremental models
- [x] Support multiple target warehouses

## Supported Target Warehouses
- [x] Snowflake
- [x] BigQuery
- [x] Databricks
- [x] Redshift
- [x] Microsoft Fabric
- [x] Spark

## Integration Status
- [x] API endpoint `/migrations/{id}/generate`
- [x] Frontend file browser
- [x] ZIP download
- [x] Progress tracking

## TODO
- [ ] Add intermediate layer models
- [ ] Mart layer generation
- [ ] Custom naming conventions
- [ ] Advanced test generation

## Code Patterns
- Jinja2 templates for all model generation
- Type mapping dictionaries per warehouse
- Test generation based on constraints

## Dependencies
- Jinja2
- PyYAML
- dbt-core (for validation)

## Metrics
- Average generation time: 30-60 seconds
- Models per table: 1 (staging) + tests
- Success rate: 98%

---
Last Updated: 2024-12-05
