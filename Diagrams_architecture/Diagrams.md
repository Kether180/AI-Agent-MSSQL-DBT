# System Flow Diagram

## Complete Migration Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MSSQL DATABASE                              │
│  (Legacy System - Tables, Views, Stored Procedures)                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ pyodbc/SQLAlchemy
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    METADATA EXTRACTOR                               │
│  • Queries system tables (sys.tables, sys.views, etc.)              │
│  • Extracts column definitions, data types                          │
│  • Analyzes dependencies (sys.sql_expression_dependencies)          │
│  • Collects statistics (row counts, complexity)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Produces JSON
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    METADATA.JSON                                    │
│  {                                                                   │
│    "tables": [...],                                                 │
│    "views": [...],                                                  │
│    "procedures": [...],                                             │
│    "dependencies": [...]                                            │
│  }                                                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Fed into
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MIGRATION ORCHESTRATOR                           │
│  • Loads metadata                                                   │
│  • Manages agent coordination                                       │
│  • Tracks state and progress                                        │
│  • Handles errors and retries                                       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  ASSESSMENT   │     │   PLANNER     │     │   EXECUTOR    │
│     AGENT     │────▶│     AGENT     │────▶│     AGENT     │
│               │     │               │     │               │
│ • Analyzes    │     │ • Creates     │     │ • Generates   │
│   complexity  │     │   migration   │     │   dbt models  │
│ • Scores      │     │   plan        │     │ • Creates     │
│   priority    │     │ • Orders by   │     │   schema.yml  │
│ • Recommends  │     │   dependencies│     │ • Writes      │
│   strategy    │     │ • Maps to dbt │     │   files       │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                     │
                                   ┌─────────────────┘
                                   │
                          For each model:
                                   │
                       ┌───────────▼──────────┐
                       │                      │
                ┌──────▼─────┐       ┌───────▼──────┐
                │   TESTER   │       │  EVALUATOR   │
                │    AGENT   │       │    AGENT     │
                │            │       │              │
                │ • Compiles │       │ • Compares   │
                │   SQL      │       │   outputs    │
                │ • Runs     │       │ • Validates  │
                │   model    │       │   data       │
                │ • Tests    │       │ • Scores     │
                └─────┬──────┘       └──────┬───────┘
                      │                     │
                      │ If fails            │ If passes
                      ▼                     │
                ┌──────────────┐            │
                │  REBUILDER   │            │
                │    AGENT     │            │
                │              │            │
                │ • Analyzes   │            │
                │   errors     │            │
                │ • Proposes   │            │
                │   fixes      │            │
                │ • Regenerates│            │
                └──────┬───────┘            │
                       │                    │
                       │ Retry              │
                       └────────┬───────────┘
                                │
                                ▼
                        Model Complete
                                │
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                         DBT PROJECT                                 │
│                                                                     │
│  dbt_project/                                                       │
│  ├── dbt_project.yml                                                │
│  ├── models/                                                        │
│  │   ├── staging/                                                   │
│  │   │   ├── sources.yml                                            │
│  │   │   ├── _schema.yml                                            │
│  │   │   ├── stg_customers.sql                                      │
│  │   │   ├── stg_orders.sql                                         │
│  │   │   └── ...                                                    │
│  │   └── marts/                                                     │
│  └── ...                                                            │
│                                                                     │
│  + migration_state.json (progress tracking)                         │
│  + migration_results.json (detailed results)                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Communication Flow

```
┌──────────────┐
│ Orchestrator │ Provides context with metadata, state, API key
└──────┬───────┘
       │
       │ 1. Initialize
       ▼
┌──────────────┐
│ Agent        │ Receives: AgentContext
│              │ - metadata
│              │ - current_model
└──────┬───────┘ - migration_state
       │
       │ 2. Execute task
       ▼
┌──────────────┐
│ Claude API   │ Optional: For intelligent decisions
│  (Optional)  │
└──────┬───────┘
       │
       │ 3. Generate result
       ▼
┌──────────────┐
│ Agent        │ Returns: AgentResult
│              │ - success: bool
│              │ - data: Dict
└──────┬───────┘ - errors: List
       │         - next_agent: AgentRole
       │
       │ 4. Update state
       ▼
┌──────────────┐
│ Orchestrator │ Persists state, determines next action
└──────────────┘
```

## State Transitions

```
                    ┌─────────────┐
                    │ PENDING     │ Initial state
                    └──────┬──────┘
                           │
                           │ Orchestrator picks model
                           ▼
                    ┌─────────────┐
                    │IN_PROGRESS  │ Executor generates
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  TESTING    │ Tester validates
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │             │
              Pass  │             │ Fail
                    ▼             ▼
            ┌─────────────┐ ┌─────────────┐
            │ EVALUATING  │ │  REBUILDING │
            └──────┬──────┘ └──────┬──────┘
                   │                │
                   │                │ Retry
                   │                └─────────┐
                   │                          │
            Pass   │                    Fail  │ (max attempts)
                   ▼                          ▼
            ┌─────────────┐          ┌─────────────┐
            │ COMPLETED   │          │   FAILED    │
            └─────────────┘          └─────────────┘
```

## Data Flow Through System

```
MSSQL Metadata → Assessment → Strategy
                               ↓
                           Planning
                               ↓
                        Model Queue
                               ↓
                     ┌─────────┴─────────┐
                     │                   │
              For each model:            │
                     │                   │
                     ▼                   │
            Generate dbt Model           │
                     ↓                   │
              Test Compilation           │
                     ↓                   │
                Run Model                │
                     ↓                   │
              Validate Output            │
                     ↓                   │
              Update State               │
                     │                   │
                     └───────────────────┘
                             ↓
                      All Models Done
                             ↓
                    Generate Report
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  CLI       │  │   Demo     │  │  (Future   │           │
│  │  (main.py) │  │  Script    │  │   Web UI)  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  APPLICATION LAYER                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Orchestrator (agent_system.py)                      │  │
│  │  - Workflow coordination                             │  │
│  │  - State management                                  │  │
│  │  - Agent lifecycle                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agents (agents.py)                                  │  │
│  │  - Assessment - Planner - Executor                   │  │
│  │  - Tester - Rebuilder - Evaluator                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    SERVICE LAYER                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Metadata    │  │  Claude API  │  │  File        │     │
│  │  Extractor   │  │  (Anthropic) │  │  Operations  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    DATA LAYER                               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  MSSQL       │  │  JSON Files  │  │  dbt Project │     │
│  │  Database    │  │  (Metadata)  │  │  (Output)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Execution Timeline

```
Time    Phase           Agent           Action
──────  ──────────────  ──────────────  ─────────────────────────
T+0s    Extraction      (System)        Connect to MSSQL
T+5s    Extraction      (System)        Query metadata
T+10s   Extraction      (System)        Build dependency graph

T+15s   Assessment      Assessment      Analyze complexity
T+30s   Assessment      Assessment      Generate strategy

T+35s   Planning        Planner         Map MSSQL to dbt
T+45s   Planning        Planner         Order by dependencies

T+50s   Execution       Executor        Generate stg_customers.sql
T+55s   Testing         Tester          Compile & test
T+58s   Evaluation      Evaluator       Validate output
T+60s   ✓ Complete      (System)        stg_customers done

T+65s   Execution       Executor        Generate stg_orders.sql
T+70s   Testing         Tester          Compile & test
T+73s   Evaluation      Evaluator       Validate output
T+75s   ✓ Complete      (System)        stg_orders done

...     (Continue for all models)

T+5m    Complete        (System)        Generate final report
```

## Error Recovery Flow

```
┌─────────────┐
│  Tester     │ Model compilation/execution fails
│  detects    │
│  error      │
└──────┬──────┘
       │
       │ Error details
       ▼
┌─────────────┐
│ Rebuilder   │
│ Agent       │
└──────┬──────┘
       │
       │ Analyze error
       ▼
┌─────────────┐
│ Claude API  │ (Optional) Get fix suggestions
│ or Rules    │
└──────┬──────┘
       │
       │ Proposed fix
       ▼
┌─────────────┐
│ Rebuilder   │ Regenerate model
│ regenerates │
└──────┬──────┘
       │
       │ Attempt 2
       ▼
┌─────────────┐
│  Tester     │ Test again
│  retests    │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
Pass│       │Fail (retry up to 3x)
   │       │
   ▼       ▼
Success   Mark Failed
```

This visual representation shows how all components work together to 
transform a legacy MSSQL database into a modern dbt project!