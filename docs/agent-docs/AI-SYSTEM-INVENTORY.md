# DataMigrate AI - AI System Inventory

## EU AI Act Compliance Documentation
**Document Version:** 1.0.0
**Last Updated:** December 2024
**Provider:** OKO Investments
**Contact:** Alexander Garcia Angus (kether180)

---

## 1. System Overview

### 1.1 System Identification

| Field | Value |
|-------|-------|
| **System Name** | DataMigrate AI |
| **System Version** | 1.0.0 |
| **Provider** | OKO Investments |
| **Intended Purpose** | Enterprise database migration from MSSQL to dbt projects |
| **Deployment Model** | SaaS (Railway Cloud) |
| **Geographic Scope** | Global (EU users included) |

### 1.2 AI Components Inventory

| Component | Type | Foundation Model | Risk Classification |
|-----------|------|------------------|---------------------|
| Claude Chat Integration | GPAI System | Claude (Anthropic) | Limited Risk (Art. 50) |
| MSSQL Extractor Agent | AI Agent | Claude API | Limited Risk |
| dbt Generator Agent | AI Agent | Claude API | Limited Risk |
| dbt Executor Agent | AI Agent | N/A (Rule-based) | Minimal Risk |
| Data Quality Agent | AI Agent | Claude API | Limited Risk |
| Validation Agent | AI Agent | Claude API | Limited Risk |
| RAG Service | AI System | Voyage AI Embeddings | Limited Risk |
| Guardian Agent | AI Agent | Rule-based + Claude | Limited Risk |
| Supervisor | AI Router | Rule-based | Minimal Risk |

---

## 2. Risk Classification Assessment

### 2.1 EU AI Act Risk Determination

**Overall System Classification: LIMITED RISK**

| Risk Category | Applicable? | Justification |
|---------------|-------------|---------------|
| **Prohibited (Art. 5)** | No | No manipulation, social scoring, or biometric categorization |
| **High-Risk (Annex III)** | Conditional | May apply if deployed in critical infrastructure contexts |
| **Limited Risk (Art. 50)** | **Yes** | Chat interface requires AI transparency disclosure |
| **Minimal Risk** | Yes | Baseline for all components |

### 2.2 Potential High-Risk Scenarios

DataMigrate AI could be classified as high-risk if used in:

1. **Financial Services** - Banking database migrations
2. **Healthcare** - Patient data migrations
3. **Critical Infrastructure** - Energy, water, transport systems

**Mitigation:** Deployers in these sectors must perform additional conformity assessment.

---

## 3. Agent-by-Agent Risk Assessment

### 3.1 MSSQL Extractor Agent

| Attribute | Value |
|-----------|-------|
| **ID** | mssql_extractor |
| **Risk Level** | Limited |
| **AI Model** | Claude (Anthropic) |
| **Purpose** | Extract database schema and metadata |
| **Data Processed** | Database schemas (no personal data) |
| **Transparency Req.** | Users informed of automated extraction |

**Potential Failures:**
- Incorrect schema extraction
- Connection timeout
- Permission errors

**Mitigations:**
- Validation Agent verification
- Retry logic with exponential backoff
- User confirmation before proceeding

---

### 3.2 dbt Generator Agent

| Attribute | Value |
|-----------|-------|
| **ID** | dbt_generator |
| **Risk Level** | Limited |
| **AI Model** | Claude (Anthropic) |
| **Purpose** | Generate dbt models from schema |
| **Data Processed** | Schema metadata (no personal data) |
| **Transparency Req.** | AI-generated output labeled |

**Potential Failures:**
- Incorrect SQL syntax
- Hallucinated column names
- Suboptimal materializations

**Mitigations:**
- Actor-Critic validation loop
- Syntax compilation check
- Human review before deployment

---

### 3.3 Validation Agent

| Attribute | Value |
|-----------|-------|
| **ID** | validation_agent |
| **Risk Level** | Limited |
| **AI Model** | Claude (Anthropic) |
| **Purpose** | Validate migration accuracy |
| **Pattern** | Actor-Critic self-healing |
| **Quality Threshold** | 95% |

**Quality Rubric:**
| Metric | Weight | Target |
|--------|--------|--------|
| Schema Completeness | 25% | 100% |
| Data Type Accuracy | 20% | 99% |
| Referential Integrity | 15% | 100% |
| dbt Syntax Validity | 20% | 100% |
| Test Coverage | 10% | 80% |
| Documentation | 10% | 90% |

---

### 3.4 Guardian Agent

| Attribute | Value |
|-----------|-------|
| **ID** | guardian_agent |
| **Risk Level** | Limited |
| **Framework** | MAESTRO 7-Layer Security |
| **Purpose** | Security orchestration and monitoring |
| **Compliance** | Article 9 (Risk Management) |

**Security Layers:**
1. Foundation Models - API key management
2. Data Operations - Encryption, credential protection
3. Agent Framework - State isolation
4. Agent Core - Input/output sanitization
5. Agent Ecosystem - Inter-agent security
6. Deployment - Container hardening
7. Monitoring - Audit logging

---

### 3.5 RAG Service

| Attribute | Value |
|-----------|-------|
| **ID** | rag_service |
| **Risk Level** | Limited |
| **Embedding Model** | Voyage AI |
| **Vector Store** | pgvector (PostgreSQL) |
| **Purpose** | Contextual query assistance |

**Data Sources:**
- dbt documentation
- Migration patterns
- Schema metadata
- User queries (anonymized)

---

## 4. Data Governance (Article 10)

### 4.1 Data Categories

| Category | Description | Retention | GDPR Basis |
|----------|-------------|-----------|------------|
| **User Data** | Account info, preferences | Account lifetime + 2 years | Contract |
| **Migration Data** | Schemas, SQL, models | 7 years | Legitimate interest |
| **Interaction Logs** | Chat history, commands | 2 years | Legitimate interest |
| **Audit Logs** | Security events | 10 years | Legal obligation |

### 4.2 Training Data

| Source | Type | Used For | Consent |
|--------|------|----------|---------|
| dbt documentation | Public | RAG indexing | N/A (public) |
| Migration patterns | Internal | Few-shot examples | N/A (synthetic) |
| Schema samples | Synthetic | Prompt examples | N/A (synthetic) |

**Note:** No customer data is used for model training. Claude API is used as-is from Anthropic.

### 4.3 Data Protection Measures

- AES-256 encryption at rest
- TLS 1.3 in transit
- Credential vault for secrets
- PII anonymization in logs
- GDPR-compliant data handling

---

## 5. Transparency Implementation (Article 50)

### 5.1 User Disclosure

**Chat Interface:**
```
"AI-Powered Assistant - Responses are generated by Claude AI. Verify critical information."
```

**AI-Generated Content Labels:**
- All assistant messages labeled "AI Generated"
- dbt models include AI generation comment header
- Validation reports indicate AI-assisted checks

### 5.2 Documentation Transparency

| Document | Availability | Format |
|----------|--------------|--------|
| API Reference | Public | Markdown |
| Developer Guide | Public | Markdown |
| Architecture | Public | Markdown |
| This Inventory | Public | Markdown |
| Model Cards | Public | YAML |

---

## 6. Human Oversight (Article 14)

### 6.1 Oversight Mechanisms

| Stage | Human Control | Implementation |
|-------|---------------|----------------|
| **Migration Start** | Required | User initiates with explicit consent |
| **Schema Review** | Recommended | Preview before generation |
| **Model Review** | Recommended | Code review before deployment |
| **Deployment** | Required | User approval for warehouse deployment |
| **Validation** | Automated + Manual | Actor-Critic with manual override |

### 6.2 Stop Mechanisms

- Cancel migration at any stage
- Emergency stop for running dbt jobs
- Rate limiting to prevent runaway processes
- Timeout controls on all operations

---

## 7. Accuracy & Robustness (Article 15)

### 7.1 Testing Coverage

| Test Type | Coverage | Tool |
|-----------|----------|------|
| Unit Tests | 60 tests | pytest |
| API Tests | 20 endpoints | FastAPI TestClient |
| Agent Tests | 11 agents | pytest |
| Integration | E2E flows | Manual + automated |

### 7.2 Validation Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Schema Extraction Accuracy | 99% | 98.5% |
| dbt Compilation Success | 99% | 97.2% |
| Data Type Mapping Accuracy | 99% | 98.8% |
| Migration Success Rate | 95% | 94.3% |

### 7.3 Robustness Measures

- Input sanitization (prompt injection prevention)
- Output validation (schema conformance)
- Error handling with graceful degradation
- Retry logic with exponential backoff
- Circuit breakers for external services

---

## 8. Recordkeeping (Article 12)

### 8.1 Log Categories

| Log Type | Content | Retention | Storage |
|----------|---------|-----------|---------|
| Access Logs | Auth events | 2 years | PostgreSQL |
| Agent Logs | Decisions, outputs | 7 years | PostgreSQL |
| Audit Logs | Security events | 10 years | PostgreSQL |
| Error Logs | Exceptions, failures | 1 year | Log aggregator |

### 8.2 Audit Trail Fields

```python
{
    "timestamp": "ISO8601",
    "event_type": "agent_action|security|user_action",
    "agent_id": "mssql_extractor|dbt_generator|...",
    "user_id": "integer",
    "organization_id": "integer",
    "migration_id": "integer|null",
    "action": "string",
    "input_hash": "SHA256 (privacy-preserving)",
    "output_hash": "SHA256",
    "execution_time_ms": "integer",
    "success": "boolean",
    "error": "string|null"
}
```

---

## 9. Post-Market Monitoring

### 9.1 Monitoring Infrastructure

| System | Purpose | Metrics |
|--------|---------|---------|
| Prometheus | Metrics collection | Latency, errors, throughput |
| Grafana | Visualization | Dashboards, alerts |
| PostgreSQL | Audit storage | Compliance logs |
| Railway | Deployment | Health, uptime |

### 9.2 Incident Reporting

**Serious Incident Definition:**
- Data loss affecting user migrations
- Security breach exposing credentials
- Systematic bias in recommendations
- Prolonged service outage (>4 hours)

**Reporting Timeline:**
- Internal: Immediate
- Regulator: 72 hours (if applicable)
- Users: 24 hours (affected parties)

---

## 10. Conformity Assessment Pathway

### 10.1 Current Status

| Requirement | Status | Evidence |
|-------------|--------|----------|
| AI System Inventory | Complete | This document |
| Risk Classification | Complete | Section 2 |
| Transparency | Complete | Chat disclosures |
| Data Governance | Complete | Section 4 |
| Technical Documentation | Complete | Developer docs |
| Recordkeeping | Partial | Audit logs implemented |
| Human Oversight | Complete | Section 6 |
| Accuracy Testing | Complete | 60 tests passing |

### 10.2 Roadmap to Full Compliance

| Phase | Timeline | Actions |
|-------|----------|---------|
| Phase 1 | Complete | Documentation, transparency, basic compliance |
| Phase 2 | Q1 2025 | Model cards, enhanced logging, FMEA |
| Phase 3 | Q2 2025 | Hallucination detection, drift monitoring |
| Phase 4 | Q3 2025 | Third-party conformity assessment (if high-risk) |

---

## 11. Contact Information

**Provider:** OKO Investments
**System Administrator:** Alexander Garcia Angus
**Email:** support@datamigrate.ai
**Compliance Inquiries:** compliance@datamigrate.ai

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 2024 | A. Garcia Angus | Initial release |

---

*This AI System Inventory is maintained as part of EU AI Act compliance for DataMigrate AI.*
