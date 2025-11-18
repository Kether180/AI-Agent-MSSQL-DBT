"""
Agent System for MSSQL to dbt Migration

This module defines the base agent class and the orchestrator that coordinates
the multi-agent workflow. It provides the structure for agents to perform, a multi agen system almost like a stage manager that coordinates 
the agents. Each agent is responsible for a specific part of the migration process
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import os

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Defines the different agent roles in the system, enums allow us to have a fixed set of roles"""
    ASSESSMENT = "assessment"
    PLANNER = "planner"
    EXECUTOR = "executor"
    TESTER = "tester"
    REBUILDER = "rebuilder"
    EVALUATOR = "evaluator"

# status of each model during migration, tracks the lifecycle of a model
class ModelStatus(Enum):
    """Status of a model in the migration process"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    FAILED = "failed"
    COMPLETED = "completed"
    SKIPPED = "skipped"

# shared information between agents, updated as work progresses and shared memory for the system
@dataclass
class AgentContext:
    """Context passed between agents"""
    metadata: Dict              # The MSSQL metadata we extracted
    dbt_project_path: str      # Where to create dbt files
    current_model: Optional[str] = None  # Which model we're working on
    migration_state: Optional[Dict] = None  # Progress tracker
    api_key: Optional[str] = None  # Claude API key (optional)
    

    
    def get_model_state(self, model_name: str) -> Optional[Dict]:
        """Get the state of a specific model"""
        if not self.migration_state or 'models' not in self.migration_state:
            return None
        # search for a specific model in the migration state
        for model in self.migration_state['models']:
            if model['name'] == model_name:
                return model
        return None
    
    def update_model_state(self, model_name: str, updates: Dict):
        """Update the state of a specific model"""
        if not self.migration_state:
            self.migration_state = {'models': []}
        
        if 'models' not in self.migration_state:
            self.migration_state['models'] = []
        
        # Find and update existing model state, errors or handling if model not found
        for model in self.migration_state['models']:
            if model['name'] == model_name:
                model.update(updates)
                return
        
        # Add new model state
        new_model = {'name': model_name}
        new_model.update(updates)
        self.migration_state['models'].append(new_model)


@dataclass
class AgentResult:
    """Result returned by an agent"""
    success: bool           # Did it work?
    role: AgentRole        # Which agent am I?
    data: Dict            # The results/outputs
    errors: List[str] = None  # Any errors encountered
    next_agent: Optional[AgentRole] = None  # Who should run next?
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BaseAgent(ABC):
    """
    Base class for all migration agents
    
    Each agent is responsible for a specific part of the migration process
    forces all agents to implement execute() method, provides common functionality like call_claude() 
    and ensures consistency across agents.
    """
    
    def __init__(self, role: AgentRole):
        self.role = role
        self.anthropic_client = None
    

    # Initialize the agent with context, particularly setting up the Claude API client if an API key is provided.
    # If there is no API, it will use a fallback logic.
    def initialize(self, context: AgentContext):
        """Initialize the agent with context"""
        if context.api_key:
            try:
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=context.api_key)
                logger.info(f"{self.role.value} agent initialized with Claude API")
            except Exception as e:
                logger.warning(f"Could not initialize Claude API: {e}")
    
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's task
        
        Args:
            context: AgentContext with all necessary information
            
        Returns:
            AgentResult with the outcome of the execution
        """
        pass

    # Every agent must implement this method to interact with the Claude API, can't create a baseagent directly , forces consistent interface.
    def call_claude(self, system_prompt: str, user_prompt: str, 
                   max_tokens: int = 4096) -> str:
        """
        Call Claude API with given prompts
        
        Args:
            system_prompt: System instruction for Claude
            user_prompt: User query/request
            max_tokens: Maximum tokens in response
            
        Returns:
            Claude's response text
        """
        if not self.anthropic_client:
            logger.warning("Claude API not initialized, returning mock response")
            return self._mock_response(user_prompt)
        
        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self._mock_response(user_prompt)

        # standardized way for all agents to use AI , checks if Claude is available, falls back gracefully if not , handles errors , return the AI response.

    def _mock_response(self, prompt: str) -> str:
        """Fallback mock response when API is not available"""
        return f"Mock response for {self.role.value} agent"
    
    def log_execution(self, message: str, level: str = "info"):
        """Log agent execution details"""
        log_func = getattr(logger, level)
        log_func(f"[{self.role.value.upper()}] {message}")


class MigrationOrchestrator:
    """
    Orchestrates the multi-agent workflow for migration
    
    Manages state, coordinates agents, and handles the iterative
    migration process.
    """
    
    def __init__(self, context: AgentContext):
        self.context = context
        self.agents: Dict[AgentRole, BaseAgent] = {}  # storage for agents
        self.state_file = os.path.join(context.dbt_project_path, 'migration_state.json')
        self._load_or_initialize_state()
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.role] = agent
        agent.initialize(self.context)
        logger.info(f"Registered {agent.role.value} agent")
    # state management methods to load, save, and initialize migration state from disk.
    def _load_or_initialize_state(self):
        """Load existing migration state or create new one"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.context.migration_state = json.load(f)
            logger.info(f"Loaded existing migration state from {self.state_file}")
        else:
            self.context.migration_state = {
                'phase': 'initialization',
                'models': [],
                'completed_count': 0,
                'failed_count': 0,
                'assessment_complete': False,
                'plan_complete': False
            }
            logger.info("Initialized new migration state")
    
    def save_state(self):
        """Persist migration state to disk""" # audit trail of what happened
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.context.migration_state, f, indent=2)
        logger.info(f"Saved migration state to {self.state_file}")
    
    # if migration crashes it can be resume from where it left off, track progress of each model, audit trail of what happened.
    def run_full_migration(self) -> Dict:
        """
        Execute the complete migration workflow
        
        Returns:
            Final migration report
        """
        logger.info("=" * 60)
        logger.info("Starting MSSQL to dbt Migration")
        logger.info("=" * 60)
        
        results = {
            'assessment': None,
            'planning': None,
            'models': [],
            'summary': {}
        }
        
        # Phase 1: Assessment
        if not self.context.migration_state.get('assessment_complete'):
            logger.info("\n--- Phase 1: Assessment ---")
            assessment_result = self._run_agent(AgentRole.ASSESSMENT)
            results['assessment'] = assessment_result.data

            if assessment_result.success:
                # Save assessment data to migration_state for reference
                self.context.migration_state['assessment'] = assessment_result.data
                self.context.migration_state['assessment_complete'] = True
                self.context.migration_state['phase'] = 'planning'
                self.save_state()
        else:
            # If assessment already exists, load it from migration_state
            if 'assessment' in self.context.migration_state:
                results['assessment'] = self.context.migration_state['assessment']
        
        # Phase 2: Planning
        if not self.context.migration_state.get('plan_complete'):
            logger.info("\n--- Phase 2: Planning ---")
            planning_result = self._run_agent(AgentRole.PLANNER)
            results['planning'] = planning_result.data

            if planning_result.success:
                # IMPORTANT: Save planning data to migration_state so Executor can access it
                self.context.migration_state['planning'] = planning_result.data
                self.context.migration_state['plan_complete'] = True
                self.context.migration_state['phase'] = 'execution'

                # Initialize model states from plan
                if 'models' in planning_result.data:
                    for model in planning_result.data['models']:
                        self.context.update_model_state(
                            model['name'],
                            {
                                'status': ModelStatus.PENDING.value,
                                'attempts': 0,
                                'errors': []
                            }
                        )
                self.save_state()
        else:
            # If plan already exists, load it from migration_state
            if 'planning' in self.context.migration_state:
                results['planning'] = self.context.migration_state['planning']
        
        # Phase 3: Iterative Model Migration
        logger.info("\n--- Phase 3: Model Migration ---")
        models_to_migrate = self._get_pending_models()
        
        for model_name in models_to_migrate:
            logger.info(f"\n>>> Migrating model: {model_name}")
            self.context.current_model = model_name
            
            model_result = self._migrate_single_model(model_name)
            results['models'].append(model_result)
            
            self.save_state()
        
        # Generate final summary
        results['summary'] = self._generate_summary()
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration Complete")
        logger.info("=" * 60)
        logger.info(f"Completed: {results['summary']['completed']}")
        logger.info(f"Failed: {results['summary']['failed']}")
        logger.info(f"Skipped: {results['summary']['skipped']}")
        
        return results
    # assessment, analyze the database ,creating an strategy
    # Planning, create migration plan, order models
    # Execution, For each model, migrate it (iterative loop)
    # Generate summary report at the end.
    
    def _migrate_single_model(self, model_name: str) -> Dict:
        """
        Migrate a single model through the agent workflow
        
        Returns:
            Result dictionary for the model
        """
        model_state = self.context.get_model_state(model_name)
        max_attempts = 3
        
        result = {
            'model': model_name,
            'status': ModelStatus.FAILED.value,
            'attempts': 0,
            'errors': []
        }
        
        while model_state['attempts'] < max_attempts:
            model_state['attempts'] += 1
            result['attempts'] = model_state['attempts']
            
            try:
                # Execute
                self.context.update_model_state(model_name, {
                    'status': ModelStatus.IN_PROGRESS.value
                })

                exec_result = self._run_agent(AgentRole.EXECUTOR)
                if not exec_result.success:
                    result['errors'].extend(exec_result.errors)
                    # Update state with errors for rebuilder
                    self.context.update_model_state(model_name, {
                        'errors': result['errors']
                    })

                    # Try to rebuild
                    rebuild_result = self._run_agent(AgentRole.REBUILDER)
                    if not rebuild_result.success:
                        continue

                # Test
                self.context.update_model_state(model_name, {
                    'status': ModelStatus.TESTING.value
                })

                test_result = self._run_agent(AgentRole.TESTER)
                if not test_result.success:
                    result['errors'].extend(test_result.errors)
                    # Update state with errors for rebuilder
                    self.context.update_model_state(model_name, {
                        'errors': result['errors']
                    })

                    # Try to rebuild
                    rebuild_result = self._run_agent(AgentRole.REBUILDER)
                    if not rebuild_result.success:
                        # After rebuilder fails, retry the executor
                        continue
                    # If rebuilder succeeds, retry the tester
                    test_result = self._run_agent(AgentRole.TESTER)
                    if not test_result.success:
                        result['errors'].extend(test_result.errors)
                        continue

                # Evaluate
                eval_result = self._run_agent(AgentRole.EVALUATOR)
                if not eval_result.success:
                    result['errors'].extend(eval_result.errors)
                    continue

                # Success!
                self.context.update_model_state(model_name, {
                    'status': ModelStatus.COMPLETED.value,
                    'validation_score': eval_result.data.get('validation_score', 1.0),
                    'errors': []  # Clear errors on success
                })

                result['status'] = ModelStatus.COMPLETED.value
                result['validation_score'] = eval_result.data.get('validation_score', 1.0)

                self.context.migration_state['completed_count'] += 1
                break

            except Exception as e:
                logger.error(f"Error migrating {model_name}: {e}")
                result['errors'].append(str(e))

        if result['status'] != ModelStatus.COMPLETED.value:
            self.context.update_model_state(model_name, {
                'status': ModelStatus.FAILED.value,
                'errors': result['errors']
            })
            self.context.migration_state['failed_count'] += 1
        
        return result

        # The model migration flow is as follows:
        # Try up to 3 times:
        #  1. Executor generates model
        #      (if fails)
        #  2. Rebuilder tries to fix
        #      (if succeeds)
        #  3. Tester validates
        #      (if fails)
        #  4. Rebuilder tries to fix
        #      (if succeeds)
        #  5. Evaluator compares outputs
        #     (if succeeds)
        #  Mark as COMPLETED
        
    def _run_agent(self, role: AgentRole) -> AgentResult:
        """Execute a specific agent"""
        if role not in self.agents:
            logger.error(f"Agent {role.value} not registered")
            return AgentResult(
                success=False,
                role=role,
                data={},
                errors=[f"Agent {role.value} not found"]
            )
        
        agent = self.agents[role]
        logger.info(f"Executing {role.value} agent...")
        
        try:
            result = agent.execute(self.context)
            logger.info(f"{role.value} agent completed: {'SUCCESS' if result.success else 'FAILED'}")
            return result
        except Exception as e:
            logger.error(f"Error executing {role.value} agent: {e}")
            return AgentResult(
                success=False,
                role=role,
                data={},
                errors=[str(e)]
            )
    
    def _get_pending_models(self) -> List[str]:
        """Get list of models that need migration"""
        models = []
        
        if 'models' in self.context.migration_state:
            for model in self.context.migration_state['models']:
                status = model.get('status')
                if status == ModelStatus.PENDING.value or status == ModelStatus.FAILED.value:
                    models.append(model['name'])
        
        return models
    
    def _generate_summary(self) -> Dict:
        """Generate migration summary statistics"""
        summary = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0,
            'pending': 0
        }
        
        if 'models' in self.context.migration_state:
            summary['total'] = len(self.context.migration_state['models'])
            
            for model in self.context.migration_state['models']:
                status = model.get('status')
                if status == ModelStatus.COMPLETED.value:
                    summary['completed'] += 1
                elif status == ModelStatus.FAILED.value:
                    summary['failed'] += 1
                elif status == ModelStatus.SKIPPED.value:
                    summary['skipped'] += 1
                elif status == ModelStatus.PENDING.value:
                    summary['pending'] += 1
        
        return summary