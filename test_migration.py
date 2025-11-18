#!/usr/bin/env python3
"""
Simple test script to run migration without emoji encoding issues
"""
import os
import sys
import logging

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from main import extract_metadata, initialize_dbt_project, run_migration

def main():
    print("=" * 60)
    print("MSSQL to dbt Migration Test")
    print("=" * 60)

    # Step 1: Extract metadata
    print("\nStep 1: Extracting metadata...")
    metadata_path = 'test_metadata.json'
    extract_metadata(None, metadata_path)
    print(f"Metadata saved to {metadata_path}")

    # Step 2: Initialize dbt project
    print("\nStep 2: Initializing dbt project...")
    project_path = './test_dbt_project'
    if initialize_dbt_project(project_path):
        print(f"dbt project created at {project_path}")
    else:
        print("Failed to initialize dbt project")
        return 1

    # Step 3: Run migration
    print("\nStep 3: Running migration...")
    results = run_migration(metadata_path, project_path)

    # Display results
    print("\n" + "=" * 60)
    print("MIGRATION RESULTS")
    print("=" * 60)
    summary = results.get('summary', {})
    print(f"Total Models: {summary.get('total', 0)}")
    print(f"Completed: {summary.get('completed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Pending: {summary.get('pending', 0)}")
    print("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
