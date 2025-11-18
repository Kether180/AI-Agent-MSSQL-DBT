class ExecutorAgent(BaseAgent):
    """Generates dbt models from MSSQL metadata"""
    
    def execute(self, context: AgentContext):
        # Get migration plan for this model
        model_plan = self._get_model_plan(model_name, context)
        
        # Get MSSQL source object details
        source_object = self._get_source_object(
            model_plan['source_object'], context
        )
        
        # Generate dbt model SQL
        model_sql = self._generate_model_sql(
            model_plan, source_object, context
        )
        
        # Generate YAML documentation
        schema_yml = self._generate_schema_yml(
            model_plan, source_object
        )
        
        # Write to dbt project
        files_created = self._write_dbt_files(
            model_name, model_sql, schema_yml,
            context.dbt_project_path
        )
        
        return AgentResult(
            success=True,
            files=files_created,
            next_agent=AgentRole.TESTER
        )
