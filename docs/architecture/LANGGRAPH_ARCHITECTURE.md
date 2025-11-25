### LangGraph Architecture

This document explains the LangGraph-based architecture for the MSSQL to dbt migration tool.

## Overview

The migration workflow has been refactored to use **LangGraph**, a framework for building stateful, multi-agent workflows. This provides:

- **Structured State Management**: TypedDict-based state with Pydantic validation
- **Visual Workflow**: Clear graph structure with conditional routing
- **Checkpointing**: State persistence for resumable migrations
- **AWS Integration**: Lambda functions and Step Functions deployment
- **Security Guardrails**: LLM input/output validation and SQL sanitization

## Architecture Components

### 1. State Management (`agents/state.py`)

Defines the typed state structure:

```python
class MigrationState(TypedDict):
    phase: Literal["assessment", "planning", "execution", "evaluation", "complete"]
    models: List[Dict[str, Any]]
    current_model_index: int
    completed_count: int
    failed_count: int
    assessment_complete: bool
    plan_complete: bool
    assessment: Optional[Dict[str, Any]]
    planning: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    project_path: Optional[str]
    errors: List[str]
    max_retries: int
    current_retry: int
```

**Key Functions:**
- `create_initial_state()` - Initialize migration state
- `get_current_model()` - Get the current model being processed
- `update_model_state()` - Update specific model state
- `is_migration_complete()` - Check if all models processed

### 2. LangGraph Workflow (`agents/graph.py`)

Defines the StateGraph that orchestrates the 6-agent workflow.

**Graph Structure:**

```
[START]
   │
   ▼
┌──────────────┐
│  Assessment  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Planner    │
└──────┬───────┘
       │
       ▼
   ╔═══════════╗
   ║ Models    ║
   ║ Exist?    ║
   ╚═══╤═══════╝
       │ Yes
       ▼
┌──────────────┐
│  Execute     │◄─────┐
│  Model       │      │
└──────┬───────┘      │
       │              │
       ▼              │
┌──────────────┐      │
│   Tester     │      │
└──────┬───────┘      │
       │              │
       ▼              │
   ╔═══════════╗      │
   ║ Passed?   ║      │
   ╚═══╤═══════╝      │
       │ No           │
       ▼              │
   ╔═══════════╗      │
   ║ Retries   ║      │
   ║ Left?     ║      │
   ╚═══╤═══════╝      │
       │ Yes          │
       ▼              │
┌──────────────┐      │
│  Rebuilder   │──────┘
└──────────────┘

       │ Yes (from Tester)
       ▼
┌──────────────┐
│ Advance to   │
│ Next Model   │
└──────┬───────┘
       │
       ▼
   ╔═══════════╗
   ║ More      ║
   ║ Models?   ║
   ╚═══╤═══════╝
       │ Yes: Loop back to Execute Model
       │ No
       ▼
┌──────────────┐
│  Evaluator   │
└──────┬───────┘
       │
       ▼
    [END]
```

**Conditional Edges:**

1. **should_continue_migration**: After planner, check if models exist
2. **should_rebuild_or_continue**: After tester, decide rebuild or advance
3. **after_advance_check**: After advance, check if more models exist

### 3. Agent Nodes (`agents/nodes.py`)

Each agent is wrapped in a LangGraph-compatible node function:

```python
def assessment_node(state: MigrationState) -> MigrationState:
    """Evaluates MSSQL metadata"""
    # Uses existing AssessmentAgent logic
    # Returns updated state
```

**Node Functions:**
- `assessment_node()` - Analyze metadata, create assessment
- `planner_node()` - Create migration plan, initialize model list
- `executor_node()` - Generate dbt model for current model
- `tester_node()` - Validate generated model
- `rebuilder_node()` - Fix errors, regenerate model
- `evaluator_node()` - Final validation of all models

### 4. Security Guardrails (`agents/guardrails.py`)

Provides security checks for LLM interactions:

**Input Validation:**
- Prompt injection detection
- Maximum length checks
- Dangerous pattern detection

**Output Validation:**
- JSON extraction from markdown
- SQL sanitization
- Dangerous SQL pattern blocking

**Rate Limiting:**
- Per-agent rate limits
- Time-windowed request tracking

**SQL Patterns Blocked:**
```python
DANGEROUS_SQL_PATTERNS = [
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)",
    r"\bDELETE\s+FROM\s+\w+\s+(WHERE\s+1\s*=\s*1)?$",
    r"\bTRUNCATE\s+TABLE",
    r"\bEXEC(\s+|\().*xp_cmdshell",
]
```

### 5. AWS Lambda Handlers (`agents/lambda_handlers.py`)

Wraps node functions for AWS Lambda execution:

```python
@handler_wrapper_v2
def assessment_lambda(event, context):
    # Loads state from S3
    # Executes assessment_node
    # Saves state back to S3
```

**Handler Features:**
- S3 state loading/saving
- Secrets Manager integration for API keys
- Error handling and logging
- Structured responses

### 6. AWS CDK Infrastructure (`aws/cdk_stack.py`)

Defines cloud infrastructure:

**Resources Created:**
- **S3 Bucket**: State storage with versioning
- **6 Lambda Functions**: One per agent
- **IAM Roles**: Permissions for S3 and Secrets Manager
- **Secrets Manager**: Stores Anthropic API key
- **Step Functions State Machine**: Orchestrates workflow
- **CloudWatch Logs**: Centralized logging

## Usage

### Local Execution with LangGraph

```python
from agents import create_initial_state, create_migration_graph
from agents.nodes import (
    assessment_node, planner_node, executor_node,
    tester_node, rebuilder_node, evaluator_node
)

# Create initial state
state = create_initial_state(
    metadata=metadata,
    project_path="./my_dbt_project",
    max_retries=3
)

# Create graph
graph = create_migration_graph(
    assessment_node=assessment_node,
    planner_node=planner_node,
    executor_node=executor_node,
    tester_node=tester_node,
    rebuilder_node=rebuilder_node,
    evaluator_node=evaluator_node,
    use_checkpointer=True
)

# Run migration
config = {"configurable": {"thread_id": "migration-1"}}
for output in graph.stream(state, config=config):
    node_name = list(output.keys())[0]
    print(f"Completed: {node_name}")
```

### Test with Mock Data

```bash
python test_langgraph_migration.py
```

### Deploy to AWS

```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy infrastructure
cd aws
cdk deploy --app "python app.py"

# Upload state to S3
aws s3 cp migration_state.json s3://YOUR-BUCKET/migrations/migration-1/state.json

# Start Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:MigrationWorkflow \
  --input '{"state_bucket": "YOUR-BUCKET", "state_key": "migrations/migration-1/state.json"}'
```

## State Flow Example

### 1. Initial State
```json
{
  "phase": "assessment",
  "models": [],
  "current_model_index": 0,
  "completed_count": 0,
  "failed_count": 0,
  "assessment_complete": false,
  "plan_complete": false,
  "metadata": {...},
  "project_path": "./my_project"
}
```

### 2. After Assessment
```json
{
  "phase": "planning",
  "assessment_complete": true,
  "assessment": {
    "total_objects": 7,
    "tables": [...],
    "strategy": {...}
  }
}
```

### 3. After Planning
```json
{
  "phase": "execution",
  "plan_complete": true,
  "models": [
    {"name": "stg_customers", "status": "pending", "attempts": 0},
    {"name": "stg_orders", "status": "pending", "attempts": 0}
  ],
  "current_model_index": 0,
  "planning": {
    "models": [...],
    "execution_order": [...]
  }
}
```

### 4. During Execution
```json
{
  "phase": "execution",
  "current_model_index": 0,
  "models": [
    {"name": "stg_customers", "status": "in_progress", "attempts": 1},
    {"name": "stg_orders", "status": "pending", "attempts": 0}
  ]
}
```

### 5. After Completion
```json
{
  "phase": "complete",
  "completed_count": 7,
  "failed_count": 0,
  "models": [
    {"name": "stg_customers", "status": "completed", "validation_score": 0.95},
    {"name": "stg_orders", "status": "completed", "validation_score": 0.95}
  ]
}
```

## Benefits of LangGraph Architecture

### 1. **Type Safety**
- Pydantic models for data validation
- TypedDict for state structure
- Catches errors early

### 2. **Observability**
- Clear state transitions
- Structured logging at each node
- Easy to debug workflow

### 3. **Resumability**
- Built-in checkpointing
- Can resume from any point
- State persisted to S3

### 4. **Scalability**
- Nodes can run on different machines
- AWS Lambda for serverless execution
- Step Functions for orchestration

### 5. **Testability**
- Each node independently testable
- Mock state for unit tests
- Integration tests with full graph

## Comparison: Original vs LangGraph

| Aspect | Original | LangGraph |
|--------|----------|-----------|
| **State Management** | JSON files | TypedDict + Pydantic |
| **Workflow** | Custom orchestrator | StateGraph |
| **Persistence** | Manual save/load | Built-in checkpointing |
| **Visualization** | None | Mermaid diagrams |
| **Cloud Deployment** | Manual | CDK infrastructure |
| **Type Safety** | Minimal | Full type hints |
| **Error Handling** | Custom | Framework-integrated |
| **Testing** | End-to-end only | Node + integration |

## Next Steps

### Development
- [ ] Add unit tests for each node
- [ ] Create integration tests with mock LLM
- [ ] Add graph visualization to README
- [ ] Document error scenarios

### Production Readiness
- [ ] Add DLQ for failed Lambda invocations
- [ ] Implement circuit breakers
- [ ] Add metrics and alarms
- [ ] Create runbook for operations

### Features
- [ ] Add parallel execution for independent models
- [ ] Implement streaming progress updates
- [ ] Add rollback capability
- [ ] Support multiple migration strategies

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Anthropic Integration](https://python.langchain.com/docs/integrations/chat/anthropic)
- [AWS CDK Python](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/)
