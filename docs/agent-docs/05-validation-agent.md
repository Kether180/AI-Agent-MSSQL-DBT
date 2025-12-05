# Validation Agent

## Status: Beta (50%)

## Overview
The Validation Agent ensures migration accuracy by comparing source and target data through row counts, checksums, and sample comparisons.

## File Locations
- Main: `agents/validation_agent.py`
- API Integration: `agents/api.py`
- Models: `models/validation.py`

## Current Capabilities
- [x] Row count comparison
- [x] Column-level checksum validation
- [x] Sample data comparison
- [x] Schema compatibility check
- [x] Data type validation
- [ ] Full table checksum
- [ ] Incremental validation
- [ ] Reconciliation reports

## Validation Checks
1. **Schema Validation**: Compare source and target schemas
2. **Row Count**: Verify record counts match
3. **Column Checksum**: Hash-based column comparison
4. **Sample Comparison**: Random sample data matching
5. **Type Compatibility**: Data type mapping verification

## Integration Status
- [x] API endpoint `/migrations/{id}/validate`
- [x] Frontend validation panel
- [x] Result storage
- [ ] Automated post-migration validation
- [ ] Scheduled validation jobs

## TODO - MEDIUM PRIORITY
1. [ ] Add automated validation trigger after deployment
2. [ ] Implement incremental validation
3. [ ] Add customizable validation rules
4. [ ] Create validation dashboard
5. [ ] Export validation reports (PDF/Excel)

## Integration Requirements
1. Hook into post-deployment pipeline
2. Add validation scheduling
3. Create validation history view
4. Alert system for validation failures

## Dependencies
- pandas
- hashlib
- pyodbc (source)
- target warehouse connectors

## Metrics
- Validation time: ~2 min per 1M rows
- Accuracy: 99% (false positives rare)

---
Last Updated: 2024-12-05
