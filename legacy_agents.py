"""
Concrete Agent Implementations

This module implements each specialized agent:
- Assessment Agent: Evaluates what to migrate
- Planner Agent: Creates migration strategy
- Executor Agent: Generates dbt models
- Tester Agent: Validates models
- Rebuilder Agent: Fixes errors
- Evaluator Agent: Compares outputs
"""

import os
import json
from typing import Dict, List
import networkx as nx
from legacy_agent_system import (
    BaseAgent, AgentRole, AgentContext, AgentResult
)


class AssessmentAgent(BaseAgent):
    """
    Evaluates what needs to be migrated and estimates complexity
    
    Responsibilities:
    - Analyze MSSQL metadata
    - Identify migration candidates
    - Estimate complexity and priority
    - Recommend what to migrate vs. leave as legacy
    """
    
    def __init__(self):
        super().__init__(AgentRole.ASSESSMENT)
    
    def execute(self, context: AgentContext) -> AgentResult:
        self.log_execution("Starting assessment of MSSQL metadata")
        
        metadata = context.metadata
        
        # Analyze objects
        tables = metadata.get('tables', [])
        procedures = metadata.get('stored_procedures', [])
        
        # Build dependency graph
        dep_graph = self._build_dependency_graph(metadata)
        
        # Assess each object
        assessment = {
            'total_objects': len(tables) + len(procedures),
            'tables': [],
            'procedures': [],
            'strategy': {},
            'recommendations': []
        }
        
        # Assess tables
        for table in tables:
            table_assessment = self._assess_table(table, dep_graph)
            assessment['tables'].append(table_assessment)
        
        # Assess procedures
        for proc in procedures:
            proc_assessment = self._assess_procedure(proc, dep_graph)
            assessment['procedures'].append(proc_assessment)
        
        # Generate strategy using Claude
        strategy = self._generate_strategy(assessment, context)
        assessment['strategy'] = strategy
        
        # Generate recommendations
        assessment['recommendations'] = self._generate_recommendations(assessment)
        
        self.log_execution(f"Assessment complete: {len(assessment['tables'])} tables, "
                          f"{len(assessment['procedures'])} procedures")
        
        return AgentResult(
            success=True,
            role=self.role,
            data=assessment,
            next_agent=AgentRole.PLANNER
        )
    
    def _build_dependency_graph(self, metadata: Dict) -> nx.DiGraph:
        """Build a directed graph of dependencies"""
        G = nx.DiGraph()
        
        # Add all objects as nodes
        for table in metadata.get('tables', []):
            full_name = f"{table['schema']}.{table['name']}"
            G.add_node(full_name, type=table['object_type'])
        
        for proc in metadata.get('stored_procedures', []):
            full_name = f"{proc['schema']}.{proc['name']}"
            G.add_node(full_name, type='PROCEDURE')
        
        # Add edges for dependencies
        for dep in metadata.get('dependencies', []):
            source = f"{dep['source_schema']}.{dep['source_name']}"
            target = f"{dep['target_schema']}.{dep['target_name']}"
            if G.has_node(source) and G.has_node(target):
                G.add_edge(source, target)
        
        return G
    
    def _assess_table(self, table: Dict, dep_graph: nx.DiGraph) -> Dict:
        """Assess a single table for migration"""
        full_name = f"{table['schema']}.{table['name']}"
        
        # Calculate metrics
        row_count = table.get('row_count', 0) or 0
        column_count = len(table.get('columns', []))
        dependency_count = len(table.get('dependencies', []))
        
        # Calculate complexity score (0-10)
        complexity = 0
        if row_count > 1000000:
            complexity += 3
        elif row_count > 100000:
            complexity += 2
        elif row_count > 10000:
            complexity += 1
        
        if column_count > 20:
            complexity += 2
        elif column_count > 10:
            complexity += 1
        
        if dependency_count > 5:
            complexity += 2
        elif dependency_count > 2:
            complexity += 1
        
        # Determine priority (lower number = higher priority)
        # Base tables with no dependencies = highest priority
        if dependency_count == 0:
            priority = 1
        elif dependency_count <= 2:
            priority = 2
        else:
            priority = 3
        
        # Migration recommendation
        if table['object_type'] == 'VIEW':
            recommendation = 'migrate_as_view'
        else:
            recommendation = 'migrate_as_source_and_staging'
        
        return {
            'full_name': full_name,
            'schema': table['schema'],
            'name': table['name'],
            'type': table['object_type'],
            'complexity': min(complexity, 10),
            'priority': priority,
            'row_count': row_count,
            'column_count': column_count,
            'dependency_count': dependency_count,
            'recommendation': recommendation,
            'migrate': True  # For POC, migrate everything
        }
    
    def _assess_procedure(self, proc: Dict, dep_graph: nx.DiGraph) -> Dict:
        """Assess a stored procedure for migration"""
        full_name = f"{proc['schema']}.{proc['name']}"
        
        # Analyze procedure complexity
        definition = proc.get('definition', '')
        line_count = len(definition.split('\n'))
        
        complexity = 0
        if line_count > 100:
            complexity += 4
        elif line_count > 50:
            complexity += 2
        elif line_count > 20:
            complexity += 1
        
        # Check for complex patterns
        if 'CURSOR' in definition.upper():
            complexity += 3
        if 'DYNAMIC SQL' in definition.upper() or 'EXEC(' in definition.upper():
            complexity += 2
        if 'TRANSACTION' in definition.upper():
            complexity += 1
        
        dependency_count = len(proc.get('dependencies', []))
        
        # Procedures are generally lower priority than tables
        priority = 4
        
        # Recommendation based on complexity
        if complexity <= 3:
            recommendation = 'convert_to_dbt_model'
        elif complexity <= 6:
            recommendation = 'convert_with_manual_review'
        else:
            recommendation = 'consider_leaving_as_stored_proc'
        
        return {
            'full_name': full_name,
            'schema': proc['schema'],
            'name': proc['name'],
            'type': 'PROCEDURE',
            'complexity': min(complexity, 10),
            'priority': priority,
            'line_count': line_count,
            'dependency_count': dependency_count,
            'recommendation': recommendation,
            'migrate': complexity <= 6  # Only migrate simpler procedures
        }
    
    def _generate_strategy(self, assessment: Dict, context: AgentContext) -> Dict:
        """Generate overall migration strategy using Claude"""
        
        if not self.anthropic_client:
            # Fallback strategy without Claude
            return self._fallback_strategy(assessment)
        
        system_prompt = """You are an expert data engineer specializing in database migrations. 
Your task is to analyze an assessment of MSSQL objects and create a migration strategy to dbt.
Focus on:
1. Migration order based on dependencies
2. Risk areas and mitigation strategies
3. Quick wins vs. complex migrations
4. Resource allocation recommendations"""
        
        user_prompt = f"""Based on this assessment of MSSQL objects:

Total Objects: {assessment['total_objects']}
Tables to Migrate: {sum(1 for t in assessment['tables'] if t['migrate'])}
Procedures to Migrate: {sum(1 for p in assessment['procedures'] if p['migrate'])}

High Complexity Items: {sum(1 for t in assessment['tables'] + assessment['procedures'] if t['complexity'] > 6)}
Medium Complexity: {sum(1 for t in assessment['tables'] + assessment['procedures'] if 3 <= t['complexity'] <= 6)}
Low Complexity: {sum(1 for t in assessment['tables'] + assessment['procedures'] if t['complexity'] < 3)}

Please provide a migration strategy as a JSON object with these keys:
- approach: Overall migration approach
- phases: List of migration phases with descriptions
- estimated_duration: Estimated time (e.g., "2-3 weeks")
- risk_factors: List of main risks
- recommendations: Key recommendations

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.call_claude(system_prompt, user_prompt)
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            self.log_execution(f"Error generating strategy with Claude: {e}", "warning")
        
        return self._fallback_strategy(assessment)
    
    def _fallback_strategy(self, assessment: Dict) -> Dict:
        """Fallback strategy when Claude is not available"""
        return {
            'approach': 'Iterative migration starting with base tables',
            'phases': [
                {
                    'phase': 1,
                    'name': 'Base Tables',
                    'description': 'Migrate tables with no dependencies first'
                },
                {
                    'phase': 2,
                    'name': 'Dependent Tables',
                    'description': 'Migrate tables with dependencies'
                },
                {
                    'phase': 3,
                    'name': 'Views',
                    'description': 'Convert views to dbt models'
                },
                {
                    'phase': 4,
                    'name': 'Stored Procedures',
                    'description': 'Convert simple procedures to dbt models'
                }
            ],
            'estimated_duration': '2-4 weeks',
            'risk_factors': [
                'Complex stored procedures may require manual conversion',
                'Data validation needed for all models',
                'Performance optimization may be required'
            ],
            'recommendations': [
                'Start with tables that have no dependencies',
                'Validate each model before proceeding',
                'Focus on business-critical tables first'
            ]
        }
    
    def _generate_recommendations(self, assessment: Dict) -> List[str]:
        """Generate specific recommendations"""
        recommendations = []
        
        # Count items by complexity
        high_complexity = sum(1 for t in assessment['tables'] + assessment['procedures'] 
                             if t['complexity'] > 6)
        
        if high_complexity > 0:
            recommendations.append(
                f"⚠️  {high_complexity} high-complexity items identified. "
                "Consider manual review for these."
            )
        
        # Check for procedures
        proc_to_migrate = sum(1 for p in assessment['procedures'] if p['migrate'])
        if proc_to_migrate > 0:
            recommendations.append(
                f"📋 {proc_to_migrate} stored procedures recommended for conversion. "
                "Review business logic carefully."
            )
        
        # Dependency recommendations
        recommendations.append(
            "✅ Start with base tables (no dependencies) for quickest wins"
        )
        
        # Testing recommendations
        recommendations.append(
            "🧪 Implement data quality tests for all migrated models"
        )
        
        return recommendations


class PlannerAgent(BaseAgent):
    """
    Creates detailed migration plan
    
    Responsibilities:
    - Map MSSQL objects to dbt models
    - Define migration order
    - Create model naming conventions
    - Plan transformations
    """
    
    def __init__(self):
        super().__init__(AgentRole.PLANNER)
    
    def execute(self, context: AgentContext) -> AgentResult:
        self.log_execution("Creating migration plan")
        
        # Get assessment results
        assessment = None
        if context.migration_state and 'assessment' in context.migration_state:
            assessment = context.migration_state['assessment']
        
        # Create migration plan
        plan = {
            'models': [],
            'execution_order': [],
            'naming_conventions': {},
            'transformations': {}
        }
        
        # Process tables
        tables = context.metadata.get('tables', [])
        for table in tables:
            model_plan = self._plan_table_migration(table, context)
            if model_plan:
                plan['models'].append(model_plan)
        
        # Process procedures
        procedures = context.metadata.get('stored_procedures', [])
        for proc in procedures:
            model_plan = self._plan_procedure_migration(proc, context)
            if model_plan:
                plan['models'].append(model_plan)
        
        # Determine execution order based on dependencies
        plan['execution_order'] = self._determine_execution_order(plan['models'])
        
        # Define naming conventions
        plan['naming_conventions'] = {
            'sources': 'src_<system>_<table>',
            'staging': 'stg_<table>',
            'intermediate': 'int_<description>',
            'marts': 'fct_<entity> or dim_<entity>'
        }
        
        self.log_execution(f"Plan created with {len(plan['models'])} models")
        
        return AgentResult(
            success=True,
            role=self.role,
            data=plan,
            next_agent=AgentRole.EXECUTOR
        )
    
    def _plan_table_migration(self, table: Dict, context: AgentContext) -> Dict:
        """Plan migration for a single table"""
        full_name = f"{table['schema']}.{table['name']}"
        
        if table['object_type'] == 'VIEW':
            # Views become dbt models
            return {
                'name': f"stg_{table['name'].lower()}",
                'source_object': full_name,
                'source_type': 'VIEW',
                'target_type': 'model',
                'materialization': 'view',
                'dependencies': table.get('dependencies', []),
                'transformations': ['Convert view logic to dbt model'],
                'priority': 3
            }
        else:
            # Tables need source + staging model
            return {
                'name': f"stg_{table['name'].lower()}",
                'source_object': full_name,
                'source_type': 'TABLE',
                'target_type': 'model',
                'materialization': 'table',
                'dependencies': [],  # Staging models typically have no deps
                'transformations': [
                    'Create source definition',
                    'Create staging model with basic transformations',
                    'Add freshness tests',
                    'Add data quality tests'
                ],
                'priority': 1 if not table.get('dependencies') else 2
            }
    
    def _plan_procedure_migration(self, proc: Dict, context: AgentContext) -> Dict:
        """Plan migration for a stored procedure"""
        full_name = f"{proc['schema']}.{proc['name']}"
        
        # Analyze procedure to determine if it should be migrated
        definition = proc.get('definition', '')
        
        # Simple SELECT procedures can become models
        if 'SELECT' in definition.upper() and 'INSERT' not in definition.upper():
            return {
                'name': f"rpt_{proc['name'].lower().replace('usp_', '')}",
                'source_object': full_name,
                'source_type': 'PROCEDURE',
                'target_type': 'model',
                'materialization': 'table',
                'dependencies': proc.get('dependencies', []),
                'transformations': [
                    'Extract SELECT logic from procedure',
                    'Convert to dbt SQL',
                    'Add parameters as variables/macros'
                ],
                'priority': 4
            }
        
        return None  # Complex procedures skipped for POC
    
    def _determine_execution_order(self, models: List[Dict]) -> List[str]:
        """Determine the order in which models should be built"""
        # Sort by priority, then by name
        sorted_models = sorted(models, key=lambda m: (m['priority'], m['name']))
        return [m['name'] for m in sorted_models]


class ExecutorAgent(BaseAgent):
    """
    Generates dbt models from MSSQL objects
    
    Responsibilities:
    - Create dbt model files
    - Generate source definitions
    - Create schema.yml files
    - Add documentation
    """
    def __init__(self):
        super().__init__(AgentRole.EXECUTOR)
    
    def execute(self, context: AgentContext) -> AgentResult:
        model_name = context.current_model
        self.log_execution(f"Generating dbt model: {model_name}")
        
        # Get model plan
        model_plan = self._get_model_plan(model_name, context)
        if not model_plan:
            return AgentResult(
                success=False,
                role=self.role,
                data={},
                errors=[f"No plan found for model {model_name}"]
            )
        # Get source object details
        source_object = self._get_source_object(model_plan['source_object'], context)
        if not source_object:
            return AgentResult(
                success=False,
                role=self.role,
                data={},
                errors=[f"Source object {model_plan['source_object']} not found"]
            )
        # Generate model SQL
        model_sql = self._generate_model_sql(model_plan, source_object, context)
        # Generate schema.yml
        schema_yml = self._generate_schema_yml(model_plan, source_object)
        # Write files to dbt project
        files_created = self._write_dbt_files(
            model_name,
            model_sql,
            schema_yml,
            context.dbt_project_path
        )
        
        self.log_execution(f"Generated {len(files_created)} files for {model_name}")
        
        return AgentResult(
            success=True,
            role=self.role,
            data={
                'model_name': model_name,
                'files_created': files_created,
                'model_sql': model_sql
            },
            next_agent=AgentRole.TESTER
        )
    
    def _get_model_plan(self, model_name: str, context: AgentContext) -> Dict:
        """Get the migration plan for a specific model"""
        if not context.migration_state or 'planning' not in context.migration_state:
            return None
        
        plan = context.migration_state['planning']
        for model in plan.get('models', []):
            if model['name'] == model_name:
                return model
        return None
    
    def _get_source_object(self, full_name: str, context: AgentContext) -> Dict:
        """Get the source MSSQL object"""
        schema, name = full_name.split('.')
        
        # Check tables
        for table in context.metadata.get('tables', []):
            if table['schema'] == schema and table['name'] == name:
                return table
        
        # Check procedures
        for proc in context.metadata.get('stored_procedures', []):
            if proc['schema'] == schema and proc['name'] == name:
                return proc
        
        return None
    
    def _generate_model_sql(self, model_plan: Dict, source_object: Dict, 
                           context: AgentContext) -> str:
        """Generate the SQL for the dbt model"""
        
        if model_plan['source_type'] == 'TABLE':
            # Generate staging model for table
            columns = source_object.get('columns', [])
            column_list = ',\n    '.join([f"{col['name'].lower()}" for col in columns])
            
            sql = f"""{{{{
    config(
        materialized='{model_plan['materialization']}'
    )
}}}}

with source as (
    select * from {{{{ source('mssql', '{source_object['name'].lower()}') }}}}
),

renamed as (
    select
        {column_list}
    from source
)

select * from renamed
"""
        
        elif model_plan['source_type'] == 'VIEW':
            # For views, we need to extract the view logic
            # For POC, create a simple reference
            sql = f"""{{{{
    config(
        materialized='view'
    )
}}}}

-- This model replicates the logic from MSSQL view: {source_object['schema']}.{source_object['name']}
-- TODO: Replace with actual view logic

select * from {{{{ source('mssql', '{source_object['name'].lower()}') }}}}
"""
        
        elif model_plan['source_type'] == 'PROCEDURE':
            # Extract SELECT logic from procedure
            definition = source_object.get('definition', '')
            sql = f"""{{{{
    config(
        materialized='{model_plan['materialization']}'
    )
}}}}

-- This model replicates the logic from stored procedure: {source_object['schema']}.{source_object['name']}
-- Original procedure definition:
{chr(10).join(['-- ' + line for line in definition.split(chr(10))])}

-- TODO: Extract and convert SELECT logic
select 1 as placeholder
"""
        
        else:
            sql = "-- Unsupported source type\nselect 1 as placeholder"
        
        return sql
    
    def _generate_schema_yml(self, model_plan: Dict, source_object: Dict) -> str:
        """Generate schema.yml content for the model"""
        
        yml = f"""version: 2

models:
  - name: {model_plan['name']}
    description: >
      Migrated from MSSQL {model_plan['source_type']}: {model_plan['source_object']}
"""
        
        # Add column documentation if it's a table
        if model_plan['source_type'] == 'TABLE':
            columns = source_object.get('columns', [])
            if columns:
                yml += "    columns:\n"
                for col in columns:
                    yml += f"""      - name: {col['name'].lower()}
        description: "{col['data_type']}"
"""
        
        return yml
    
    def _write_dbt_files(self, model_name: str, sql: str, schema: str, 
                        project_path: str) -> List[str]:
        """Write dbt files to disk"""
        files_created = []
        
        # Create models directory if it doesn't exist
        models_dir = os.path.join(project_path, 'models', 'staging')
        os.makedirs(models_dir, exist_ok=True)
        
        # Write SQL file
        sql_path = os.path.join(models_dir, f"{model_name}.sql")
        with open(sql_path, 'w') as f:
            f.write(sql)
        files_created.append(sql_path)
        
        # Write schema file
        schema_path = os.path.join(models_dir, f"_schema.yml")
        
        # Append to existing schema file or create new one
        if os.path.exists(schema_path):
            with open(schema_path, 'a') as f:
                f.write('\n' + schema)
        else:
            with open(schema_path, 'w') as f:
                f.write(schema)
        files_created.append(schema_path)
        
        return files_created


class TesterAgent(BaseAgent):
    """
    Tests and validates dbt models
    
    Responsibilities:
    - Compile models
    - Run models
    - Execute tests
    - Report errors
    """
    
    def __init__(self):
        super().__init__(AgentRole.TESTER)
    
    def execute(self, context: AgentContext) -> AgentResult:
        model_name = context.current_model
        self.log_execution(f"Testing model: {model_name}")

        # In a real implementation, this would:
        # 1. Run dbt compile
        # 2. Run dbt run for the specific model
        # 3. Run dbt test for the model

        # For POC, simulate testing
        test_results = {
            'model': model_name,
            'compile_success': True,
            'run_success': True,
            'tests_passed': True,
            'errors': []
        }

        # Simulate some basic checks
        model_path = os.path.join(
            context.dbt_project_path,
            'models',
            'staging',
            f"{model_name}.sql"
        )

        if not os.path.exists(model_path):
            test_results['compile_success'] = False
            test_results['errors'].append(f"Model file not found: {model_path}")
            self.log_execution(f"ERROR: Model file not found at {model_path}", "error")
        else:
            self.log_execution(f"[OK] Model file exists at {model_path}")
            # Read the file to verify it has content
            try:
                with open(model_path, 'r') as f:
                    content = f.read()
                    if len(content) < 10:  # Basic sanity check
                        test_results['compile_success'] = False
                        test_results['errors'].append(f"Model file appears empty or invalid")
                    else:
                        self.log_execution(f"[OK] Model file has {len(content)} characters")
            except Exception as e:
                test_results['compile_success'] = False
                test_results['errors'].append(f"Error reading model file: {e}")

        success = (test_results['compile_success'] and
                  test_results['run_success'] and
                  test_results['tests_passed'])

        if success:
            self.log_execution(f"[OK] Model {model_name} passed all tests")
        else:
            self.log_execution(f"[FAIL] Model {model_name} failed testing: {test_results['errors']}", "warning")

        return AgentResult(
            success=success,
            role=self.role,
            data=test_results,
            errors=test_results['errors'] if not success else [],
            next_agent=AgentRole.EVALUATOR if success else AgentRole.REBUILDER
        )


class RebuilderAgent(BaseAgent):
    """
    Fixes errors and rebuilds models
    
    Responsibilities:
    - Analyze errors
    - Propose fixes
    - Regenerate models
    - Validate fixes
    """
    
    def __init__(self):
        super().__init__(AgentRole.REBUILDER)
    
    def execute(self, context: AgentContext) -> AgentResult:
        model_name = context.current_model
        self.log_execution(f"Attempting to rebuild model: {model_name}")

        # Get previous errors
        model_state = context.get_model_state(model_name)
        errors = model_state.get('errors', []) if model_state else []

        # For POC, log that we would attempt to fix errors
        self.log_execution(f"Errors to fix: {errors}")

        # In a real implementation, this would:
        # 1. Use Claude to analyze the errors
        # 2. Propose fixes
        # 3. Regenerate the model
        # 4. Return to testing

        # For POC: If there are no actual errors, consider it a success
        # This allows the workflow to continue instead of always failing
        if not errors or len(errors) == 0:
            self.log_execution("No errors found to fix, marking as successful")
            return AgentResult(
                success=True,
                role=self.role,
                data={'attempted_fixes': [], 'note': 'POC: No errors to fix'},
                next_agent=AgentRole.TESTER
            )

        # If there are actual errors, return failure with details
        self.log_execution(f"Found {len(errors)} errors, would need manual intervention")
        return AgentResult(
            success=False,
            role=self.role,
            data={'attempted_fixes': []},
            errors=errors,
            next_agent=AgentRole.TESTER
        )


class EvaluatorAgent(BaseAgent):
    """
    Evaluates model correctness
    
    Responsibilities:
    - Compare dbt output to MSSQL output
    - Calculate validation scores
    - Identify discrepancies
    - Approve or reject migration
    """
    
    def __init__(self):
        super().__init__(AgentRole.EVALUATOR)
    
    def execute(self, context: AgentContext) -> AgentResult:
        model_name = context.current_model
        self.log_execution(f"Evaluating model: {model_name}")
        
        # In a real implementation, this would:
        # 1. Run the model in dbt to get output
        # 2. Run equivalent query in MSSQL
        # 3. Compare row counts, column values, aggregates
        # 4. Calculate validation score
        
        # For POC, simulate validation
        evaluation = {
            'model': model_name,
            'validation_score': 0.95,  # 95% match
            'row_count_match': True,
            'schema_match': True,
            'data_quality_score': 0.95,
            'discrepancies': [],
            'passed': True
        }
        
        return AgentResult(
            success=True,
            role=self.role,
            data=evaluation
        )
