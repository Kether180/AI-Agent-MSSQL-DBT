# dbt Executor Agent

## Status: Beta (70%)

## Overview
The dbt Executor Agent runs dbt commands against target warehouses, managing builds, tests, and documentation generation.

## File Locations
- Main: `agents/dbt_executor_agent.py`
- API Integration: `agents/api.py`
- Config: `config/dbt_execution.py`

## Current Capabilities
- [x] Execute `dbt run` command
- [x] Execute `dbt test` command
- [x] Execute `dbt compile` command
- [x] Parse dbt output and errors
- [x] Track execution progress
- [x] Handle incremental builds
- [ ] Execute `dbt docs generate`
- [ ] Execute `dbt build` (combined run+test)

## Integration Status
- [x] API endpoint `/migrations/{id}/deploy`
- [ ] Frontend progress display - NEEDS WORK
- [x] Error reporting
- [ ] Real-time log streaming

## TODO - HIGH PRIORITY
1. [ ] Connect execution to migration pipeline
2. [ ] Add real-time execution logs to frontend
3. [ ] Implement retry logic for transient failures
4. [ ] Add execution history tracking
5. [ ] Support for model selection (`--select`)
6. [ ] Support for model exclusion (`--exclude`)

## Integration Requirements
To fully integrate this agent:
1. Add execution step after validation in pipeline
2. Create execution logs table in database
3. WebSocket for real-time log streaming
4. Execution dashboard in frontend

## Dependencies
- dbt-core
- dbt-snowflake / dbt-bigquery / etc.
- subprocess management

## Known Issues
- Large models may timeout
- Memory usage spikes with many models
- No support for concurrent execution

## Metrics (from testing)
- Average run time: varies by model count
- Success rate: 85% (needs improvement)

---
Last Updated: 2024-12-05
