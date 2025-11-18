# How to Run the MSSQL to dbt Migration Tool

This guide will walk you through running the AI-powered migration tool to convert your MSSQL database to dbt models.

---

## 📋 Prerequisites

### Required Software
- **Python 3.12+** (tested on Python 3.12)
- **pip** (Python package manager)

### Optional
- **MSSQL Database** (for real migrations; not needed for demo/testing)
- **Anthropic API Key** (for AI-powered features; works without it in fallback mode)

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
# Navigate to project directory
cd AI-Agent-MSSQL-DBT

# Install required packages
pip install -r requirements.txt
```

This installs:
- `anthropic` - Claude API for AI features
- `pyodbc` - MSSQL database connectivity
- `networkx` - Dependency graph analysis
- `dbt-core` & `dbt-duckdb` - dbt transformation framework
- Other utilities (pyyaml, jinja2, etc.)

---

### 2. Choose Your Run Mode

#### **Option A: Quick Demo (No Database Required)** ⚡

Run with mock data to see how the tool works:

```bash
python test_migration.py
```

This will:
- ✅ Extract mock metadata (e-commerce database example)
- ✅ Initialize a dbt project at `./test_dbt_project/`
- ✅ Generate 7 dbt models (4 tables, 1 view, 2 procedures)
- ✅ Display results summary

**Expected Output:**
```
============================================================
MSSQL to dbt Migration Test
============================================================

Step 1: Extracting metadata...
INFO - Extracted 5 tables/views
INFO - Extracted 2 stored procedures

Step 2: Initializing dbt project...
INFO - dbt project initialized successfully

Step 3: Running migration...
INFO - Starting migration workflow
...
============================================================
MIGRATION RESULTS
============================================================
Total Models: 7
Completed: 7
Failed: 0
Pending: 0
============================================================
```

---

#### **Option B: Step-by-Step Migration** 🔧

For more control, run each phase separately:

```bash
# Step 1: Extract metadata from MSSQL (or use mock mode)
python main.py extract --output metadata.json

# Step 2: Initialize dbt project structure
python main.py init --project-path ./my_dbt_project

# Step 3: Run migration
python main.py migrate --metadata metadata.json --project-path ./my_dbt_project
```

---

#### **Option C: Full Migration (All-in-One)** 🚀

Run everything in one command:

```bash
python main.py full --project-path ./my_migration
```

This executes all three steps automatically.

---

## 🔌 Connecting to Real MSSQL Database

### 1. Prepare Your Connection String

```bash
# Format:
DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=username;PWD=password

# Example:
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=AdventureWorks;UID=sa;PWD=MyPassword123
```

### 2. Run with Connection String

```bash
python main.py full \
  --connection-string "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;UID=user;PWD=pass" \
  --project-path ./my_real_migration
```

---

## 🤖 Enable AI Features (Claude API)

For intelligent migration strategies and error fixing:

### 1. Get Anthropic API Key

Sign up at [https://console.anthropic.com](https://console.anthropic.com)

### 2. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

**Windows (CMD):**
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Run Migration

```bash
# The tool automatically detects the API key
python main.py full --project-path ./smart_migration
```

**Or pass it directly:**
```bash
python main.py migrate \
  --metadata metadata.json \
  --project-path ./my_project \
  --api-key "your-api-key-here"
```

---

## 📂 Understanding the Output

After running the migration, you'll have:

```
my_dbt_project/
├── dbt_project.yml              # dbt configuration
├── models/
│   ├── staging/
│   │   ├── sources.yml          # Source table definitions
│   │   ├── _schema.yml          # Model documentation
│   │   ├── stg_customers.sql    # Generated models
│   │   ├── stg_orders.sql
│   │   ├── stg_products.sql
│   │   └── ...
│   └── marts/                   # (empty, ready for your marts)
├── migration_state.json         # Migration progress tracking
└── migration_results.json       # Detailed results & metrics
```

---

## 📊 Viewing Results

### 1. Check Migration Summary

```bash
# View final results
cat my_dbt_project/migration_results.json
```

**Example Output:**
```json
{
  "summary": {
    "total": 7,
    "completed": 7,
    "failed": 0,
    "skipped": 0,
    "pending": 0
  }
}
```

### 2. Inspect Generated Models

```bash
# List all generated SQL files
ls my_dbt_project/models/staging/*.sql

# View a specific model
cat my_dbt_project/models/staging/stg_customers.sql
```

### 3. Check Migration State

```bash
# See which models completed successfully
cat my_dbt_project/migration_state.json
```

---

## 🧪 Testing the Generated Models

### 1. Install dbt (if not already installed)

```bash
pip install dbt-duckdb
```

### 2. Compile the Models

```bash
cd my_dbt_project
dbt compile
```

### 3. Run the Models

```bash
dbt run
```

### 4. Test the Models

```bash
dbt test
```

---

## ⚙️ Advanced Usage

### Resume Failed Migration

If a migration fails partway through:

```bash
# The tool automatically detects existing migration_state.json
python main.py migrate --metadata metadata.json --project-path ./my_project
```

It will skip completed models and retry failed ones.

---

### Extract Metadata Only

```bash
# Save metadata without running migration
python main.py extract \
  --connection-string "YOUR_CONNECTION_STRING" \
  --output my_metadata.json
```

---

### Migrate Specific Models

Edit `migration_state.json` to set unwanted models to `"status": "skipped"`, then run:

```bash
python main.py migrate --metadata metadata.json --project-path ./my_project
```

---

## 🐛 Troubleshooting

### Issue: `UnicodeEncodeError` on Windows

**Symptom:** Errors about checkmark characters (✓) not encoding properly.

**Solution:** This is a cosmetic logging issue that doesn't affect functionality. The migration still completes successfully. To avoid seeing these errors:

1. Use `test_migration.py` instead of `main.py`
2. Or redirect output to a file:
   ```bash
   python main.py full --project-path ./my_project > output.log 2>&1
   ```

See the detailed explanation in the "Unicode Bug Explanation" section below.

---

### Issue: No ODBC Driver Found

**Symptom:** `pyodbc.Error: ('01000', "[01000] [unixODBC]...")`

**Solution:** Install ODBC Driver for SQL Server:
- **Windows:** Download from [Microsoft](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Linux:** `sudo apt-get install unixodbc-dev`
- **Mac:** `brew install unixodbc`

---

### Issue: Claude API Rate Limits

**Symptom:** `RateLimitError` from Anthropic API

**Solution:** The tool works in fallback mode without the API. Set longer delays between calls or upgrade your API plan.

---

### Issue: Migration Fails with "No plan found"

**Symptom:** All models fail with error "No plan found for model X"

**Solution:** This was fixed in the latest version. Make sure you're using the updated code with the fix to `agent_system.py` (lines 259-260).

---

## 📝 Command Reference

### `python main.py extract`

**Purpose:** Extract metadata from MSSQL database

**Arguments:**
- `--connection-string` (optional): MSSQL connection string. If omitted, uses mock data.
- `--output` (default: `mssql_metadata.json`): Output file path

**Example:**
```bash
python main.py extract --output my_metadata.json
```

---

### `python main.py init`

**Purpose:** Initialize dbt project structure

**Arguments:**
- `--project-path` (default: `./dbt_project`): Path for new dbt project

**Example:**
```bash
python main.py init --project-path ./production_migration
```

---

### `python main.py migrate`

**Purpose:** Run migration using extracted metadata

**Arguments:**
- `--metadata` (required): Path to metadata JSON file
- `--project-path` (required): Path to dbt project
- `--api-key` (optional): Anthropic API key (or use `ANTHROPIC_API_KEY` env var)

**Example:**
```bash
python main.py migrate \
  --metadata metadata.json \
  --project-path ./my_project \
  --api-key "sk-ant-..."
```

---

### `python main.py full`

**Purpose:** Run complete workflow (extract + init + migrate)

**Arguments:**
- `--connection-string` (optional): MSSQL connection string
- `--project-path` (default: `./dbt_project`): Path for dbt project
- `--api-key` (optional): Anthropic API key

**Example:**
```bash
python main.py full \
  --connection-string "DRIVER={...};SERVER=localhost;..." \
  --project-path ./complete_migration \
  --api-key "sk-ant-..."
```

---

### Global Flags

- `-v`, `--verbose`: Enable debug logging

**Example:**
```bash
python main.py full --project-path ./my_project -v
```

---

## 📈 Performance Tips

1. **Use Mock Mode for Testing** - Iterate on configuration without hitting your database
2. **Enable Claude API** - Get better migration strategies (but costs API credits)
3. **Start Small** - Test with a subset of tables first
4. **Check Logs** - Review `migration.log` for detailed execution info
5. **Resume on Failure** - The tool saves state, so you can resume if interrupted

---

## 🎯 Typical Workflow

```bash
# 1. Test with mock data first
python test_migration.py

# 2. Extract metadata from your database
python main.py extract \
  --connection-string "YOUR_CONNECTION_STRING" \
  --output prod_metadata.json

# 3. Review the metadata
cat prod_metadata.json

# 4. Run migration
python main.py full \
  --connection-string "YOUR_CONNECTION_STRING" \
  --project-path ./prod_migration

# 5. Review generated models
ls -la prod_migration/models/staging/

# 6. Test with dbt
cd prod_migration
dbt compile
dbt run

# 7. Customize as needed
# Edit the generated .sql files to add business logic
```

---

## 🔍 Example: Complete Migration

```bash
# Set API key for AI features
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Run complete migration
python main.py full \
  --connection-string "DRIVER={ODBC Driver 17 for SQL Server};SERVER=prod-db.company.com;DATABASE=Sales;UID=migration_user;PWD=SecurePass123!" \
  --project-path ./sales_to_dbt

# Output:
# ============================================================
# MSSQL to dbt Migration Test
# ============================================================
#
# Step 1: Extracting metadata...
# INFO - Connected to MSSQL successfully
# INFO - Extracted 23 tables/views
# INFO - Extracted 8 stored procedures
# Metadata saved to test_metadata.json
#
# Step 2: Initializing dbt project...
# INFO - dbt project initialized successfully
# dbt project created at ./sales_to_dbt
#
# Step 3: Running migration...
# INFO - Registered 6 agents
# INFO - Starting MSSQL to dbt Migration
#
# --- Phase 1: Assessment ---
# INFO - Assessment complete: 23 tables, 8 procedures
#
# --- Phase 2: Planning ---
# INFO - Plan created with 31 models
#
# --- Phase 3: Model Migration ---
# INFO - Migrating model: stg_customers
# INFO - Migrating model: stg_orders
# ...
# INFO - Migration Complete
# ============================================================
# MIGRATION RESULTS
# ============================================================
# Total Models: 31
# Completed: 29
# Failed: 2
# Pending: 0
# ============================================================

# Check the results
cat sales_to_dbt/migration_results.json

# Review failed models
cat sales_to_dbt/migration_state.json | grep -A5 '"status": "failed"'

# Test the generated models
cd sales_to_dbt
dbt compile
dbt run
```

---

## 🆘 Getting Help

1. **Check Logs:** Review `migration.log` for detailed error messages
2. **Review State:** Check `migration_state.json` to see which step failed
3. **Read CHANGES.md:** See what bugs were fixed and known issues
4. **Test with Mock Data:** Use `test_migration.py` to verify the tool works
5. **Check Requirements:** Ensure all dependencies are installed: `pip install -r requirements.txt`

---

## 📚 Additional Resources

- **[CHANGES.md](CHANGES.md)** - Detailed list of fixes and changes
- **[README.md](README.md)** - Project overview and architecture
- **[dbt Documentation](https://docs.getdbt.com/)** - Learn about dbt
- **[Anthropic Claude](https://docs.anthropic.com/)** - AI API documentation

---

## ⚡ Quick Reference Card

```bash
# Mock mode (no database)
python test_migration.py

# Extract only
python main.py extract --output my_data.json

# Full migration with database
python main.py full \
  --connection-string "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;UID=user;PWD=pass" \
  --project-path ./my_project

# With AI features
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py full --project-path ./smart_project

# Check results
cat my_project/migration_results.json
ls my_project/models/staging/

# Test with dbt
cd my_project && dbt run
```

---

**Happy Migrating! 🚀**

For issues or questions, refer to [CHANGES.md](CHANGES.md) for troubleshooting.
