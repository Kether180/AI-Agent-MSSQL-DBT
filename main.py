"""
Main CLI Application for MSSQL to dbt Migration Tool

This is the entry point for running migrations.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional

from metadata_extractor import MSSQLMetadataExtractor
from legacy_agent_system import (
    AgentContext, MigrationOrchestrator, AgentRole
)
from legacy_agents import (
    AssessmentAgent, PlannerAgent, ExecutorAgent,
    TesterAgent, RebuilderAgent, EvaluatorAgent
)


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def initialize_dbt_project(project_path: str) -> bool:
    """
    Initialize a basic dbt project structure
    
    Args:
        project_path: Path to create the dbt project
        
    Returns:
        True if successful
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing dbt project at {project_path}")
    
    try:
        # Create directory structure
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, 'models', 'staging'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'models', 'marts'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'seeds'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'tests'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'macros'), exist_ok=True)
        
        # Create dbt_project.yml
        dbt_project_yml = f"""name: 'mssql_migration'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  mssql_migration:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
"""
        
        dbt_project_path = os.path.join(project_path, 'dbt_project.yml')
        with open(dbt_project_path, 'w') as f:
            f.write(dbt_project_yml)
        
        # Create profiles.yml (using DuckDB for POC)
        profiles_dir = os.path.join(Path.home(), '.dbt')
        os.makedirs(profiles_dir, exist_ok=True)
        
        profiles_yml = """default:
  outputs:
    dev:
      type: duckdb
      path: mssql_migration.duckdb
      schema: main
  target: dev
"""
        
        profiles_path = os.path.join(profiles_dir, 'profiles.yml')
        if not os.path.exists(profiles_path):
            with open(profiles_path, 'w') as f:
                f.write(profiles_yml)
        
        # Create sources.yml for MSSQL sources
        sources_yml = """version: 2

sources:
  - name: mssql
    description: Source tables from MSSQL database
    tables:
      # Tables will be added by the migration tool
"""
        
        sources_path = os.path.join(project_path, 'models', 'staging', 'sources.yml')
        with open(sources_path, 'w') as f:
            f.write(sources_yml)
        
        logger.info("dbt project initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing dbt project: {e}")
        return False


def extract_metadata(connection_string: Optional[str], output_path: str) -> dict:
    """
    Extract metadata from MSSQL
    
    Args:
        connection_string: MSSQL connection string (None for mock mode)
        output_path: Path to save metadata JSON
        
    Returns:
        Extracted metadata dictionary
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting metadata extraction")
    
    extractor = MSSQLMetadataExtractor(connection_string)
    metadata = extractor.extract_all_metadata()
    extractor.save_metadata(metadata, output_path)
    extractor.close()
    
    logger.info(f"Metadata extracted and saved to {output_path}")
    return metadata


def run_migration(
    metadata_path: str,
    dbt_project_path: str,
    api_key: Optional[str] = None
) -> dict:
    """
    Run the full migration workflow
    
    Args:
        metadata_path: Path to metadata JSON file
        dbt_project_path: Path to dbt project
        api_key: Anthropic API key (optional)
        
    Returns:
        Migration results dictionary
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting migration workflow")
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Create agent context
    context = AgentContext(
        metadata=metadata,
        dbt_project_path=dbt_project_path,
        api_key=api_key or os.environ.get('ANTHROPIC_API_KEY')
    )
    
    # Create orchestrator
    orchestrator = MigrationOrchestrator(context)
    
    # Register all agents
    orchestrator.register_agent(AssessmentAgent())
    orchestrator.register_agent(PlannerAgent())
    orchestrator.register_agent(ExecutorAgent())
    orchestrator.register_agent(TesterAgent())
    orchestrator.register_agent(RebuilderAgent())
    orchestrator.register_agent(EvaluatorAgent())
    
    # Run migration
    results = orchestrator.run_full_migration()
    
    # Save results
    results_path = os.path.join(dbt_project_path, 'migration_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Migration complete. Results saved to {results_path}")
    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MSSQL to dbt Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract metadata (mock mode for POC)
  python main.py extract --output metadata.json
  
  # Initialize dbt project
  python main.py init --project-path ./dbt_project
  
  # Run full migration
  python main.py migrate --metadata metadata.json --project-path ./dbt_project
  
  # Run with Claude API
  python main.py migrate --metadata metadata.json --project-path ./dbt_project --api-key YOUR_KEY
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract metadata from MSSQL')
    extract_parser.add_argument(
        '--connection-string',
        help='MSSQL connection string (optional, uses mock mode if not provided)'
    )
    extract_parser.add_argument(
        '--output',
        default='mssql_metadata.json',
        help='Output path for metadata JSON (default: mssql_metadata.json)'
    )
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize dbt project')
    init_parser.add_argument(
        '--project-path',
        default='./dbt_project',
        help='Path for dbt project (default: ./dbt_project)'
    )
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run migration')
    migrate_parser.add_argument(
        '--metadata',
        required=True,
        help='Path to metadata JSON file'
    )
    migrate_parser.add_argument(
        '--project-path',
        required=True,
        help='Path to dbt project'
    )
    migrate_parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    
    # Full command (extract + init + migrate)
    full_parser = subparsers.add_parser('full', help='Run complete workflow')
    full_parser.add_argument(
        '--connection-string',
        help='MSSQL connection string (optional)'
    )
    full_parser.add_argument(
        '--project-path',
        default='./dbt_project',
        help='Path for dbt project (default: ./dbt_project)'
    )
    full_parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
    )
    
    # Global arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'extract':
            extract_metadata(
                args.connection_string,
                args.output
            )
            print(f"\n✅ Metadata extracted successfully to {args.output}")
            
        elif args.command == 'init':
            if initialize_dbt_project(args.project_path):
                print(f"\n✅ dbt project initialized at {args.project_path}")
            else:
                print("\n❌ Failed to initialize dbt project")
                return 1
                
        elif args.command == 'migrate':
            results = run_migration(
                args.metadata,
                args.project_path,
                args.api_key
            )
            
            print("\n" + "=" * 60)
            print("MIGRATION SUMMARY")
            print("=" * 60)
            print(f"Total Models: {results['summary']['total']}")
            print(f"✅ Completed: {results['summary']['completed']}")
            print(f"❌ Failed: {results['summary']['failed']}")
            print(f"⏭️  Skipped: {results['summary']['skipped']}")
            print(f"⏸️  Pending: {results['summary']['pending']}")
            print("=" * 60)
            
        elif args.command == 'full':
            # Extract
            print("\n📊 Step 1: Extracting metadata...")
            metadata_path = 'mssql_metadata.json'
            extract_metadata(args.connection_string, metadata_path)
            
            # Initialize
            print("\n🏗️  Step 2: Initializing dbt project...")
            if not initialize_dbt_project(args.project_path):
                print("❌ Failed to initialize dbt project")
                return 1
            
            # Migrate
            print("\n🚀 Step 3: Running migration...")
            results = run_migration(
                metadata_path,
                args.project_path,
                args.api_key
            )
            
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE")
            print("=" * 60)
            print(f"✅ Completed: {results['summary']['completed']}")
            print(f"❌ Failed: {results['summary']['failed']}")
            print(f"📁 dbt project: {args.project_path}")
            print("=" * 60)
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
