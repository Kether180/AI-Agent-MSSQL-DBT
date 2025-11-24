"""
AWS Lambda Handler Functions

This module provides Lambda handler wrappers for each agent node.
Handlers load state from S3, execute the agent, and save state back to S3.
"""

import json
import os
import logging
from typing import Dict, Any, Callable
from functools import wraps
import boto3
from botocore.exceptions import ClientError

from .state import MigrationState
from .nodes import (
    assessment_node, planner_node, executor_node,
    tester_node, rebuilder_node, evaluator_node
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Lazy-loaded AWS clients (only initialize when needed)
_s3_client = None
_secrets_client = None


def get_s3_client():
    """Get or create S3 client"""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3')
    return _s3_client


def get_secrets_client():
    """Get or create Secrets Manager client"""
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = boto3.client('secretsmanager')
    return _secrets_client


def get_secret(secret_name: str) -> str:
    """
    Retrieve secret from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret

    Returns:
        Secret value

    Raises:
        ClientError: If secret cannot be retrieved
    """
    try:
        response = get_secrets_client().get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        raise


def load_state_from_s3(bucket: str, key: str) -> MigrationState:
    """
    Load migration state from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Migration state dictionary

    Raises:
        ClientError: If state cannot be loaded
    """
    try:
        response = get_s3_client().get_object(Bucket=bucket, Key=key)
        state_json = response['Body'].read().decode('utf-8')
        return json.loads(state_json)
    except ClientError as e:
        logger.error(f"Error loading state from s3://{bucket}/{key}: {e}")
        raise


def save_state_to_s3(bucket: str, key: str, state: MigrationState) -> None:
    """
    Save migration state to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key
        state: Migration state to save

    Raises:
        ClientError: If state cannot be saved
    """
    try:
        state_json = json.dumps(state, indent=2, default=str)
        get_s3_client().put_object(
            Bucket=bucket,
            Key=key,
            Body=state_json.encode('utf-8'),
            ContentType='application/json'
        )
        logger.info(f"Saved state to s3://{bucket}/{key}")
    except ClientError as e:
        logger.error(f"Error saving state to s3://{bucket}/{key}: {e}")
        raise


def handler_wrapper(node_func: Callable) -> Callable:
    """
    Decorator for Lambda handlers that adds common logic.

    Handles:
    - Loading state from S3
    - Setting environment variables
    - Executing the node function
    - Saving state back to S3
    - Error handling and logging

    Args:
        node_func: Agent node function to wrap

    Returns:
        Wrapped Lambda handler function
    """
    @wraps(node_func)
    def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Lambda handler function.

        Expected event structure:
        {
            "state_bucket": "my-migration-bucket",
            "state_key": "migrations/migration-123/state.json",
            "anthropic_secret_name": "anthropic-api-key"
        }

        Args:
            event: Lambda event
            context: Lambda context

        Returns:
            Response with status and state location
        """
        try:
            # Extract parameters
            state_bucket = event.get('state_bucket')
            state_key = event.get('state_key')
            anthropic_secret_name = event.get('anthropic_secret_name')

            if not state_bucket or not state_key:
                raise ValueError("state_bucket and state_key are required")

            logger.info(f"Processing migration state from s3://{state_bucket}/{state_key}")

            # Get API key from Secrets Manager if provided
            if anthropic_secret_name:
                try:
                    api_key = get_secret(anthropic_secret_name)
                    os.environ['ANTHROPIC_API_KEY'] = api_key
                    logger.info("Loaded Anthropic API key from Secrets Manager")
                except Exception as e:
                    logger.warning(f"Could not load API key: {e}, using fallback")

            # Load state from S3
            state = load_state_from_s3(state_bucket, state_key)

            # Execute the node function
            logger.info(f"Executing {node_func.__name__}")
            updated_state = node_func(state)

            # Save updated state back to S3
            save_state_to_s3(state_bucket, state_key, updated_state)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'{node_func.__name__} completed successfully',
                    'state_location': f's3://{state_bucket}/{state_key}',
                    'phase': updated_state.get('phase'),
                    'completed_count': updated_state.get('completed_count', 0),
                    'failed_count': updated_state.get('failed_count', 0)
                })
            }

        except Exception as e:
            logger.error(f"Lambda handler error: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': f'Error: {str(e)}',
                    'error_type': type(e).__name__
                })
            }

    return handler


# Lambda Handler Functions

@handler_wrapper
def assessment_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Assessment Agent.

    This is wrapped by handler_wrapper which handles S3 I/O.
    """
    # The wrapper loads state and passes it to assessment_node
    pass  # Wrapper handles everything


@handler_wrapper
def planner_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Planner Agent"""
    pass


@handler_wrapper
def executor_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Executor Agent"""
    pass


@handler_wrapper
def tester_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Tester Agent"""
    pass


@handler_wrapper
def rebuilder_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Rebuilder Agent"""
    pass


@handler_wrapper
def evaluator_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Evaluator Agent"""
    pass


# Direct node mapping for the wrapper to use
HANDLER_NODE_MAP = {
    assessment_handler: assessment_node,
    planner_handler: planner_node,
    executor_handler: executor_node,
    tester_handler: tester_node,
    rebuilder_handler: rebuilder_node,
    evaluator_handler: evaluator_node,
}


def handler_wrapper_v2(node_func: Callable) -> Callable:
    """
    Improved wrapper that directly calls the node function.

    Args:
        node_func: Agent node function to wrap

    Returns:
        Wrapped Lambda handler function
    """
    @wraps(node_func)
    def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Extract parameters
            state_bucket = event.get('state_bucket')
            state_key = event.get('state_key')
            anthropic_secret_name = event.get('anthropic_secret_name')

            if not state_bucket or not state_key:
                raise ValueError("state_bucket and state_key are required")

            logger.info(f"Processing {node_func.__name__}")

            # Get API key if provided
            if anthropic_secret_name:
                try:
                    api_key = get_secret(anthropic_secret_name)
                    os.environ['ANTHROPIC_API_KEY'] = api_key
                except Exception as e:
                    logger.warning(f"Could not load API key: {e}")

            # Load state
            state = load_state_from_s3(state_bucket, state_key)

            # Execute node
            updated_state = node_func(state)

            # Save state
            save_state_to_s3(state_bucket, state_key, updated_state)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'{node_func.__name__} completed',
                    'phase': updated_state.get('phase'),
                    'completed_count': updated_state.get('completed_count', 0),
                    'failed_count': updated_state.get('failed_count', 0)
                })
            }

        except Exception as e:
            logger.error(f"Handler error: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

    return handler


# Create properly wrapped handlers
assessment_lambda = handler_wrapper_v2(assessment_node)
planner_lambda = handler_wrapper_v2(planner_node)
executor_lambda = handler_wrapper_v2(executor_node)
tester_lambda = handler_wrapper_v2(tester_node)
rebuilder_lambda = handler_wrapper_v2(rebuilder_node)
evaluator_lambda = handler_wrapper_v2(evaluator_node)
