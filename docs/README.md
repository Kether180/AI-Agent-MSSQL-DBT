# Documentation

Complete documentation for DataMigrate AI - MSSQL to dbt Migration Platform.

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

---

## Folder Structure

```
docs/
├── architecture/                              # Architecture markdown docs
│   ├── KARPENTER_VS_CLUSTER_AUTOSCALER.md    # Karpenter cost analysis
│   ├── KUBERNETES_TERRAFORM_ARCHITECTURE.md   # K8s + Terraform guide
│   ├── LANGGRAPH_ARCHITECTURE.md             # AI agent workflow
│   └── RUST_VS_FASTAPI_BACKEND.md            # Backend comparison
├── GUARDIAN_AGENT_DOCUMENTATION.md            # Security agent docs
├── *.pdf / *.docx                             # PDF and Word documents
└── README.md                                  # This file
```

---

## PDF & Word Documentation

### Business & Sales
| Document | Description |
|----------|-------------|
| **DATAMIGRATE_AI_SALES_DECK_DENMARK.pdf/docx** | Denmark market sales deck with pricing (50K-2M DKK) |
| **DATAMIGRATE_AI_COMPLETE_ARCHITECTURE.pdf/docx** | Full system architecture overview |

### ML Strategy & Contracts
| Document | Description |
|----------|-------------|
| **DATAMIGRATE_AI_ML_STRATEGY.pdf/docx** | Complete ML strategy with SQLCoder recommendation |
| **DATA_COLLECTION_AGREEMENT_TEMPLATE.pdf/docx** | Customer data collection contract template |

### Infrastructure & Architecture
| Document | Description |
|----------|-------------|
| **KARPENTER_VS_CLUSTER_AUTOSCALER.pdf/docx** | Karpenter cost savings analysis (40-60% savings) |
| **KUBERNETES_TERRAFORM_ARCHITECTURE.pdf/docx** | Complete K8s + Terraform infrastructure guide |
| **LANGGRAPH_ARCHITECTURE.pdf/docx** | Multi-agent AI workflow documentation |

---

## Architecture Documentation (Markdown)

Located in `architecture/`

### Infrastructure
- **[KARPENTER_VS_CLUSTER_AUTOSCALER.md](architecture/KARPENTER_VS_CLUSTER_AUTOSCALER.md)**
  - 40-60% cost savings analysis
  - 10x faster scaling comparison
  - Implementation guide with Terraform

- **[KUBERNETES_TERRAFORM_ARCHITECTURE.md](architecture/KUBERNETES_TERRAFORM_ARCHITECTURE.md)**
  - Complete EKS infrastructure
  - Cost breakdown (Dev: $250/mo, Prod: $1,300/mo)
  - Deployment workflow

### AI Agents
- **[LANGGRAPH_ARCHITECTURE.md](architecture/LANGGRAPH_ARCHITECTURE.md)**
  - 6-agent workflow (Assessment, Planner, Executor, Tester, Rebuilder, Evaluator)
  - State management with TypedDict
  - AWS Lambda + Step Functions deployment

### Backend
- **[RUST_VS_FASTAPI_BACKEND.md](architecture/RUST_VS_FASTAPI_BACKEND.md)**
  - Go vs Rust vs Python comparison
  - TCO analysis

---

## Security Documentation

- **[GUARDIAN_AGENT_DOCUMENTATION.md](GUARDIAN_AGENT_DOCUMENTATION.md)**
  - Security agent implementation
  - Input/output validation
  - SQL injection prevention

---

## Quick Links

### For Business
1. Sales Deck: `DATAMIGRATE_AI_SALES_DECK_DENMARK.pdf`
2. ML Strategy: `DATAMIGRATE_AI_ML_STRATEGY.pdf`
3. Customer Contract: `DATA_COLLECTION_AGREEMENT_TEMPLATE.pdf`

### For DevOps
1. Infrastructure: `KUBERNETES_TERRAFORM_ARCHITECTURE.pdf`
2. Cost Optimization: `KARPENTER_VS_CLUSTER_AUTOSCALER.pdf`
3. Architecture Overview: `DATAMIGRATE_AI_COMPLETE_ARCHITECTURE.pdf`

### For AI/ML Engineers
1. Agent Workflow: `LANGGRAPH_ARCHITECTURE.pdf`
2. Security: `GUARDIAN_AGENT_DOCUMENTATION.md`
3. ML Strategy: `DATAMIGRATE_AI_ML_STRATEGY.pdf`

---

## Key Highlights

### Cost Savings
- **Karpenter**: 40-60% infrastructure cost savings ($960-4,200/year)
- **Go Backend**: 5-10x faster API responses vs Python
- **Spot Instances**: 70% discount with intelligent fallback

### ML Strategy
- **Recommended Model**: SQLCoder 15B (85% SQL accuracy)
- **Data Collection**: Schema patterns only (never actual data)
- **Privacy Options**: Anonymized, Named (with discount), or Opt-out

### Architecture
- **Backend**: Go (Gin) for API + Python for AI agents
- **Frontend**: Vue.js 3 + TypeScript
- **Infrastructure**: EKS + Terraform + Karpenter
- **AI Framework**: LangGraph + LangChain

---

**Last Updated**: December 2025
**Copyright**: OKO Investments. All rights reserved.
