# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Anthropic API key for AI features

### Installation

```bash
# Clone or navigate to the project directory
cd mssql-to-dbt-migration

# Install dependencies
pip install -r requirements.txt --break-system-packages
```

### Option 1: Run the Demo (Recommended for First Time)

```bash
# Run the interactive demo
python demo.py
```

This will:
1. Extract metadata from a mock MSSQL database (e-commerce example)
2. Initialize a dbt project
3. Run the complete migration workflow
4. Show you the results

### Option 2: Run Step-by-Step

```bash
# Step 1: Extract metadata
python main.py extract --output metadata.json

# Step 2: Initialize dbt project
python main.py init --project-path ./my_migration

# Step 3: Run migration
python main.py migrate \
    --metadata metadata.json \
    --project-path ./my_migration
```

### Option 3: Full Workflow (One Command)

```bash
# Run everything at once
python main.py full --project-path ./my_migration
```

## 🤖 Using with Claude API

To enable AI-powered agents:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run the demo or migration
python demo.py
# OR
python main.py full --project-path ./smart_migration
```

## 📊 What You'll See

### 1. Metadata Extraction
```
📊 Extraction Summary:
   Tables: 4
   Views: 1
   Stored Procedures: 2
   Dependencies: 9
```

### 2. Agent Workflow
```
🔧 Registering specialized agents:
   ✓ Assessment Agent
   ✓ Planner Agent
   ✓ Executor Agent
   ✓ Tester Agent
   ✓ Rebuilder Agent
   ✓ Evaluator Agent
```

### 3. Migration Results
```
📈 Summary:
   Total: 5
   ✅ Completed: 4
   ❌ Failed: 1
   ⏭️  Skipped: 0
```

### 4. Generated Files
```
demo_dbt_project/
├── dbt_project.yml
├── models/
│   └── staging/
│       ├── sources.yml
│       ├── _schema.yml
│       ├── stg_customers.sql
│       ├── stg_orders.sql
│       └── ...
├── migration_state.json
└── migration_results.json
```

## 🔍 Understanding the Output

### Key Files Generated

1. **mssql_metadata.json**
   - Complete metadata extracted from source database
   - Tables, views, procedures, dependencies
   - Used as input for the migration

2. **migration_state.json**
   - Current state of the migration
   - Which models are completed/failed/pending
   - Can be used to resume failed migrations

3. **migration_results.json**
   - Detailed results of the migration
   - Assessment, planning, and execution results
   - Validation scores and error messages

4. **dbt Models** (in models/staging/)
   - Generated SQL files for each model
   - Schema definitions in _schema.yml
   - Ready to run with `dbt run`

## 🧪 Testing the Migration

After running the migration:

```bash
# Navigate to the dbt project
cd demo_dbt_project

# (Optional) Install dbt if not already installed
pip install dbt-core dbt-duckdb --break-system-packages

# Compile the models to check for SQL errors
dbt compile

# (Note: Running requires actual data sources configured)
```

## 📖 Next Steps

1. **Explore the Code**
   - `metadata_extractor.py` - See how metadata is extracted
   - `agents.py` - Understand each agent's logic
   - `agent_system.py` - See the orchestration

2. **Customize for Your Needs**
   - Modify agent behavior in `agents.py`
   - Add custom assessment rules
   - Extend with new agent types

3. **Test with Real Data**
   - Provide MSSQL connection string
   - Configure profiles.yml for your data warehouse
   - Run on a small subset first

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure you installed all dependencies
pip install -r requirements.txt --break-system-packages
```

### "Permission denied" on demo.py
```bash
# Make the script executable
chmod +x demo.py
```

### "No module named 'anthropic'"
```bash
# The tool works without the API
# But to enable it, install the client:
pip install anthropic --break-system-packages
```

### Migration fails on certain models
- Check `migration.log` for detailed errors
- Review the failed model in `migration_state.json`
- The tool will retry up to 3 times automatically

## 💡 Tips

- **Start Small**: Test with a few tables before migrating everything
- **Review First**: Check the assessment results before proceeding
- **Use Version Control**: Commit the generated dbt project to git
- **Validate Data**: Always compare outputs between source and target
- **Iterate**: You can modify and re-run specific models

## 📞 Getting Help

- Check `migration.log` for detailed execution logs
- Review `ARCHITECTURE.md` for design details
- See `SOLUTION_OVERVIEW.md` for the big picture
- Read `README.md` for comprehensive documentation

## ⚡ Quick Reference

```bash
# Extract only
python main.py extract --output metadata.json

# Initialize only
python main.py init --project-path ./project

# Migrate only
python main.py migrate --metadata metadata.json --project-path ./project

# Full workflow
python main.py full --project-path ./project

# With API key
export ANTHROPIC_API_KEY="sk-..."
python main.py full --project-path ./project

# With real MSSQL
python main.py full \
  --connection-string "DRIVER={...};SERVER=..." \
  --project-path ./project

# Help
python main.py --help
python main.py extract --help
```

## 🎯 Success Criteria

You'll know it's working when you see:

1. ✅ Metadata JSON file created
2. ✅ dbt project directory with models
3. ✅ Migration results showing completed models
4. ✅ Valid SQL in the generated .sql files
5. ✅ No critical errors in migration.log

---

**You're now ready to run automated MSSQL to dbt migrations! 🎉**
