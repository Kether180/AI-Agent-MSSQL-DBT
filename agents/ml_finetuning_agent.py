"""
ML Fine-Tuning Agent - Machine Learning Model Training and Optimization

This agent provides model fine-tuning, training data preparation, hyperparameter
optimization, model evaluation, and deployment management for ML-powered migrations.
Part of the DataMigrate AI Eight-Agent Architecture.

Author: DataMigrate AI Team
Version: 1.0.0
"""

import os
import json
import logging
import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import statistics
import random

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of ML models for fine-tuning"""
    SCHEMA_MAPPER = "schema_mapper"
    SQL_TRANSLATOR = "sql_translator"
    DATA_CLASSIFIER = "data_classifier"
    ANOMALY_DETECTOR = "anomaly_detector"
    QUALITY_PREDICTOR = "quality_predictor"
    TRANSFORMATION_SUGGESTER = "transformation_suggester"
    ERROR_PREDICTOR = "error_predictor"


class TrainingStatus(str, Enum):
    """Status of training jobs"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationStrategy(str, Enum):
    """Hyperparameter optimization strategies"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    EVOLUTIONARY = "evolutionary"
    MANUAL = "manual"


class EvaluationMetric(str, Enum):
    """Model evaluation metrics"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC_ROC = "auc_roc"
    MSE = "mse"
    MAE = "mae"
    BLEU = "bleu"  # For translation tasks
    EXACT_MATCH = "exact_match"


@dataclass
class TrainingExample:
    """A single training example"""
    example_id: str
    input_data: Dict[str, Any]
    expected_output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    source: str = "manual"


@dataclass
class TrainingDataset:
    """A training dataset"""
    dataset_id: str
    name: str
    model_type: ModelType
    examples: List[TrainingExample] = field(default_factory=list)
    train_split: float = 0.8
    validation_split: float = 0.1
    test_split: float = 0.1
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"


@dataclass
class Hyperparameters:
    """Model hyperparameters"""
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    dropout_rate: float = 0.1
    hidden_layers: List[int] = field(default_factory=lambda: [256, 128])
    activation: str = "relu"
    optimizer: str = "adam"
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingJob:
    """A training job"""
    job_id: str
    model_type: ModelType
    dataset_id: str
    hyperparameters: Hyperparameters
    status: TrainingStatus = TrainingStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class ModelVersion:
    """A trained model version"""
    version_id: str
    model_type: ModelType
    training_job_id: str
    metrics: Dict[str, float]
    hyperparameters: Hyperparameters
    created_at: datetime = field(default_factory=datetime.now)
    is_deployed: bool = False
    deployment_url: Optional[str] = None


@dataclass
class EvaluationResult:
    """Results from model evaluation"""
    model_version_id: str
    dataset_id: str
    metrics: Dict[str, float]
    confusion_matrix: Optional[List[List[int]]] = None
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=datetime.now)


class MLFineTuningAgent:
    """
    ML Fine-Tuning Agent for model training and optimization.

    Capabilities:
    - Training Data Preparation
    - Model Fine-Tuning
    - Hyperparameter Optimization
    - Model Evaluation
    - A/B Testing
    - Model Versioning
    - Deployment Management
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the ML Fine-Tuning Agent"""
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            max_tokens=4096
        )

        # Storage for datasets, jobs, and models
        self.datasets: Dict[str, TrainingDataset] = {}
        self.jobs: Dict[str, TrainingJob] = {}
        self.models: Dict[str, ModelVersion] = {}

        # Model type configurations
        self.model_configs = self._initialize_model_configs()

        # Initialize the LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("ML Fine-Tuning Agent initialized successfully")

    def _initialize_model_configs(self) -> Dict[str, Dict]:
        """Initialize configurations for each model type"""
        return {
            ModelType.SCHEMA_MAPPER.value: {
                "description": "Maps source schemas to target schemas",
                "input_format": {"source_column": str, "source_type": str, "context": str},
                "output_format": {"target_column": str, "target_type": str, "transformation": str},
                "metrics": [EvaluationMetric.ACCURACY, EvaluationMetric.F1_SCORE],
                "default_hyperparameters": Hyperparameters(epochs=20, learning_rate=0.0001)
            },
            ModelType.SQL_TRANSLATOR.value: {
                "description": "Translates SQL between dialects",
                "input_format": {"source_sql": str, "source_dialect": str, "target_dialect": str},
                "output_format": {"translated_sql": str},
                "metrics": [EvaluationMetric.BLEU, EvaluationMetric.EXACT_MATCH],
                "default_hyperparameters": Hyperparameters(epochs=50, learning_rate=0.00005)
            },
            ModelType.DATA_CLASSIFIER.value: {
                "description": "Classifies data types and patterns",
                "input_format": {"sample_values": list, "column_name": str},
                "output_format": {"data_type": str, "pattern": str, "confidence": float},
                "metrics": [EvaluationMetric.ACCURACY, EvaluationMetric.PRECISION, EvaluationMetric.RECALL],
                "default_hyperparameters": Hyperparameters(epochs=15, batch_size=64)
            },
            ModelType.ANOMALY_DETECTOR.value: {
                "description": "Detects anomalies in data",
                "input_format": {"values": list, "context": dict},
                "output_format": {"is_anomaly": bool, "score": float, "explanation": str},
                "metrics": [EvaluationMetric.AUC_ROC, EvaluationMetric.PRECISION, EvaluationMetric.RECALL],
                "default_hyperparameters": Hyperparameters(epochs=30, dropout_rate=0.2)
            },
            ModelType.QUALITY_PREDICTOR.value: {
                "description": "Predicts data quality scores",
                "input_format": {"column_profile": dict, "sample_data": list},
                "output_format": {"quality_score": float, "issues": list},
                "metrics": [EvaluationMetric.MSE, EvaluationMetric.MAE],
                "default_hyperparameters": Hyperparameters(epochs=25, hidden_layers=[512, 256, 128])
            },
            ModelType.TRANSFORMATION_SUGGESTER.value: {
                "description": "Suggests data transformations",
                "input_format": {"source_data": dict, "target_schema": dict},
                "output_format": {"transformations": list, "sql_code": str},
                "metrics": [EvaluationMetric.ACCURACY, EvaluationMetric.BLEU],
                "default_hyperparameters": Hyperparameters(epochs=40, learning_rate=0.0001)
            },
            ModelType.ERROR_PREDICTOR.value: {
                "description": "Predicts migration errors",
                "input_format": {"migration_config": dict, "source_stats": dict},
                "output_format": {"error_probability": float, "potential_errors": list},
                "metrics": [EvaluationMetric.AUC_ROC, EvaluationMetric.F1_SCORE],
                "default_hyperparameters": Hyperparameters(epochs=20, dropout_rate=0.3)
            }
        }

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for ML operations"""
        workflow = StateGraph(dict)

        # Add nodes
        workflow.add_node("prepare_data", self._prepare_data_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("train_model", self._train_model_node)
        workflow.add_node("optimize_hyperparams", self._optimize_hyperparams_node)
        workflow.add_node("evaluate_model", self._evaluate_model_node)
        workflow.add_node("deploy_model", self._deploy_model_node)

        # Set entry point
        workflow.set_entry_point("prepare_data")

        # Add edges
        workflow.add_edge("prepare_data", "validate_data")

        # Conditional edges based on operation
        workflow.add_conditional_edges(
            "validate_data",
            self._route_after_validation,
            {
                "train": "train_model",
                "optimize": "optimize_hyperparams",
                "evaluate": "evaluate_model",
                "end": END
            }
        )

        workflow.add_edge("train_model", "evaluate_model")
        workflow.add_edge("optimize_hyperparams", "train_model")

        workflow.add_conditional_edges(
            "evaluate_model",
            self._should_deploy,
            {
                "deploy": "deploy_model",
                "end": END
            }
        )

        workflow.add_edge("deploy_model", END)

        return workflow.compile()

    def _route_after_validation(self, state: dict) -> str:
        """Route after data validation"""
        operation = state.get("operation", "train")

        if state.get("validation_errors"):
            return "end"

        if operation == "optimize":
            return "optimize"
        elif operation == "evaluate":
            return "evaluate"
        else:
            return "train"

    def _should_deploy(self, state: dict) -> str:
        """Determine if model should be deployed"""
        auto_deploy = state.get("auto_deploy", False)
        metrics = state.get("evaluation_metrics", {})
        threshold = state.get("deployment_threshold", 0.8)

        if auto_deploy:
            # Check if primary metric meets threshold
            primary_metric = state.get("primary_metric", "accuracy")
            if metrics.get(primary_metric, 0) >= threshold:
                return "deploy"

        return "end"

    async def _prepare_data_node(self, state: dict) -> dict:
        """Prepare training data"""
        examples = state.get("examples", [])
        model_type = state.get("model_type", ModelType.SCHEMA_MAPPER.value)

        if not examples:
            state["prepared_data"] = None
            return state

        # Validate and format examples
        formatted_examples = []
        for i, ex in enumerate(examples):
            example = TrainingExample(
                example_id=f"ex_{hashlib.md5(str(ex).encode()).hexdigest()[:8]}",
                input_data=ex.get("input", {}),
                expected_output=ex.get("output"),
                metadata=ex.get("metadata", {}),
                weight=ex.get("weight", 1.0)
            )
            formatted_examples.append(example)

        # Create dataset
        dataset_id = f"ds_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dataset = TrainingDataset(
            dataset_id=dataset_id,
            name=state.get("dataset_name", "Training Dataset"),
            model_type=ModelType(model_type),
            examples=formatted_examples
        )

        self.datasets[dataset_id] = dataset

        # Split data
        random.shuffle(formatted_examples)
        n = len(formatted_examples)
        train_end = int(n * dataset.train_split)
        val_end = train_end + int(n * dataset.validation_split)

        state["prepared_data"] = {
            "dataset_id": dataset_id,
            "total_examples": n,
            "train_examples": train_end,
            "validation_examples": val_end - train_end,
            "test_examples": n - val_end
        }

        return state

    async def _validate_data_node(self, state: dict) -> dict:
        """Validate training data quality"""
        prepared_data = state.get("prepared_data")
        model_type = state.get("model_type", ModelType.SCHEMA_MAPPER.value)

        if not prepared_data:
            state["validation_errors"] = ["No data prepared"]
            return state

        errors = []
        warnings = []

        dataset = self.datasets.get(prepared_data["dataset_id"])
        if not dataset:
            errors.append("Dataset not found")
            state["validation_errors"] = errors
            return state

        # Check minimum examples
        if len(dataset.examples) < 10:
            errors.append(f"Insufficient training examples: {len(dataset.examples)} (minimum 10)")

        # Check data format
        model_config = self.model_configs.get(model_type, {})
        expected_input = model_config.get("input_format", {})

        for example in dataset.examples[:5]:  # Check first 5
            for key in expected_input.keys():
                if key not in example.input_data:
                    warnings.append(f"Example missing expected input field: {key}")

        # Check class balance for classifiers
        if model_type in [ModelType.DATA_CLASSIFIER.value, ModelType.ANOMALY_DETECTOR.value]:
            outputs = [str(ex.expected_output) for ex in dataset.examples]
            unique_outputs = set(outputs)
            if len(unique_outputs) < 2:
                errors.append("Classification requires at least 2 classes")

            # Check for severe imbalance
            class_counts = {o: outputs.count(o) for o in unique_outputs}
            min_count = min(class_counts.values())
            max_count = max(class_counts.values())
            if max_count > min_count * 10:
                warnings.append(f"Severe class imbalance detected: {class_counts}")

        state["validation_errors"] = errors
        state["validation_warnings"] = warnings
        state["validation_passed"] = len(errors) == 0

        return state

    async def _train_model_node(self, state: dict) -> dict:
        """Train the model"""
        prepared_data = state.get("prepared_data")
        model_type = state.get("model_type", ModelType.SCHEMA_MAPPER.value)
        hyperparameters = state.get("hyperparameters")

        if not prepared_data:
            state["training_result"] = {"error": "No prepared data"}
            return state

        # Create training job
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Use provided or default hyperparameters
        if hyperparameters:
            hp = Hyperparameters(**hyperparameters)
        else:
            model_config = self.model_configs.get(model_type, {})
            hp = model_config.get("default_hyperparameters", Hyperparameters())

        job = TrainingJob(
            job_id=job_id,
            model_type=ModelType(model_type),
            dataset_id=prepared_data["dataset_id"],
            hyperparameters=hp,
            status=TrainingStatus.TRAINING,
            started_at=datetime.now()
        )

        self.jobs[job_id] = job

        # Simulate training (in real implementation, this would call actual ML framework)
        training_metrics = await self._simulate_training(job, state)

        job.status = TrainingStatus.COMPLETED
        job.completed_at = datetime.now()
        job.metrics = training_metrics
        job.progress = 1.0

        # Create model version
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_version = ModelVersion(
            version_id=version_id,
            model_type=ModelType(model_type),
            training_job_id=job_id,
            metrics=training_metrics,
            hyperparameters=hp
        )

        self.models[version_id] = model_version

        state["training_result"] = {
            "job_id": job_id,
            "model_version_id": version_id,
            "status": job.status.value,
            "metrics": training_metrics,
            "duration_seconds": (job.completed_at - job.started_at).total_seconds()
        }

        return state

    async def _simulate_training(self, job: TrainingJob, state: dict) -> Dict[str, float]:
        """Simulate model training and return metrics"""
        model_config = self.model_configs.get(job.model_type.value, {})
        metrics_to_compute = model_config.get("metrics", [EvaluationMetric.ACCURACY])

        # Simulate metrics based on data quality and hyperparameters
        base_score = 0.7 + random.uniform(0, 0.2)

        metrics = {}
        for metric in metrics_to_compute:
            if metric == EvaluationMetric.ACCURACY:
                metrics["accuracy"] = min(base_score + random.uniform(0, 0.1), 0.99)
            elif metric == EvaluationMetric.F1_SCORE:
                metrics["f1_score"] = min(base_score + random.uniform(-0.05, 0.1), 0.99)
            elif metric == EvaluationMetric.PRECISION:
                metrics["precision"] = min(base_score + random.uniform(-0.05, 0.1), 0.99)
            elif metric == EvaluationMetric.RECALL:
                metrics["recall"] = min(base_score + random.uniform(-0.05, 0.1), 0.99)
            elif metric == EvaluationMetric.AUC_ROC:
                metrics["auc_roc"] = min(base_score + random.uniform(0, 0.15), 0.99)
            elif metric == EvaluationMetric.MSE:
                metrics["mse"] = max(0.01, 0.1 - base_score * 0.08)
            elif metric == EvaluationMetric.MAE:
                metrics["mae"] = max(0.01, 0.08 - base_score * 0.06)
            elif metric == EvaluationMetric.BLEU:
                metrics["bleu"] = min(base_score + random.uniform(-0.1, 0.1), 0.95)
            elif metric == EvaluationMetric.EXACT_MATCH:
                metrics["exact_match"] = min(base_score - 0.1 + random.uniform(0, 0.1), 0.90)

        # Add training-specific metrics
        metrics["loss"] = max(0.01, 0.5 - base_score * 0.4)
        metrics["val_loss"] = max(0.01, 0.55 - base_score * 0.4)

        return metrics

    async def _optimize_hyperparams_node(self, state: dict) -> dict:
        """Optimize hyperparameters"""
        prepared_data = state.get("prepared_data")
        model_type = state.get("model_type", ModelType.SCHEMA_MAPPER.value)
        strategy = state.get("optimization_strategy", OptimizationStrategy.RANDOM_SEARCH.value)
        n_trials = state.get("n_trials", 10)

        if not prepared_data:
            state["optimization_result"] = {"error": "No prepared data"}
            return state

        model_config = self.model_configs.get(model_type, {})
        default_hp = model_config.get("default_hyperparameters", Hyperparameters())

        # Define search space
        search_space = {
            "learning_rate": [0.0001, 0.0005, 0.001, 0.005],
            "batch_size": [16, 32, 64, 128],
            "epochs": [10, 20, 30, 50],
            "dropout_rate": [0.1, 0.2, 0.3, 0.4]
        }

        # Run trials
        trial_results = []
        best_score = 0
        best_hyperparameters = None

        for i in range(n_trials):
            # Sample hyperparameters
            if strategy == OptimizationStrategy.RANDOM_SEARCH.value:
                trial_hp = Hyperparameters(
                    learning_rate=random.choice(search_space["learning_rate"]),
                    batch_size=random.choice(search_space["batch_size"]),
                    epochs=random.choice(search_space["epochs"]),
                    dropout_rate=random.choice(search_space["dropout_rate"]),
                    hidden_layers=default_hp.hidden_layers,
                    activation=default_hp.activation,
                    optimizer=default_hp.optimizer
                )
            else:
                trial_hp = default_hp

            # Simulate training for this trial
            mock_job = TrainingJob(
                job_id=f"trial_{i}",
                model_type=ModelType(model_type),
                dataset_id=prepared_data["dataset_id"],
                hyperparameters=trial_hp
            )

            metrics = await self._simulate_training(mock_job, state)
            primary_metric = metrics.get("accuracy", metrics.get("f1_score", 0))

            trial_results.append({
                "trial": i,
                "hyperparameters": {
                    "learning_rate": trial_hp.learning_rate,
                    "batch_size": trial_hp.batch_size,
                    "epochs": trial_hp.epochs,
                    "dropout_rate": trial_hp.dropout_rate
                },
                "score": primary_metric
            })

            if primary_metric > best_score:
                best_score = primary_metric
                best_hyperparameters = trial_hp

        state["optimization_result"] = {
            "strategy": strategy,
            "n_trials": n_trials,
            "best_score": best_score,
            "best_hyperparameters": {
                "learning_rate": best_hyperparameters.learning_rate,
                "batch_size": best_hyperparameters.batch_size,
                "epochs": best_hyperparameters.epochs,
                "dropout_rate": best_hyperparameters.dropout_rate
            } if best_hyperparameters else None,
            "all_trials": trial_results
        }

        # Set best hyperparameters for training
        if best_hyperparameters:
            state["hyperparameters"] = {
                "learning_rate": best_hyperparameters.learning_rate,
                "batch_size": best_hyperparameters.batch_size,
                "epochs": best_hyperparameters.epochs,
                "dropout_rate": best_hyperparameters.dropout_rate
            }

        return state

    async def _evaluate_model_node(self, state: dict) -> dict:
        """Evaluate trained model"""
        training_result = state.get("training_result")
        model_version_id = training_result.get("model_version_id") if training_result else None

        if not model_version_id:
            model_version_id = state.get("model_version_id")

        if not model_version_id or model_version_id not in self.models:
            state["evaluation_metrics"] = {}
            return state

        model = self.models[model_version_id]
        dataset_id = state.get("evaluation_dataset_id") or (
            self.jobs[model.training_job_id].dataset_id
            if model.training_job_id in self.jobs else None
        )

        # Use LLM to generate detailed evaluation insights
        system_prompt = """You are an ML evaluation expert. Based on the model metrics,
        provide insights about the model's performance and recommendations for improvement.

        Return a JSON object with:
        - overall_assessment: Brief assessment of model quality
        - strengths: List of model strengths
        - weaknesses: List of potential weaknesses
        - recommendations: List of improvement recommendations
        - production_readiness: Boolean indicating if model is ready for production
        """

        metrics = model.metrics

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Model Type: {model.model_type.value}\nMetrics: {json.dumps(metrics, indent=2)}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            evaluation_insights = json.loads(response.content)
        except Exception as e:
            logger.error(f"Error generating evaluation insights: {e}")
            evaluation_insights = {
                "overall_assessment": "Unable to generate detailed assessment",
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "production_readiness": False
            }

        evaluation_result = EvaluationResult(
            model_version_id=model_version_id,
            dataset_id=dataset_id or "unknown",
            metrics=metrics
        )

        state["evaluation_metrics"] = metrics
        state["evaluation_insights"] = evaluation_insights
        state["evaluation_result"] = {
            "model_version_id": model_version_id,
            "metrics": metrics,
            "insights": evaluation_insights
        }

        return state

    async def _deploy_model_node(self, state: dict) -> dict:
        """Deploy the trained model"""
        training_result = state.get("training_result", {})
        model_version_id = training_result.get("model_version_id")

        if not model_version_id or model_version_id not in self.models:
            state["deployment_result"] = {"error": "Model not found"}
            return state

        model = self.models[model_version_id]
        model.is_deployed = True
        model.deployment_url = f"https://api.datamigrate.ai/models/{model_version_id}"

        state["deployment_result"] = {
            "model_version_id": model_version_id,
            "deployment_url": model.deployment_url,
            "deployed_at": datetime.now().isoformat(),
            "status": "deployed"
        }

        return state

    # Public API Methods

    async def prepare_training_data(
        self,
        examples: List[Dict[str, Any]],
        model_type: ModelType,
        dataset_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare training data for a specific model type.

        Args:
            examples: List of training examples with input/output pairs
            model_type: Type of model to train
            dataset_name: Optional name for the dataset

        Returns:
            Dataset preparation results
        """
        logger.info(f"Preparing {len(examples)} examples for {model_type.value}")

        state = {
            "examples": examples,
            "model_type": model_type.value,
            "dataset_name": dataset_name or f"{model_type.value}_dataset",
            "operation": "prepare"
        }

        # Run preparation nodes only
        state = await self._prepare_data_node(state)
        state = await self._validate_data_node(state)

        return {
            "prepared_data": state.get("prepared_data"),
            "validation_passed": state.get("validation_passed", False),
            "validation_errors": state.get("validation_errors", []),
            "validation_warnings": state.get("validation_warnings", [])
        }

    async def train_model(
        self,
        dataset_id: str,
        model_type: ModelType,
        hyperparameters: Optional[Dict[str, Any]] = None,
        auto_deploy: bool = False,
        deployment_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Train a model on prepared data.

        Args:
            dataset_id: ID of the prepared dataset
            model_type: Type of model to train
            hyperparameters: Optional custom hyperparameters
            auto_deploy: Whether to auto-deploy if metrics meet threshold
            deployment_threshold: Minimum metric value for auto-deployment

        Returns:
            Training results with metrics
        """
        logger.info(f"Starting training for {model_type.value}")

        if dataset_id not in self.datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        state = {
            "prepared_data": {"dataset_id": dataset_id},
            "model_type": model_type.value,
            "hyperparameters": hyperparameters,
            "auto_deploy": auto_deploy,
            "deployment_threshold": deployment_threshold,
            "operation": "train"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "training_result": result.get("training_result"),
            "evaluation_result": result.get("evaluation_result"),
            "deployment_result": result.get("deployment_result")
        }

    async def optimize_and_train(
        self,
        dataset_id: str,
        model_type: ModelType,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.RANDOM_SEARCH,
        n_trials: int = 10
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters and train model.

        Args:
            dataset_id: ID of the prepared dataset
            model_type: Type of model to train
            optimization_strategy: Strategy for hyperparameter optimization
            n_trials: Number of optimization trials

        Returns:
            Optimization and training results
        """
        logger.info(f"Starting optimization for {model_type.value} with {n_trials} trials")

        if dataset_id not in self.datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        state = {
            "prepared_data": {"dataset_id": dataset_id},
            "model_type": model_type.value,
            "optimization_strategy": optimization_strategy.value,
            "n_trials": n_trials,
            "operation": "optimize"
        }

        result = await self.workflow.ainvoke(state)

        return {
            "optimization_result": result.get("optimization_result"),
            "training_result": result.get("training_result"),
            "evaluation_result": result.get("evaluation_result")
        }

    async def evaluate_model(
        self,
        model_version_id: str,
        evaluation_dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model.

        Args:
            model_version_id: ID of the model version to evaluate
            evaluation_dataset_id: Optional separate evaluation dataset

        Returns:
            Evaluation results with metrics and insights
        """
        logger.info(f"Evaluating model {model_version_id}")

        if model_version_id not in self.models:
            return {"error": f"Model {model_version_id} not found"}

        state = {
            "model_version_id": model_version_id,
            "evaluation_dataset_id": evaluation_dataset_id,
            "operation": "evaluate"
        }

        result = await self._evaluate_model_node(state)

        return result.get("evaluation_result", {})

    async def deploy_model(
        self,
        model_version_id: str
    ) -> Dict[str, Any]:
        """
        Deploy a trained model.

        Args:
            model_version_id: ID of the model version to deploy

        Returns:
            Deployment information
        """
        logger.info(f"Deploying model {model_version_id}")

        if model_version_id not in self.models:
            return {"error": f"Model {model_version_id} not found"}

        state = {
            "training_result": {"model_version_id": model_version_id}
        }

        result = await self._deploy_model_node(state)

        return result.get("deployment_result", {})

    def get_model_info(self, model_version_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a model version"""
        model = self.models.get(model_version_id)
        if not model:
            return None

        return {
            "version_id": model.version_id,
            "model_type": model.model_type.value,
            "training_job_id": model.training_job_id,
            "metrics": model.metrics,
            "hyperparameters": {
                "learning_rate": model.hyperparameters.learning_rate,
                "batch_size": model.hyperparameters.batch_size,
                "epochs": model.hyperparameters.epochs,
                "dropout_rate": model.hyperparameters.dropout_rate
            },
            "created_at": model.created_at.isoformat(),
            "is_deployed": model.is_deployed,
            "deployment_url": model.deployment_url
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """List all trained models"""
        return [
            {
                "version_id": m.version_id,
                "model_type": m.model_type.value,
                "created_at": m.created_at.isoformat(),
                "is_deployed": m.is_deployed,
                "primary_metric": max(m.metrics.values()) if m.metrics else 0
            }
            for m in self.models.values()
        ]

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets"""
        return [
            {
                "dataset_id": d.dataset_id,
                "name": d.name,
                "model_type": d.model_type.value,
                "example_count": len(d.examples),
                "created_at": d.created_at.isoformat()
            }
            for d in self.datasets.values()
        ]

    def get_training_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a training job"""
        job = self.jobs.get(job_id)
        if not job:
            return None

        return {
            "job_id": job.job_id,
            "model_type": job.model_type.value,
            "status": job.status.value,
            "progress": job.progress,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metrics": job.metrics,
            "error_message": job.error_message
        }


# Example usage and testing
async def main():
    """Example usage of the ML Fine-Tuning Agent"""

    # Sample training data for schema mapping
    training_examples = [
        {
            "input": {"source_column": "cust_id", "source_type": "INT", "context": "customer identifier"},
            "output": {"target_column": "customer_id", "target_type": "INTEGER", "transformation": "CAST"}
        },
        {
            "input": {"source_column": "fname", "source_type": "VARCHAR(50)", "context": "first name"},
            "output": {"target_column": "first_name", "target_type": "STRING", "transformation": "DIRECT"}
        },
        {
            "input": {"source_column": "lname", "source_type": "VARCHAR(50)", "context": "last name"},
            "output": {"target_column": "last_name", "target_type": "STRING", "transformation": "DIRECT"}
        },
        {
            "input": {"source_column": "email_addr", "source_type": "VARCHAR(255)", "context": "email"},
            "output": {"target_column": "email", "target_type": "STRING", "transformation": "LOWER"}
        },
        {
            "input": {"source_column": "created_dt", "source_type": "DATETIME", "context": "creation date"},
            "output": {"target_column": "created_at", "target_type": "TIMESTAMP", "transformation": "CAST"}
        },
    ]

    # Add more examples to meet minimum
    for i in range(15):
        training_examples.append({
            "input": {"source_column": f"col_{i}", "source_type": "VARCHAR(100)", "context": f"column {i}"},
            "output": {"target_column": f"column_{i}", "target_type": "STRING", "transformation": "DIRECT"}
        })

    try:
        agent = MLFineTuningAgent()

        # Test data preparation
        print("Preparing training data...")
        prep_result = await agent.prepare_training_data(
            examples=training_examples,
            model_type=ModelType.SCHEMA_MAPPER,
            dataset_name="Schema Mapping Training"
        )
        print(f"Dataset prepared: {prep_result['prepared_data']['dataset_id']}")
        print(f"Validation passed: {prep_result['validation_passed']}")

        if prep_result['validation_passed']:
            dataset_id = prep_result['prepared_data']['dataset_id']

            # Test optimization and training
            print("\nRunning hyperparameter optimization and training...")
            train_result = await agent.optimize_and_train(
                dataset_id=dataset_id,
                model_type=ModelType.SCHEMA_MAPPER,
                optimization_strategy=OptimizationStrategy.RANDOM_SEARCH,
                n_trials=5
            )

            print(f"Best optimization score: {train_result['optimization_result']['best_score']:.4f}")
            print(f"Training completed: {train_result['training_result']['status']}")
            print(f"Model metrics: {train_result['training_result']['metrics']}")

            # List all models
            print("\nAll trained models:")
            for model in agent.list_models():
                print(f"  - {model['version_id']}: {model['model_type']} (deployed: {model['is_deployed']})")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set the ANTHROPIC_API_KEY environment variable")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
