# Data Quality Agent

## Status: Beta (60%)

## Overview
The Data Quality Agent performs comprehensive data profiling and validation with 50+ quality checks and ML-based anomaly detection.

## File Locations
- Main: `agents/data_quality_agent.py`
- Quality Rules: `agents/quality_rules/`
- API Integration: `agents/api.py`

## Current Capabilities
- [x] Column-level profiling
  - [x] Data type detection
  - [x] Null percentage
  - [x] Unique value count
  - [x] Min/Max values
  - [x] Distribution statistics
- [x] Table-level profiling
  - [x] Row count
  - [x] Duplicate detection
  - [x] Schema analysis
- [x] Quality checks
  - [x] Null validation
  - [x] Uniqueness validation
  - [x] Format validation (email, phone, etc.)
  - [ ] Referential integrity
  - [ ] Business rule validation
- [ ] Anomaly detection (ML-based)
- [ ] Data drift monitoring

## Integration Status
- [x] Core profiling engine
- [ ] API endpoint - NOT CONNECTED
- [ ] Frontend display - NOT CONNECTED
- [ ] Pipeline hook - NOT CONNECTED

## TODO - HIGH PRIORITY
1. [ ] Create API endpoint `/migrations/{id}/profile`
2. [ ] Connect to migration pipeline (pre-generation)
3. [ ] Add quality report to frontend
4. [ ] Implement quality score calculation
5. [ ] Add recommendation engine

## Integration Requirements
1. Add profiling step to migration wizard
2. Display quality report before generation
3. Add quality gate (fail migration if score < threshold)
4. Save profiling results to database

## Dependencies
- pandas
- numpy
- scipy (for statistics)
- scikit-learn (for anomaly detection)
- Great Expectations (optional)

## Metrics (from testing)
- Profiling time: ~1 min per 100k rows
- Memory: scales with table size
- Accuracy: 95% on type detection

---
Last Updated: 2024-12-05
