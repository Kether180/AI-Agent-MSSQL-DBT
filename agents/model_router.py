"""
Model Router - Flexible LLM Provider System

This module provides a unified interface for multiple LLM providers,
enabling:
1. Easy switching between providers (Claude, OpenAI, local models)
2. Cost optimization (route simple tasks to cheaper models)
3. Future fine-tuning support with custom models
4. Fallback chains for reliability

Author: Alexander Garcia Angus
Company: OKO Investments
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class ModelProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"      # Claude models
    OPENAI = "openai"            # GPT models
    OLLAMA = "ollama"            # Local open-source models
    HUGGINGFACE = "huggingface"  # HuggingFace models
    CUSTOM = "custom"            # Fine-tuned custom models
    VLLM = "vllm"                # vLLM for production inference


class TaskComplexity(Enum):
    """Task complexity for smart routing"""
    SIMPLE = "simple"      # Basic SQL generation, simple transformations
    MEDIUM = "medium"      # Standard migrations, moderate logic
    COMPLEX = "complex"    # Complex stored procedures, business logic
    CRITICAL = "critical"  # Production migrations, requires best model


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: ModelProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0    # Cost tracking
    cost_per_1k_output: float = 0.0
    supports_function_calling: bool = True
    supports_streaming: bool = True
    context_window: int = 100000
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PRE-CONFIGURED MODELS
# =============================================================================

AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    # Anthropic Claude Models
    "claude-sonnet-4": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-sonnet-4-20250514",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        context_window=200000,
    ),
    "claude-opus-4": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-opus-4-20250514",
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        context_window=200000,
    ),
    "claude-haiku": ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-5-haiku-20241022",
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        context_window=200000,
    ),

    # OpenAI Models
    "gpt-4o": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o",
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        context_window=128000,
    ),
    "gpt-4o-mini": ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o-mini",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        context_window=128000,
    ),

    # Open-Source Models (via Ollama or vLLM)
    "llama-3-70b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="llama3:70b",
        base_url="http://localhost:11434",
        cost_per_1k_input=0.0,  # Free if self-hosted
        cost_per_1k_output=0.0,
        context_window=8192,
        supports_function_calling=False,
    ),
    "llama-3-8b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="llama3:8b",
        base_url="http://localhost:11434",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=8192,
        supports_function_calling=False,
    ),
    "mistral-7b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="mistral:7b",
        base_url="http://localhost:11434",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=32768,
        supports_function_calling=False,
    ),
    "codellama-34b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="codellama:34b",
        base_url="http://localhost:11434",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=16384,
        supports_function_calling=False,
        metadata={"specialization": "code"}
    ),
    "sqlcoder-7b": ModelConfig(
        provider=ModelProvider.OLLAMA,
        model_name="sqlcoder:7b",
        base_url="http://localhost:11434",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=8192,
        supports_function_calling=False,
        metadata={"specialization": "sql"}
    ),

    # Custom Fine-tuned Model (placeholder for future)
    "datamigrate-sql-v1": ModelConfig(
        provider=ModelProvider.CUSTOM,
        model_name="datamigrate-sql-v1",
        base_url="http://localhost:8080/v1",  # vLLM or custom endpoint
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=8192,
        supports_function_calling=False,
        metadata={
            "specialization": "mssql-to-dbt",
            "fine_tuned_on": "migration_examples",
            "version": "1.0.0"
        }
    ),
}


# =============================================================================
# ABSTRACT BASE CLASS FOR MODEL CLIENTS
# =============================================================================

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response from the model"""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> Dict:
        """Generate a JSON response from the model"""
        pass

    def track_usage(self, input_tokens: int, output_tokens: int):
        """Track token usage and cost"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        cost = (
            (input_tokens / 1000) * self.config.cost_per_1k_input +
            (output_tokens / 1000) * self.config.cost_per_1k_output
        )
        self.total_cost += cost
        return cost

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "model": self.config.model_name,
            "provider": self.config.provider.value,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 4),
        }


# =============================================================================
# ANTHROPIC CLIENT
# =============================================================================

class AnthropicClient(BaseLLMClient):
    """Client for Anthropic Claude models"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        client = self._get_client()

        response = client.messages.create(
            model=self.config.model_name,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature if temperature is not None else self.config.temperature,
            system=system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}]
        )

        # Track usage
        self.track_usage(
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        return response.content[0].text

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> Dict:
        system = system_prompt or "You are a helpful assistant that responds in valid JSON."
        if schema:
            system += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        response = await self.generate(
            prompt=prompt + "\n\nRespond with valid JSON only.",
            system_prompt=system,
        )

        # Parse JSON from response
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {"error": str(e), "raw_response": response}


# =============================================================================
# OPENAI CLIENT
# =============================================================================

class OpenAIClient(BaseLLMClient):
    """Client for OpenAI GPT models"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            max_tokens=max_tokens or self.config.max_tokens,
            temperature=temperature if temperature is not None else self.config.temperature,
        )

        # Track usage
        self.track_usage(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return response.choices[0].message.content

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> Dict:
        client = self._get_client()

        messages = []
        system = system_prompt or "You are a helpful assistant."
        messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            response_format={"type": "json_object"},
        )

        self.track_usage(
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        return json.loads(response.choices[0].message.content)


# =============================================================================
# OLLAMA CLIENT (Local Open-Source Models)
# =============================================================================

class OllamaClient(BaseLLMClient):
    """Client for Ollama (local open-source models)"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "system": system_prompt or "",
                    "stream": False,
                    "options": {
                        "temperature": temperature if temperature is not None else self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens,
                    }
                }
            )

            result = response.json()

            # Estimate tokens (Ollama doesn't always provide exact counts)
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(result.get("response", "").split()) * 1.3
            self.track_usage(int(input_tokens), int(output_tokens))

            return result.get("response", "")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> Dict:
        system = system_prompt or "You are a helpful assistant."
        system += "\n\nIMPORTANT: Respond with valid JSON only, no markdown formatting."

        if schema:
            system += f"\n\nJSON Schema:\n{json.dumps(schema, indent=2)}"

        response = await self.generate(
            prompt=prompt,
            system_prompt=system,
        )

        try:
            # Clean response
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama: {e}")
            return {"error": str(e), "raw_response": response}


# =============================================================================
# CUSTOM/VLLM CLIENT (For Fine-tuned Models)
# =============================================================================

class CustomModelClient(BaseLLMClient):
    """Client for custom fine-tuned models (via vLLM or similar)"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:8080/v1"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        import httpx

        # Use OpenAI-compatible API (vLLM supports this)
        async with httpx.AsyncClient(timeout=120.0) as client:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.config.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens or self.config.max_tokens,
                    "temperature": temperature if temperature is not None else self.config.temperature,
                }
            )

            result = response.json()

            # Track usage
            if "usage" in result:
                self.track_usage(
                    result["usage"].get("prompt_tokens", 0),
                    result["usage"].get("completion_tokens", 0)
                )

            return result["choices"][0]["message"]["content"]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None,
    ) -> Dict:
        system = system_prompt or "You are a helpful assistant."
        system += "\n\nRespond with valid JSON only."

        response = await self.generate(prompt, system)

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw_response": response}


# =============================================================================
# MODEL ROUTER
# =============================================================================

class ModelRouter:
    """
    Intelligent model router that selects the best model for each task.

    Features:
    - Cost optimization: Route simple tasks to cheaper models
    - Quality assurance: Use premium models for critical tasks
    - Fallback chains: Automatic retry with different models
    - Usage tracking: Monitor costs across all models
    """

    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.routing_config = self._default_routing_config()
        self.fallback_chains = self._default_fallback_chains()

    def _default_routing_config(self) -> Dict[TaskComplexity, str]:
        """Default model routing based on task complexity"""
        return {
            TaskComplexity.SIMPLE: "claude-haiku",      # Cheapest, fast
            TaskComplexity.MEDIUM: "gpt-4o-mini",       # Good balance
            TaskComplexity.COMPLEX: "claude-sonnet-4",  # High quality
            TaskComplexity.CRITICAL: "claude-opus-4",   # Best quality
        }

    def _default_fallback_chains(self) -> Dict[str, List[str]]:
        """Fallback chains if primary model fails"""
        return {
            "claude-opus-4": ["claude-sonnet-4", "gpt-4o"],
            "claude-sonnet-4": ["gpt-4o", "claude-haiku"],
            "claude-haiku": ["gpt-4o-mini", "llama-3-8b"],
            "gpt-4o": ["claude-sonnet-4", "gpt-4o-mini"],
            "gpt-4o-mini": ["claude-haiku", "llama-3-8b"],
            "llama-3-70b": ["llama-3-8b", "mistral-7b"],
            "llama-3-8b": ["mistral-7b", "codellama-34b"],
        }

    def get_client(self, model_name: str) -> BaseLLMClient:
        """Get or create a client for the specified model"""
        if model_name not in self.clients:
            if model_name not in AVAILABLE_MODELS:
                raise ValueError(f"Unknown model: {model_name}")

            config = AVAILABLE_MODELS[model_name]

            # Create appropriate client based on provider
            if config.provider == ModelProvider.ANTHROPIC:
                self.clients[model_name] = AnthropicClient(config)
            elif config.provider == ModelProvider.OPENAI:
                self.clients[model_name] = OpenAIClient(config)
            elif config.provider == ModelProvider.OLLAMA:
                self.clients[model_name] = OllamaClient(config)
            elif config.provider in (ModelProvider.CUSTOM, ModelProvider.VLLM):
                self.clients[model_name] = CustomModelClient(config)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")

        return self.clients[model_name]

    def route(self, complexity: TaskComplexity) -> BaseLLMClient:
        """Route to the appropriate model based on task complexity"""
        model_name = self.routing_config.get(complexity, "claude-sonnet-4")
        return self.get_client(model_name)

    async def generate_with_fallback(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate with automatic fallback on failure"""
        models_to_try = [model_name] + self.fallback_chains.get(model_name, [])

        last_error = None
        for model in models_to_try:
            try:
                client = self.get_client(model)
                result = await client.generate(prompt, system_prompt, **kwargs)
                if model != model_name:
                    logger.info(f"Used fallback model: {model}")
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All models failed. Last error: {last_error}")

    def set_routing(self, complexity: TaskComplexity, model_name: str):
        """Update routing configuration"""
        if model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_name}")
        self.routing_config[complexity] = model_name

    def register_custom_model(self, name: str, config: ModelConfig):
        """Register a custom fine-tuned model"""
        AVAILABLE_MODELS[name] = config
        logger.info(f"Registered custom model: {name}")

    def get_all_usage_stats(self) -> Dict[str, Dict]:
        """Get usage statistics for all active clients"""
        return {
            name: client.get_usage_stats()
            for name, client in self.clients.items()
        }

    def get_total_cost(self) -> float:
        """Get total cost across all models"""
        return sum(
            client.total_cost
            for client in self.clients.values()
        )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_router_instance: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get the singleton model router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def generate(
    prompt: str,
    complexity: TaskComplexity = TaskComplexity.MEDIUM,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Generate a response using the appropriate model for the task complexity"""
    router = get_model_router()
    client = router.route(complexity)
    return await client.generate(prompt, system_prompt, **kwargs)


async def generate_sql(
    prompt: str,
    system_prompt: Optional[str] = None,
) -> str:
    """Generate SQL using a code-specialized model"""
    router = get_model_router()

    # Try SQL-specialized model first, fallback to general
    try:
        client = router.get_client("sqlcoder-7b")
    except Exception:
        client = router.route(TaskComplexity.MEDIUM)

    sql_system = system_prompt or """You are an expert SQL developer specializing in:
- Microsoft SQL Server (T-SQL)
- dbt (data build tool) transformations
- Data warehouse modeling

Generate clean, efficient, well-documented SQL code."""

    return await client.generate(prompt, sql_system)


# =============================================================================
# FINE-TUNING DATA COLLECTOR
# =============================================================================

class FineTuningDataCollector:
    """
    Collect successful migrations for future fine-tuning.

    When a migration succeeds with high quality score,
    save the input/output pair for training data.
    """

    def __init__(self, output_dir: str = "fine_tuning_data"):
        self.output_dir = output_dir
        self.examples: List[Dict] = []
        os.makedirs(output_dir, exist_ok=True)

    def add_example(
        self,
        task_type: str,  # "assessment", "planning", "execution", etc.
        input_data: Dict,
        output_data: Dict,
        quality_score: float,
        metadata: Optional[Dict] = None
    ):
        """Add a successful example for fine-tuning"""
        if quality_score < 0.8:  # Only collect high-quality examples
            return

        example = {
            "task_type": task_type,
            "input": input_data,
            "output": output_data,
            "quality_score": quality_score,
            "metadata": metadata or {},
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }

        self.examples.append(example)
        logger.info(f"Collected fine-tuning example: {task_type} (score: {quality_score})")

    def export_for_training(self, format: str = "jsonl") -> str:
        """Export collected data for fine-tuning"""
        filename = f"{self.output_dir}/training_data.{format}"

        if format == "jsonl":
            with open(filename, "w") as f:
                for example in self.examples:
                    # Convert to chat format for fine-tuning
                    training_example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are a {example['task_type']} agent for MSSQL to dbt migration."
                            },
                            {
                                "role": "user",
                                "content": json.dumps(example["input"])
                            },
                            {
                                "role": "assistant",
                                "content": json.dumps(example["output"])
                            }
                        ]
                    }
                    f.write(json.dumps(training_example) + "\n")

        logger.info(f"Exported {len(self.examples)} examples to {filename}")
        return filename

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        task_counts = {}
        for example in self.examples:
            task = example["task_type"]
            task_counts[task] = task_counts.get(task, 0) + 1

        return {
            "total_examples": len(self.examples),
            "by_task_type": task_counts,
            "avg_quality_score": sum(e["quality_score"] for e in self.examples) / len(self.examples) if self.examples else 0,
        }


# Singleton collector
_collector_instance: Optional[FineTuningDataCollector] = None


def get_fine_tuning_collector() -> FineTuningDataCollector:
    """Get the singleton fine-tuning data collector"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = FineTuningDataCollector()
    return _collector_instance
