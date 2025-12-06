# DataMigrate AI - API Reference

## Complete REST API Documentation
**Version:** 1.0.0
**Base URL:** `https://datamigrate-ai.up.railway.app` (Production)
**Local URL:** `http://localhost:8001` (Development)
**Author:** Alexander Garcia Angus (kether180)
**Property of:** OKO Investments

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status Endpoints](#health--status-endpoints)
3. [Agent Endpoints](#agent-endpoints)
4. [Migration Endpoints](#migration-endpoints)
5. [Validation Endpoints](#validation-endpoints)
6. [Security Endpoints](#security-endpoints)
7. [Chat Endpoints](#chat-endpoints)
8. [Deployment Endpoints](#deployment-endpoints)
9. [Data Quality Endpoints](#data-quality-endpoints)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)

---

## Authentication

All protected endpoints require JWT authentication via the Go backend. The Python AI service receives pre-authenticated requests.

### Headers
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Health & Status Endpoints

### GET /health

Check if the AI service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "datamigrate-ai-agents",
  "timestamp": "2024-12-06T10:30:00Z",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is unhealthy

---

### GET /agents/health

Get health status of all AI agents.

**Response:**
```json
{
  "overall_status": "healthy",
  "agents": {
    "mssql_extractor": {
      "status": "healthy",
      "last_used": "2024-12-06T10:25:00Z",
      "response_time_ms": 145
    },
    "dbt_generator": {
      "status": "healthy",
      "last_used": "2024-12-06T10:28:00Z",
      "response_time_ms": 230
    }
  },
  "timestamp": "2024-12-06T10:30:00Z"
}
```

---

### GET /agents/status

Get completion status and capabilities of all agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "MSSQL Extractor",
      "id": "mssql_extractor",
      "status": "production",
      "completion": 95,
      "capabilities": [
        "Schema extraction",
        "Metadata analysis",
        "Relationship detection"
      ]
    },
    {
      "name": "dbt Generator",
      "id": "dbt_generator",
      "status": "production",
      "completion": 95,
      "capabilities": [
        "Model generation",
        "Source creation",
        "Test scaffolding"
      ]
    }
  ]
}
```

---

## Agent Endpoints

### GET /agents/{agent_id}

Get detailed information about a specific agent.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_id | string | Yes | Agent identifier (e.g., `mssql_extractor`) |

**Response:**
```json
{
  "id": "mssql_extractor",
  "name": "MSSQL Extractor",
  "description": "Extracts metadata from MSSQL databases",
  "status": "production",
  "completion": 95,
  "capabilities": [
    "Schema extraction",
    "Foreign key detection",
    "Index analysis"
  ],
  "metrics": {
    "total_invocations": 1250,
    "success_rate": 0.98,
    "avg_response_time_ms": 145
  }
}
```

**Status Codes:**
- `200 OK` - Agent found
- `404 Not Found` - Agent not found

---

### GET /agents/{agent_id}/test

Test an agent's functionality.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_id | string | Yes | Agent identifier |

**Response:**
```json
{
  "agent_id": "mssql_extractor",
  "test_status": "passed",
  "tests_run": 5,
  "tests_passed": 5,
  "execution_time_ms": 450,
  "details": [
    {"name": "initialization", "status": "passed"},
    {"name": "connection_mock", "status": "passed"},
    {"name": "schema_extraction", "status": "passed"}
  ]
}
```

---

## Migration Endpoints

### POST /migrations/start

Start a new database migration.

**Request Body:**
```json
{
  "connection": {
    "host": "sql-server.example.com",
    "port": 1433,
    "database": "SourceDB",
    "username": "migration_user",
    "password": "secure_password",
    "encrypt": true
  },
  "target_warehouse": "snowflake",
  "project_name": "my_dbt_project",
  "options": {
    "include_views": true,
    "include_stored_procedures": false,
    "generate_tests": true,
    "generate_docs": true
  }
}
```

**Response:**
```json
{
  "migration_id": 42,
  "status": "started",
  "created_at": "2024-12-06T10:30:00Z",
  "estimated_duration_minutes": 15
}
```

**Status Codes:**
- `200 OK` - Migration started
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Failed to start

---

### GET /migrations/{migration_id}/status

Get the current status of a migration.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| migration_id | integer | Yes | Migration ID |

**Response:**
```json
{
  "migration_id": 42,
  "status": "in_progress",
  "progress": 65,
  "current_step": "Generating dbt models",
  "steps_completed": [
    {"step": "Schema extraction", "status": "completed", "duration_ms": 3200},
    {"step": "Relationship analysis", "status": "completed", "duration_ms": 1500}
  ],
  "steps_pending": [
    "Model generation",
    "Test scaffolding",
    "Validation"
  ],
  "started_at": "2024-12-06T10:30:00Z",
  "estimated_completion": "2024-12-06T10:45:00Z"
}
```

**Status Codes:**
- `200 OK` - Status retrieved
- `404 Not Found` - Migration not found

---

### POST /migrations/{migration_id}/stop

Stop a running migration.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| migration_id | integer | Yes | Migration ID |

**Response:**
```json
{
  "migration_id": 42,
  "status": "stopped",
  "stopped_at": "2024-12-06T10:35:00Z",
  "progress_at_stop": 65
}
```

---

### GET /migrations/{migration_id}/files

Get list of generated files for a migration.

**Response:**
```json
{
  "migration_id": 42,
  "files": [
    {
      "path": "models/staging/stg_customers.sql",
      "type": "model",
      "size_bytes": 1250
    },
    {
      "path": "models/staging/stg_orders.sql",
      "type": "model",
      "size_bytes": 890
    },
    {
      "path": "models/schema.yml",
      "type": "schema",
      "size_bytes": 3400
    }
  ],
  "total_files": 15,
  "total_size_bytes": 45000
}
```

---

### GET /migrations/{migration_id}/files/{file_path}

Get content of a specific generated file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| migration_id | integer | Yes | Migration ID |
| file_path | string | Yes | Path to file (e.g., `models/staging/stg_customers.sql`) |

**Response:**
```json
{
  "path": "models/staging/stg_customers.sql",
  "content": "{{ config(materialized='view') }}\n\nSELECT\n    customer_id,\n    customer_name\nFROM {{ source('mssql', 'customers') }}",
  "language": "sql",
  "size_bytes": 1250
}
```

---

### GET /migrations/{migration_id}/download

Download the complete dbt project as a ZIP file.

**Response:**
- `Content-Type: application/zip`
- Binary ZIP file

---

## Validation Endpoints

### POST /migrations/{migration_id}/validate

Validate a migration using standard validation rules.

**Request Body:**
```json
{
  "check_schema": true,
  "check_syntax": true,
  "check_tests": true,
  "check_documentation": false
}
```

**Response:**
```json
{
  "migration_id": 42,
  "passed": true,
  "score": 0.92,
  "checks": [
    {
      "name": "schema_completeness",
      "passed": true,
      "score": 1.0,
      "details": "All 25 tables migrated"
    },
    {
      "name": "syntax_validity",
      "passed": true,
      "score": 0.95,
      "details": "45/47 models compile successfully"
    }
  ],
  "recommendations": [
    "Add tests for primary keys in 2 models"
  ]
}
```

---

### POST /migrations/{migration_id}/validate-actor-critic

Validate using the Actor-Critic self-healing pattern.

**Request Body:**
```json
{
  "quality_threshold": 0.95,
  "max_iterations": 3,
  "auto_fix": true
}
```

**Response:**
```json
{
  "migration_id": 42,
  "status": "approved",
  "final_score": 0.97,
  "passed": true,
  "needs_manual_review": false,
  "iterations_used": 2,
  "issues_found": [
    "Missing unique test on customer_id",
    "Incorrect data type mapping for datetime2"
  ],
  "issues_fixed": [
    "Added unique test on customer_id",
    "Fixed datetime2 to TIMESTAMP_NTZ mapping"
  ],
  "rubric_scores": {
    "schema_completeness": 1.0,
    "data_type_accuracy": 0.99,
    "referential_integrity": 1.0,
    "dbt_syntax_validity": 1.0,
    "test_coverage": 0.88,
    "documentation_coverage": 0.92
  }
}
```

**Quality Rubric:**
| Metric | Weight | Threshold |
|--------|--------|-----------|
| Schema Completeness | 25% | 100% |
| Data Type Accuracy | 20% | 99% |
| Referential Integrity | 15% | 100% |
| dbt Syntax Validity | 20% | 100% |
| Test Coverage | 10% | 80% |
| Documentation Coverage | 10% | 90% |

---

### POST /migrations/{migration_id}/enhance-schema

Enhance schema documentation using AI.

**Response:**
```json
{
  "migration_id": 42,
  "enhanced_tables": 25,
  "enhancements": [
    {
      "table": "customers",
      "added_descriptions": 12,
      "inferred_relationships": 3
    }
  ]
}
```

---

## Security Endpoints

### GET /security/maestro-assessment

Get MAESTRO 7-layer security assessment.

**Response:**
```json
{
  "assessment_id": "maestro-2024-12-06-001",
  "overall_score": 0.87,
  "overall_status": "secure",
  "layers": {
    "foundation_models": {
      "score": 0.95,
      "status": "secure",
      "checks": [
        {"name": "api_key_rotation", "status": "passed"},
        {"name": "model_version_pinning", "status": "passed"}
      ]
    },
    "data_operations": {
      "score": 0.90,
      "status": "secure",
      "checks": [
        {"name": "encryption_at_rest", "status": "passed"},
        {"name": "connection_encryption", "status": "passed"}
      ]
    },
    "agent_framework": {
      "score": 0.85,
      "status": "warning",
      "checks": [
        {"name": "tool_permissions", "status": "passed"},
        {"name": "execution_sandboxing", "status": "warning"}
      ]
    },
    "agent_core": {
      "score": 0.88,
      "status": "secure",
      "checks": [
        {"name": "input_sanitization", "status": "passed"},
        {"name": "output_filtering", "status": "passed"}
      ]
    },
    "agent_ecosystem": {
      "score": 0.82,
      "status": "warning",
      "checks": [
        {"name": "inter_agent_auth", "status": "warning"},
        {"name": "message_encryption", "status": "passed"}
      ]
    },
    "deployment": {
      "score": 0.90,
      "status": "secure",
      "checks": [
        {"name": "container_security", "status": "passed"},
        {"name": "secrets_management", "status": "passed"}
      ]
    },
    "monitoring": {
      "score": 0.80,
      "status": "warning",
      "checks": [
        {"name": "audit_logging", "status": "passed"},
        {"name": "anomaly_detection", "status": "warning"}
      ]
    }
  },
  "recommendations": [
    "Enable full execution sandboxing for dbt commands",
    "Implement inter-agent authentication tokens",
    "Add ML-based anomaly detection"
  ],
  "assessed_at": "2024-12-06T10:30:00Z"
}
```

**MAESTRO Layers:**
| Layer | Description |
|-------|-------------|
| Foundation Models | Claude API security, model version control |
| Data Operations | Database encryption, credential management |
| Agent Framework | LangGraph safeguards, tool permissions |
| Agent Core | Input/output validation, behavior constraints |
| Agent Ecosystem | Multi-agent communication security |
| Deployment | Container security, secrets management |
| Monitoring | Audit logging, anomaly detection |

---

### GET /security/stats

Get security statistics.

**Response:**
```json
{
  "blocked_requests": 15,
  "sanitized_inputs": 234,
  "rate_limit_hits": 5,
  "anomalies_detected": 2,
  "last_threat_detected": "2024-12-05T14:22:00Z",
  "period": "last_24_hours"
}
```

---

### GET /security/audit-logs

Get security audit logs.

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| limit | integer | 100 | Max records to return |
| offset | integer | 0 | Pagination offset |
| severity | string | all | Filter by severity (info, warning, critical) |

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-12-06T10:25:00Z",
      "severity": "warning",
      "event": "rate_limit_exceeded",
      "user_id": "user_123",
      "details": "100 requests/minute limit exceeded"
    }
  ],
  "total": 250,
  "limit": 100,
  "offset": 0
}
```

---

## Chat Endpoints

### POST /chat

Send a message to the AI assistant.

**Request Body:**
```json
{
  "message": "How do I create a staging model for my customers table?",
  "language": "en",
  "context": {
    "migration_id": 42,
    "current_table": "customers"
  }
}
```

**Supported Languages:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `da` - Danish
- `nl` - Dutch
- `pt` - Portuguese

**Response:**
```json
{
  "response": "To create a staging model for your customers table, I recommend...",
  "suggestions": [
    "View generated model",
    "Add tests",
    "Preview SQL"
  ],
  "related_docs": [
    {
      "title": "dbt Staging Best Practices",
      "url": "/docs/staging-models"
    }
  ]
}
```

---

## Deployment Endpoints

### POST /migrations/{migration_id}/deploy

Deploy a validated migration to a data warehouse.

**Request Body:**
```json
{
  "connection": {
    "warehouse_type": "snowflake",
    "account": "xy12345.us-east-1",
    "warehouse": "COMPUTE_WH",
    "database": "ANALYTICS",
    "schema": "DBT_PROD",
    "role": "TRANSFORMER",
    "user": "dbt_user",
    "password": "secure_password"
  },
  "options": {
    "run_tests": true,
    "full_refresh": false,
    "target": "prod"
  }
}
```

**Response:**
```json
{
  "deployment_id": 101,
  "migration_id": 42,
  "status": "deploying",
  "started_at": "2024-12-06T11:00:00Z",
  "steps": [
    {"step": "deps_install", "status": "completed"},
    {"step": "dbt_run", "status": "in_progress"},
    {"step": "dbt_test", "status": "pending"}
  ]
}
```

---

### GET /migrations/{migration_id}/deployments/{deployment_id}

Get deployment status.

**Response:**
```json
{
  "deployment_id": 101,
  "migration_id": 42,
  "status": "completed",
  "started_at": "2024-12-06T11:00:00Z",
  "completed_at": "2024-12-06T11:05:00Z",
  "results": {
    "models_run": 45,
    "models_success": 45,
    "tests_run": 120,
    "tests_passed": 118,
    "tests_failed": 2
  }
}
```

---

### GET /migrations/{migration_id}/deployments

List all deployments for a migration.

**Response:**
```json
{
  "migration_id": 42,
  "deployments": [
    {
      "deployment_id": 101,
      "status": "completed",
      "target": "prod",
      "deployed_at": "2024-12-06T11:05:00Z"
    },
    {
      "deployment_id": 100,
      "status": "completed",
      "target": "dev",
      "deployed_at": "2024-12-05T15:30:00Z"
    }
  ]
}
```

---

## Data Quality Endpoints

### POST /data-quality/scan

Scan a database for data quality issues.

**Request Body:**
```json
{
  "host": "sql-server.example.com",
  "port": 1433,
  "database": "SourceDB",
  "username": "scan_user",
  "password": "secure_password",
  "options": {
    "check_nulls": true,
    "check_duplicates": true,
    "check_patterns": true,
    "sample_size": 10000
  }
}
```

**Response:**
```json
{
  "scan_id": "scan-2024-12-06-001",
  "status": "completed",
  "tables_scanned": 25,
  "issues_found": 12,
  "issues": [
    {
      "table": "customers",
      "column": "email",
      "issue_type": "null_values",
      "severity": "warning",
      "count": 150,
      "percentage": 1.5
    },
    {
      "table": "orders",
      "column": "order_id",
      "issue_type": "duplicates",
      "severity": "critical",
      "count": 3
    }
  ],
  "recommendations": [
    "Add NOT NULL constraint to customers.email after data cleanup",
    "Investigate duplicate order_ids immediately"
  ]
}
```

---

### POST /connections/{connection_id}/scan-quality

Scan an existing saved connection.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| connection_id | integer | Yes | Saved connection ID |

**Response:** Same as `/data-quality/scan`

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "MIGRATION_NOT_FOUND",
    "message": "Migration with ID 42 not found",
    "details": {
      "migration_id": 42
    }
  },
  "timestamp": "2024-12-06T10:30:00Z",
  "request_id": "req-abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limiting

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Health checks | 1000/min | 1 minute |
| Read operations | 100/min | 1 minute |
| Write operations | 50/min | 1 minute |
| Migration start | 10/min | 1 minute |
| Chat | 30/min | 1 minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701864660
```

---

## SDK Examples

### Python
```python
import requests

BASE_URL = "https://datamigrate-ai.up.railway.app"

# Start a migration
response = requests.post(
    f"{BASE_URL}/migrations/start",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "connection": {
            "host": "sql-server.example.com",
            "database": "SourceDB",
            "username": "user",
            "password": "pass"
        },
        "target_warehouse": "snowflake",
        "project_name": "my_project"
    }
)
migration = response.json()
print(f"Migration started: {migration['migration_id']}")
```

### JavaScript
```javascript
const BASE_URL = 'https://datamigrate-ai.up.railway.app';

// Start a migration
const response = await fetch(`${BASE_URL}/migrations/start`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    connection: {
      host: 'sql-server.example.com',
      database: 'SourceDB',
      username: 'user',
      password: 'pass'
    },
    target_warehouse: 'snowflake',
    project_name: 'my_project'
  })
});
const migration = await response.json();
console.log(`Migration started: ${migration.migration_id}`);
```

### cURL
```bash
curl -X POST https://datamigrate-ai.up.railway.app/migrations/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "host": "sql-server.example.com",
      "database": "SourceDB",
      "username": "user",
      "password": "pass"
    },
    "target_warehouse": "snowflake",
    "project_name": "my_project"
  }'
```

---

*API Reference generated for DataMigrate AI v1.0.0*
