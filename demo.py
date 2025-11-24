#!/usr/bin/env python3
"""
Demo Script for MSSQL to dbt Migration Tool

This script demonstrates the complete migration workflow using mock data.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metadata_extractor import MSSQLMetadataExtractor
from legacy_agent_system import AgentContext, MigrationOrchestrator
from legacy_agents import (
    AssessmentAgent, PlannerAgent, ExecutorAgent,
    TesterAgent, RebuilderAgent, EvaluatorAgent
)
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(text):
    """Print a section header"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}\n")


def cleanup_demo_files():
    """Clean up any existing demo files"""
    files_to_remove = [
        'mssql_metadata.json',
        'migration.log'
    ]
    
    dirs_to_remove = [
        'demo_dbt_project'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            logger.info(f"Removed existing file: {file}")
    
    for dir in dirs_to_remove:
        if os.path.exists(dir):
            shutil.rmtree(dir)
            logger.info(f"Removed existing directory: {dir}")


def demo_metadata_extraction():
    """Demonstrate metadata extraction"""
    print_section("Step 1: Metadata Extraction")
    
    print("Extracting metadata from MSSQL database (mock mode)...")
    print("In production, this would connect to your actual MSSQL instance.\n")
    
    # Create extractor in mock mode
    extractor = MSSQLMetadataExtractor()
    
    # Extract metadata
    metadata = extractor.extract_all_metadata()
    
    # Save to file
    extractor.save_metadata(metadata, 'mssql_metadata.json')
    
    # Display summary
    print("📊 Extraction Summary:")
    print(f"   Tables: {metadata['summary']['total_tables']}")
    print(f"   Views: {metadata['summary']['total_views']}")
    print(f"   Stored Procedures: {metadata['summary']['total_procedures']}")
    print(f"   Dependencies: {metadata['summary']['total_dependencies']}")
    
    # Show some example objects
    print("\n📋 Sample Objects:")
    for table in metadata['tables'][:3]:
        print(f"   - {table['schema']}.{table['name']} "
              f"({table['object_type']}, {len(table['columns'])} columns)")
    
    return metadata


def demo_dbt_initialization():
    """Demonstrate dbt project initialization"""
    print_section("Step 2: dbt Project Initialization")
    
    print("Initializing dbt project structure...")
    
    project_path = 'demo_dbt_project'
    
    # Create directory structure
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, 'models', 'staging'), exist_ok=True)
    os.makedirs(os.path.join(project_path, 'models', 'marts'), exist_ok=True)
    
    # Create dbt_project.yml
    dbt_project_yml = """name: 'mssql_migration_demo'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

models:
  mssql_migration_demo:
    staging:
      +materialized: view
"""
    
    with open(os.path.join(project_path, 'dbt_project.yml'), 'w') as f:
        f.write(dbt_project_yml)
    
    # Create sources.yml
    sources_yml = """version: 2

sources:
  - name: mssql
    description: Source tables from MSSQL
    tables: []
"""
    
    with open(os.path.join(project_path, 'models', 'staging', 'sources.yml'), 'w') as f:
        f.write(sources_yml)
    
    print(f"✅ dbt project created at: {project_path}")
    print("\n📁 Project Structure:")
    print(f"   {project_path}/")
    print("   ├── dbt_project.yml")
    print("   └── models/")
    print("       ├── staging/")
    print("       │   └── sources.yml")
    print("       └── marts/")
    
    return project_path


def demo_agent_workflow(metadata, project_path):
    """Demonstrate the agent workflow"""
    print_section("Step 3: Multi-Agent Migration Workflow")
    
    # Create agent context
    context = AgentContext(
        metadata=metadata,
        dbt_project_path=project_path,
        api_key=os.environ.get('ANTHROPIC_API_KEY')
    )
    
    if context.api_key:
        print("🤖 Claude API detected - using AI-powered agents")
    else:
        print("📝 Running in mock mode - using rule-based logic")
        print("   (Set ANTHROPIC_API_KEY environment variable for AI features)")
    
    # Create orchestrator
    orchestrator = MigrationOrchestrator(context)
    
    # Register agents
    print("\n🔧 Registering specialized agents:")
    agents = [
        ("Assessment", AssessmentAgent()),
        ("Planner", PlannerAgent()),
        ("Executor", ExecutorAgent()),
        ("Tester", TesterAgent()),
        ("Rebuilder", RebuilderAgent()),
        ("Evaluator", EvaluatorAgent())
    ]
    
    for name, agent in agents:
        orchestrator.register_agent(agent)
        print(f"   ✓ {name} Agent")
    
    # Run migration
    print("\n🚀 Starting migration workflow...\n")
    
    results = orchestrator.run_full_migration()
    
    return results


def display_results(results):
    """Display migration results"""
    print_section("Migration Results")
    
    # Assessment results
    if results.get('assessment'):
        assessment = results['assessment']
        print("📊 Assessment:")
        print(f"   Total objects analyzed: {assessment.get('total_objects', 0)}")
        
        if 'strategy' in assessment:
            strategy = assessment['strategy']
            print(f"\n   Strategy: {strategy.get('approach', 'N/A')}")
            print(f"   Estimated Duration: {strategy.get('estimated_duration', 'N/A')}")
        
        if 'recommendations' in assessment and assessment['recommendations']:
            print("\n   Key Recommendations:")
            for rec in assessment['recommendations'][:3]:
                print(f"     • {rec}")
    
    # Planning results
    if results.get('planning'):
        planning = results['planning']
        print(f"\n📋 Planning:")
        print(f"   Models to migrate: {len(planning.get('models', []))}")
        print(f"   Execution order defined: ✓")
    
    # Model migration results
    if results.get('models'):
        print(f"\n🔨 Model Migration:")
        print(f"   Total models processed: {len(results['models'])}")
        
        for model in results['models'][:5]:  # Show first 5
            status_icon = "✅" if model['status'] == 'completed' else "❌"
            print(f"     {status_icon} {model['model']} - {model['status']}")
    
    # Summary
    summary = results.get('summary', {})
    print(f"\n📈 Summary:")
    print(f"   Total: {summary.get('total', 0)}")
    print(f"   ✅ Completed: {summary.get('completed', 0)}")
    print(f"   ❌ Failed: {summary.get('failed', 0)}")
    print(f"   ⏭️  Skipped: {summary.get('skipped', 0)}")
    print(f"   ⏸️  Pending: {summary.get('pending', 0)}")


def show_generated_files(project_path):
    """Show the generated dbt files"""
    print_section("Generated dbt Files")
    
    models_dir = os.path.join(project_path, 'models', 'staging')
    
    if os.path.exists(models_dir):
        files = [f for f in os.listdir(models_dir) if f.endswith('.sql')]
        
        print(f"📁 Generated {len(files)} dbt models in {models_dir}:\n")
        
        for file in files[:5]:  # Show first 5 files
            print(f"   • {file}")
            
            # Show a snippet of the first file
            if file == files[0]:
                file_path = os.path.join(models_dir, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')[:15]  # First 15 lines
                    
                    print(f"\n   Preview of {file}:")
                    print("   " + "─" * 60)
                    for line in lines:
                        print(f"   {line}")
                    print("   " + "─" * 60)


def main():
    """Run the complete demo"""
    print_banner("MSSQL to dbt Agentic Migration Tool - DEMO")
    
    print("This demo will:")
    print("  1. Extract metadata from a mock MSSQL database")
    print("  2. Initialize a dbt project structure")
    print("  3. Run the multi-agent migration workflow")
    print("  4. Display the results")
    
    input("\nPress Enter to start the demo...")
    
    try:
        # Clean up any existing demo files
        cleanup_demo_files()
        
        # Step 1: Extract metadata
        metadata = demo_metadata_extraction()
        
        input("\nPress Enter to continue to dbt initialization...")
        
        # Step 2: Initialize dbt project
        project_path = demo_dbt_initialization()
        
        input("\nPress Enter to start the agent workflow...")
        
        # Step 3: Run agent workflow
        results = demo_agent_workflow(metadata, project_path)
        
        # Step 4: Display results
        display_results(results)
        
        # Step 5: Show generated files
        show_generated_files(project_path)
        
        # Final summary
        print_banner("Demo Complete!")
        
        print("✅ The migration POC has completed successfully!\n")
        print("Key Outcomes:")
        print(f"  • Metadata extracted and analyzed")
        print(f"  • dbt project created at: {project_path}")
        print(f"  • {results['summary']['completed']} models successfully migrated")
        print(f"  • Migration state saved for resumability")
        
        print("\n📁 Files created:")
        print("  • mssql_metadata.json - Extracted metadata")
        print("  • demo_dbt_project/ - Complete dbt project")
        print("  • demo_dbt_project/migration_state.json - Migration state")
        print("  • demo_dbt_project/migration_results.json - Detailed results")
        print("  • migration.log - Detailed execution log")
        
        print("\n🚀 Next Steps:")
        print("  1. Review the generated dbt models")
        print("  2. Customize the SQL as needed")
        print("  3. Run 'dbt run' to execute the models")
        print("  4. Add tests and documentation")
        
        print("\n💡 To use with real MSSQL:")
        print("  python main.py full --connection-string 'YOUR_CONNECTION_STRING'")
        
        print("\n🤖 To enable AI features:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("  python demo.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during demo: {e}")
        logger.exception("Demo failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
