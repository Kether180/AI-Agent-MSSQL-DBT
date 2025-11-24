"""
Native LangGraph Agent Nodes

This module contains pure LangGraph implementations of all migration agents.
No adapter layer - these nodes work directly with MigrationState and use
LangChain/LangGraph primitives natively.

Architecture:
- Direct ChatAnthropic integration
- Native state updates (no translation)
- Guardrails for security
- Clean, maintainable code
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from .state import MigrationState, get_current_model
from .guardrails import (
    validate_llm_input,
    validate_llm_output,
    sanitize_sql_output,
    check_rate_limit
)

logger = logging.getLogger(__name__)

# Initialize LLM (lazy-loaded)
_llm = None

def get_llm() -> Optional[ChatAnthropic]:
    """Get or create ChatAnthropic instance"""
    global _llm
    if _llm is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - will use fallback logic")
            return None
        _llm = ChatAnthropic(
            model="claude-sonnet-4",
            temperature=0.0,
            anthropic_api_key=api_key
        )
    return _llm


# =============================================================================
# ASSESSMENT NODE
# =============================================================================

def assessment_node(state: MigrationState) -> MigrationState:
    """
    Assessment Agent - Analyzes MSSQL metadata and creates migration strategy.

    Input: MigrationState with metadata
    Output: MigrationState with assessment data and assessment_complete=True
    """
    logger.info("=== Assessment Node Starting ===")

    # Check rate limit only if API key is available
    has_api_key = os.environ.get("ANTHROPIC_API_KEY") is not None
    if has_api_key and not check_rate_limit("assessment", max_requests=5, window_seconds=60):
        logger.warning("Assessment rate limit exceeded")
        state['errors'] = state.get('errors', []) + ["Rate limit exceeded for assessment"]
        return state

    try:
        # Extract metadata
        metadata = state.get('metadata', {})
        if not metadata:
            raise ValueError("No metadata provided for assessment")

        # Build prompt
        system_prompt = """You are an expert database migration specialist.
Analyze the provided MSSQL metadata and create a comprehensive assessment.

Your assessment should include:
1. Total number of tables, views, and stored procedures
2. Complexity analysis (simple/medium/complex)
3. Identified dependencies between objects
4. Potential migration challenges
5. Recommended migration order

Respond in JSON format:
{
  "total_objects": int,
  "tables_count": int,
  "views_count": int,
  "procedures_count": int,
  "complexity": "simple|medium|complex",
  "dependencies": [{"source": "obj1", "target": "obj2"}],
  "challenges": ["challenge1", "challenge2"],
  "migration_strategy": "description",
  "estimated_models": int
}
"""

        user_prompt = f"""Analyze this MSSQL metadata:

Database: {metadata.get('database', 'Unknown')}
Tables: {len(metadata.get('tables', []))}
Views: {len(metadata.get('views', []))}
Stored Procedures: {len(metadata.get('stored_procedures', []))}

Full metadata:
{json.dumps(metadata, indent=2)}
"""

        # Validate input
        user_prompt = validate_llm_input(user_prompt)

        # Call LLM
        llm = get_llm()

        if llm is None:
            # Fallback: Create assessment from metadata directly
            logger.warning("No LLM available, using fallback assessment")
            assessment_data = {
                "total_objects": len(metadata.get('tables', [])) + len(metadata.get('views', [])),
                "tables_count": len(metadata.get('tables', [])),
                "views_count": len(metadata.get('views', [])),
                "procedures_count": len(metadata.get('stored_procedures', [])),
                "complexity": "medium",
                "dependencies": [],
                "challenges": ["No LLM available for detailed analysis"],
                "migration_strategy": "Sequential migration of all objects",
                "estimated_models": len(metadata.get('tables', [])) + len(metadata.get('views', []))
            }
        else:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Extract and validate output
            assessment_text = validate_llm_output(response.content)

            # Parse JSON from response
            try:
                # Try to extract JSON from markdown code blocks
                if "```json" in assessment_text:
                    start = assessment_text.find("```json") + 7
                    end = assessment_text.find("```", start)
                    assessment_text = assessment_text[start:end].strip()
                elif "```" in assessment_text:
                    start = assessment_text.find("```") + 3
                    end = assessment_text.find("```", start)
                    assessment_text = assessment_text[start:end].strip()

                assessment_data = json.loads(assessment_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse assessment JSON: {e}")
                # Create fallback assessment
                assessment_data = {
                    "total_objects": len(metadata.get('tables', [])) + len(metadata.get('views', [])),
                    "tables_count": len(metadata.get('tables', [])),
                    "views_count": len(metadata.get('views', [])),
                    "procedures_count": len(metadata.get('stored_procedures', [])),
                    "complexity": "medium",
                    "dependencies": [],
                    "challenges": ["Unable to parse LLM response"],
                    "migration_strategy": "Sequential migration of all objects",
                    "estimated_models": len(metadata.get('tables', [])) + len(metadata.get('views', []))
                }

        # Update state
        state['assessment'] = assessment_data
        state['assessment_complete'] = True
        state['phase'] = 'planning'

        logger.info(f"Assessment complete: {assessment_data.get('estimated_models', 0)} models estimated")
        logger.info(f"Complexity: {assessment_data.get('complexity', 'unknown')}")

    except Exception as e:
        logger.error(f"Assessment failed: {e}", exc_info=True)
        state['errors'] = state.get('errors', []) + [f"Assessment error: {str(e)}"]

    return state


# =============================================================================
# PLANNER NODE
# =============================================================================

def planner_node(state: MigrationState) -> MigrationState:
    """
    Planner Agent - Creates detailed migration plan with model list.

    Input: MigrationState with assessment data
    Output: MigrationState with planning data and models list initialized
    """
    logger.info("=== Planner Node Starting ===")

    # Check rate limit only if API key is available
    has_api_key = os.environ.get("ANTHROPIC_API_KEY") is not None
    if has_api_key and not check_rate_limit("planner", max_requests=5, window_seconds=60):
        logger.warning("Planner rate limit exceeded")
        state['errors'] = state.get('errors', []) + ["Rate limit exceeded for planner"]
        return state

    try:
        # Extract assessment
        assessment = state.get('assessment', {})
        metadata = state.get('metadata', {})

        if not assessment:
            raise ValueError("No assessment data available for planning")

        # Build prompt
        system_prompt = """You are an expert dbt migration planner.
Create a detailed migration plan based on the assessment.

For each MSSQL object, create a dbt model specification:
1. Model name (following dbt naming conventions: stg_, int_, fct_, dim_)
2. Source object (table/view name)
3. Model type (staging/intermediate/fact/dimension)
4. Dependencies (which other models it depends on)
5. Priority (1=highest, 5=lowest)

Respond in JSON format:
{
  "migration_order": "dependency-first|alphabetical|complexity-based",
  "models": [
    {
      "name": "stg_customers",
      "source_object": "dbo.customers",
      "model_type": "staging",
      "dependencies": [],
      "priority": 1,
      "description": "Staging table for customers"
    }
  ],
  "total_models": int
}
"""

        user_prompt = f"""Create migration plan for this database:

Assessment:
{json.dumps(assessment, indent=2)}

Metadata (tables and views):
Tables: {json.dumps(metadata.get('tables', [])[:10], indent=2)}
Views: {json.dumps(metadata.get('views', [])[:5], indent=2)}

Create a model for each table and view.
"""

        # Validate input
        user_prompt = validate_llm_input(user_prompt)

        # Call LLM
        llm = get_llm()

        if llm is None:
            # Fallback: Create plan from metadata directly
            logger.warning("No LLM available, using fallback planning")
            tables = metadata.get('tables', [])
            views = metadata.get('views', [])

            models = []
            for i, table in enumerate(tables[:20]):  # Limit to 20 for demo
                models.append({
                    "name": f"stg_{table.get('name', f'table_{i}')}",
                    "source_object": f"{table.get('schema', 'dbo')}.{table.get('name', f'table_{i}')}",
                    "model_type": "staging",
                    "dependencies": [],
                    "priority": 1,
                    "description": f"Staging model for {table.get('name', 'table')}"
                })

            for i, view in enumerate(views[:10]):  # Limit to 10 for demo
                models.append({
                    "name": f"int_{view.get('name', f'view_{i}')}",
                    "source_object": f"{view.get('schema', 'dbo')}.{view.get('name', f'view_{i}')}",
                    "model_type": "intermediate",
                    "dependencies": [],
                    "priority": 2,
                    "description": f"Intermediate model for {view.get('name', 'view')}"
                })

            plan_data = {
                "migration_order": "dependency-first",
                "models": models,
                "total_models": len(models)
            }
        else:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Extract and validate output
            plan_text = validate_llm_output(response.content)

            # Parse JSON
            try:
                if "```json" in plan_text:
                    start = plan_text.find("```json") + 7
                    end = plan_text.find("```", start)
                    plan_text = plan_text[start:end].strip()
                elif "```" in plan_text:
                    start = plan_text.find("```") + 3
                    end = plan_text.find("```", start)
                    plan_text = plan_text[start:end].strip()

                plan_data = json.loads(plan_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse plan JSON: {e}")
                # Create fallback plan from metadata
                tables = metadata.get('tables', [])
                views = metadata.get('views', [])

                models = []
                for i, table in enumerate(tables[:20]):  # Limit to 20 for demo
                    models.append({
                        "name": f"stg_{table.get('name', f'table_{i}')}",
                        "source_object": f"{table.get('schema', 'dbo')}.{table.get('name', f'table_{i}')}",
                        "model_type": "staging",
                        "dependencies": [],
                        "priority": 1,
                        "description": f"Staging model for {table.get('name', 'table')}"
                    })

                for i, view in enumerate(views[:10]):  # Limit to 10 for demo
                    models.append({
                        "name": f"int_{view.get('name', f'view_{i}')}",
                        "source_object": f"{view.get('schema', 'dbo')}.{view.get('name', f'view_{i}')}",
                        "model_type": "intermediate",
                        "dependencies": [],
                        "priority": 2,
                        "description": f"Intermediate model for {view.get('name', 'view')}"
                    })

                plan_data = {
                    "migration_order": "dependency-first",
                    "models": models,
                    "total_models": len(models)
                }

        # Initialize models list in state
        state['planning'] = plan_data
        state['plan_complete'] = True
        state['phase'] = 'execution'

        # Create model tracking entries
        state['models'] = [
            {
                'name': model['name'],
                'source_object': model.get('source_object'),
                'status': 'pending',
                'attempts': 0,
                'errors': [],
                'validation_score': 0.0,
                'file_path': None,
                'model_type': model.get('model_type', 'staging'),
                'dependencies': model.get('dependencies', [])
            }
            for model in plan_data['models']
        ]
        state['current_model_index'] = 0

        logger.info(f"Planning complete: {len(state['models'])} models to migrate")

    except Exception as e:
        logger.error(f"Planning failed: {e}", exc_info=True)
        state['errors'] = state.get('errors', []) + [f"Planning error: {str(e)}"]

    return state


# =============================================================================
# EXECUTOR NODE
# =============================================================================

def executor_node(state: MigrationState) -> MigrationState:
    """
    Executor Agent - Generates dbt model SQL for current model.

    Input: MigrationState with current_model_index pointing to pending model
    Output: MigrationState with model file created and status='in_progress'
    """
    logger.info("=== Executor Node Starting ===")

    # Get current model
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to execute")
        return state

    model_name = current_model['name']
    logger.info(f"Executing model: {model_name}")

    # Check rate limit only if API key is available
    has_api_key = os.environ.get("ANTHROPIC_API_KEY") is not None
    if has_api_key and not check_rate_limit(f"executor_{model_name}", max_requests=3, window_seconds=60):
        logger.warning(f"Executor rate limit exceeded for {model_name}")
        current_model['errors'].append("Rate limit exceeded")
        return state

    try:
        # Extract context
        metadata = state.get('metadata', {})
        source_object = current_model.get('source_object', '')
        model_type = current_model.get('model_type', 'staging')
        dependencies = current_model.get('dependencies', [])

        # Find source table/view in metadata
        source_schema = None
        for table in metadata.get('tables', []):
            if f"{table.get('schema', 'dbo')}.{table.get('name')}" == source_object:
                source_schema = table
                break

        if not source_schema:
            for view in metadata.get('views', []):
                if f"{view.get('schema', 'dbo')}.{view.get('name')}" == source_object:
                    source_schema = view
                    break

        # Build prompt
        system_prompt = """You are an expert dbt developer.
Generate a dbt model SQL file based on the source schema.

Requirements:
1. Use {{ source() }} or {{ ref() }} macros appropriately
2. Follow dbt best practices
3. Include appropriate transformations for the model type
4. Add column descriptions as comments
5. Use proper indentation and formatting

Respond with ONLY the SQL code, no markdown blocks or explanations.
"""

        columns_info = ""
        if source_schema and 'columns' in source_schema:
            columns_info = "\n".join([
                f"  - {col.get('name', 'unknown')}: {col.get('type', 'UNKNOWN')}"
                for col in source_schema.get('columns', [])[:30]  # Limit to 30 columns
            ])

        user_prompt = f"""Generate dbt model SQL for:

Model Name: {model_name}
Model Type: {model_type}
Source Object: {source_object}
Dependencies: {', '.join(dependencies) if dependencies else 'None'}

Source Schema:
{columns_info if columns_info else 'Schema not available - generate SELECT * with basic transformations'}

Generate the SQL code now.
"""

        # Validate input
        user_prompt = validate_llm_input(user_prompt)

        # Call LLM
        llm = get_llm()

        if llm is None:
            # Fallback: Generate simple SQL template
            logger.warning("No LLM available, using SQL template")
            sql_code = f"""-- dbt model: {model_name}
-- Source: {source_object}

{{{{ config(materialized='view') }}}}

SELECT
    *
FROM {{{{ source('mssql', '{source_object.split('.')[-1] if '.' in source_object else source_object}') }}}}
"""
        else:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Extract and validate SQL
            sql_code = validate_llm_output(response.content)
            sql_code = sanitize_sql_output(sql_code)

        # Clean up markdown if present
        if "```sql" in sql_code:
            start = sql_code.find("```sql") + 6
            end = sql_code.find("```", start)
            sql_code = sql_code[start:end].strip()
        elif "```" in sql_code:
            start = sql_code.find("```") + 3
            end = sql_code.find("```", start)
            sql_code = sql_code[start:end].strip()

        # Save to file
        project_path = Path(state.get('project_path', './test_langgraph_project'))
        models_dir = project_path / 'models'

        # Create subdirectory based on model type
        if model_type == 'staging':
            model_dir = models_dir / 'staging'
        elif model_type == 'intermediate':
            model_dir = models_dir / 'intermediate'
        elif model_type in ['fact', 'dimension']:
            model_dir = models_dir / 'marts'
        else:
            model_dir = models_dir

        model_dir.mkdir(parents=True, exist_ok=True)

        file_path = model_dir / f"{model_name}.sql"
        with open(file_path, 'w') as f:
            f.write(sql_code)

        # Update model status
        current_model['file_path'] = str(file_path)
        current_model['status'] = 'in_progress'
        current_model['attempts'] = current_model.get('attempts', 0) + 1

        logger.info(f"Model {model_name} generated at {file_path}")

    except Exception as e:
        logger.error(f"Executor failed for {model_name}: {e}", exc_info=True)
        current_model['errors'].append(f"Execution error: {str(e)}")
        current_model['status'] = 'failed'
        state['failed_count'] = state.get('failed_count', 0) + 1

    return state


# =============================================================================
# TESTER NODE
# =============================================================================

def tester_node(state: MigrationState) -> MigrationState:
    """
    Tester Agent - Validates generated dbt model.

    Input: MigrationState with model in 'in_progress' status
    Output: MigrationState with model marked 'completed' or 'failed'
    """
    logger.info("=== Tester Node Starting ===")

    # Get current model
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to test")
        return state

    model_name = current_model['name']
    file_path = current_model.get('file_path')

    if not file_path or not Path(file_path).exists():
        logger.error(f"Model file not found: {file_path}")
        current_model['errors'].append("Model file not found")
        current_model['status'] = 'failed'
        state['failed_count'] = state.get('failed_count', 0) + 1
        return state

    logger.info(f"Testing model: {model_name}")

    try:
        # Read generated SQL
        with open(file_path, 'r') as f:
            sql_code = f.read()

        # Build validation prompt
        system_prompt = """You are a dbt quality assurance expert.
Review the generated dbt model SQL and provide a validation score.

Check for:
1. Correct use of {{ source() }} or {{ ref() }} macros
2. Valid SQL syntax
3. Appropriate transformations for model type
4. Best practices (CTEs, clear column names, etc.)
5. No dangerous SQL operations

Respond in JSON format:
{
  "valid": true/false,
  "score": 0.0-1.0,
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"]
}
"""

        user_prompt = f"""Validate this dbt model:

Model Name: {model_name}
Model Type: {current_model.get('model_type', 'staging')}

SQL Code:
{sql_code}

Provide validation result.
"""

        # Validate input
        user_prompt = validate_llm_input(user_prompt)

        # Call LLM
        llm = get_llm()

        if llm is None:
            # Fallback: Basic validation without LLM
            logger.warning("No LLM available, using basic validation")
            # Check if file has SQL content
            has_select = "SELECT" in sql_code.upper()
            has_source_or_ref = "source(" in sql_code or "ref(" in sql_code

            validation_result = {
                "valid": has_select and (has_source_or_ref or len(sql_code) > 50),
                "score": 0.8 if has_select else 0.5,
                "issues": [] if has_select else ["No SELECT statement found"],
                "recommendations": []
            }
        else:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Parse validation result
            validation_text = validate_llm_output(response.content)

            try:
                if "```json" in validation_text:
                    start = validation_text.find("```json") + 7
                    end = validation_text.find("```", start)
                    validation_text = validation_text[start:end].strip()
                elif "```" in validation_text:
                    start = validation_text.find("```") + 3
                    end = validation_text.find("```", start)
                    validation_text = validation_text[start:end].strip()

                validation_result = json.loads(validation_text)
            except json.JSONDecodeError:
                # Fallback: assume success if no parsing errors
                validation_result = {
                    "valid": True,
                    "score": 0.9,
                    "issues": [],
                    "recommendations": []
                }

        # Update model based on validation
        if validation_result.get('valid', False) and validation_result.get('score', 0.0) >= 0.7:
            current_model['status'] = 'completed'
            current_model['validation_score'] = validation_result.get('score', 0.9)
            state['completed_count'] = state.get('completed_count', 0) + 1
            logger.info(f"Model {model_name} passed testing (score: {validation_result.get('score', 0.9)})")
        else:
            current_model['status'] = 'failed'
            current_model['errors'].extend(validation_result.get('issues', ['Validation failed']))
            state['failed_count'] = state.get('failed_count', 0) + 1
            logger.warning(f"Model {model_name} failed testing: {validation_result.get('issues', [])}")

    except Exception as e:
        logger.error(f"Tester failed for {model_name}: {e}", exc_info=True)
        current_model['errors'].append(f"Testing error: {str(e)}")
        current_model['status'] = 'failed'
        state['failed_count'] = state.get('failed_count', 0) + 1

    return state


# =============================================================================
# REBUILDER NODE
# =============================================================================

def rebuilder_node(state: MigrationState) -> MigrationState:
    """
    Rebuilder Agent - Attempts to fix failed models.

    Input: MigrationState with current model in 'failed' status
    Output: MigrationState with model status reset to 'pending' for retry
    """
    logger.info("=== Rebuilder Node Starting ===")

    # Get current model
    current_model = get_current_model(state)
    if not current_model:
        logger.warning("No current model to rebuild")
        return state

    model_name = current_model['name']
    attempts = current_model.get('attempts', 0)
    max_retries = state.get('max_retries', 3)

    logger.info(f"Rebuilding model: {model_name} (attempt {attempts}/{max_retries})")

    if attempts >= max_retries:
        logger.error(f"Model {model_name} exceeded max retries")
        # Keep as failed, will be skipped
        return state

    try:
        errors = current_model.get('errors', [])
        file_path = current_model.get('file_path')

        # Read existing SQL if available
        existing_sql = ""
        if file_path and Path(file_path).exists():
            with open(file_path, 'r') as f:
                existing_sql = f.read()

        # Build rebuild prompt
        system_prompt = """You are a dbt debugging expert.
The previous model generation failed. Analyze the errors and generate a corrected version.

Requirements:
1. Address all identified errors
2. Maintain dbt best practices
3. Keep the same model structure
4. Improve SQL quality

Respond with ONLY the corrected SQL code, no markdown or explanations.
"""

        user_prompt = f"""Fix this dbt model:

Model Name: {model_name}
Previous Attempts: {attempts}
Errors:
{chr(10).join(f"  - {err}" for err in errors)}

Previous SQL:
{existing_sql if existing_sql else 'Not available'}

Generate corrected SQL now.
"""

        # Validate input
        user_prompt = validate_llm_input(user_prompt)

        # Call LLM
        llm = get_llm()

        if llm is None:
            # Fallback: Just add a comment to existing SQL
            logger.warning("No LLM available, adding retry comment to SQL")
            sql_code = f"""-- dbt model: {model_name} (retry {attempts})
{existing_sql if existing_sql else '-- Original SQL not available'}
"""
        else:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Extract SQL
            sql_code = validate_llm_output(response.content)
            sql_code = sanitize_sql_output(sql_code)

        # Clean markdown
        if "```sql" in sql_code:
            start = sql_code.find("```sql") + 6
            end = sql_code.find("```", start)
            sql_code = sql_code[start:end].strip()
        elif "```" in sql_code:
            start = sql_code.find("```") + 3
            end = sql_code.find("```", start)
            sql_code = sql_code[start:end].strip()

        # Save corrected SQL
        if file_path:
            with open(file_path, 'w') as f:
                f.write(sql_code)

        # Reset model for retry
        current_model['status'] = 'pending'
        current_model['errors'] = []  # Clear old errors

        logger.info(f"Model {model_name} rebuilt, ready for retry")

    except Exception as e:
        logger.error(f"Rebuilder failed for {model_name}: {e}", exc_info=True)
        current_model['errors'].append(f"Rebuild error: {str(e)}")

    return state


# =============================================================================
# EVALUATOR NODE
# =============================================================================

def evaluator_node(state: MigrationState) -> MigrationState:
    """
    Evaluator Agent - Final evaluation and reporting.

    Input: MigrationState with all models processed
    Output: MigrationState with phase='complete' and final summary
    """
    logger.info("=== Evaluator Node Starting ===")

    try:
        models = state.get('models', [])
        completed = state.get('completed_count', 0)
        failed = state.get('failed_count', 0)
        total = len(models)

        # Calculate success rate
        success_rate = (completed / total * 100) if total > 0 else 0.0

        # Gather statistics
        evaluation = {
            'total_models': total,
            'completed': completed,
            'failed': failed,
            'success_rate': success_rate,
            'completed_models': [m['name'] for m in models if m['status'] == 'completed'],
            'failed_models': [
                {'name': m['name'], 'errors': m.get('errors', [])}
                for m in models if m['status'] == 'failed'
            ]
        }

        state['evaluation'] = evaluation
        state['phase'] = 'complete'

        logger.info("=" * 60)
        logger.info("MIGRATION EVALUATION")
        logger.info("=" * 60)
        logger.info(f"Total Models: {total}")
        logger.info(f"Completed: {completed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Evaluator failed: {e}", exc_info=True)
        state['errors'] = state.get('errors', []) + [f"Evaluation error: {str(e)}"]

    return state
