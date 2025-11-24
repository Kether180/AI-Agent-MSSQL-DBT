"""
AWS CDK Infrastructure Stack

This module defines the AWS infrastructure for running the migration
workflow using Lambda functions and Step Functions.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
)
from constructs import Construct


class MigrationWorkflowStack(Stack):
    """
    CDK Stack for MSSQL to dbt Migration Workflow

    Creates:
    - S3 bucket for state storage
    - 6 Lambda functions (one per agent)
    - IAM roles with necessary permissions
    - Step Functions state machine
    - Secrets Manager secret for API key
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for state storage
        state_bucket = s3.Bucket(
            self, "MigrationStateBucket",
            bucket_name=f"mssql-dbt-migration-state-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(90),
                    noncurrent_version_expiration=Duration.days(30)
                )
            ]
        )

        # Secrets Manager for Anthropic API Key
        anthropic_secret = secretsmanager.Secret(
            self, "AnthropicApiKeySecret",
            secret_name="mssql-dbt-migration/anthropic-api-key",
            description="Anthropic API key for Claude integration"
        )

        # IAM Role for Lambda functions
        lambda_role = iam.Role(
            self, "MigrationLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Role for migration Lambda functions",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Grant S3 permissions
        state_bucket.grant_read_write(lambda_role)

        # Grant Secrets Manager permissions
        anthropic_secret.grant_read(lambda_role)

        # Common Lambda environment variables
        common_env = {
            "STATE_BUCKET": state_bucket.bucket_name,
            "ANTHROPIC_SECRET_NAME": anthropic_secret.secret_name,
            "LOG_LEVEL": "INFO"
        }

        # Lambda Layer for dependencies
        dependencies_layer = lambda_.LayerVersion(
            self, "DependenciesLayer",
            code=lambda_.Code.from_asset("lambda_layers/dependencies"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_12],
            description="Dependencies for migration agents"
        )

        # Lambda Functions for each agent

        assessment_lambda = lambda_.Function(
            self, "AssessmentLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.assessment_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(5),
            memory_size=512,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        planner_lambda = lambda_.Function(
            self, "PlannerLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.planner_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(5),
            memory_size=512,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        executor_lambda = lambda_.Function(
            self, "ExecutorLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.executor_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(10),
            memory_size=1024,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        tester_lambda = lambda_.Function(
            self, "TesterLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.tester_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(10),
            memory_size=1024,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        rebuilder_lambda = lambda_.Function(
            self, "RebuilderLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.rebuilder_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(10),
            memory_size=1024,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        evaluator_lambda = lambda_.Function(
            self, "EvaluatorLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agents.lambda_handlers.evaluator_lambda",
            code=lambda_.Code.from_asset("."),
            role=lambda_role,
            environment=common_env,
            timeout=Duration.minutes(5),
            memory_size=512,
            layers=[dependencies_layer],
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Step Functions State Machine

        # Define tasks
        assessment_task = tasks.LambdaInvoke(
            self, "RunAssessment",
            lambda_function=assessment_lambda,
            output_path="$.Payload"
        )

        planner_task = tasks.LambdaInvoke(
            self, "RunPlanner",
            lambda_function=planner_lambda,
            output_path="$.Payload"
        )

        executor_task = tasks.LambdaInvoke(
            self, "RunExecutor",
            lambda_function=executor_lambda,
            output_path="$.Payload"
        )

        tester_task = tasks.LambdaInvoke(
            self, "RunTester",
            lambda_function=tester_lambda,
            output_path="$.Payload"
        )

        rebuilder_task = tasks.LambdaInvoke(
            self, "RunRebuilder",
            lambda_function=rebuilder_lambda,
            output_path="$.Payload"
        )

        evaluator_task = tasks.LambdaInvoke(
            self, "RunEvaluator",
            lambda_function=evaluator_lambda,
            output_path="$.Payload"
        )

        # Success and Failure states
        success = sfn.Succeed(self, "MigrationComplete")
        failure = sfn.Fail(
            self, "MigrationFailed",
            cause="Migration workflow failed",
            error="MIGRATION_ERROR"
        )

        # Check if models exist after planning
        check_models = sfn.Choice(self, "CheckModelsExist")
        check_models.when(
            sfn.Condition.number_greater_than("$.body.completed_count", 0),
            executor_task
        ).when(
            sfn.Condition.number_equals("$.body.completed_count", 0),
            evaluator_task
        ).otherwise(failure)

        # Check test results
        check_test_results = sfn.Choice(self, "CheckTestResults")

        # Increment model index (pseudo-task using Pass state)
        advance_model = sfn.Pass(
            self, "AdvanceToNextModel",
            parameters={
                "current_model_index.$": "States.MathAdd($.body.current_model_index, 1)"
            }
        )

        # Check if more models to process
        check_more_models = sfn.Choice(self, "CheckMoreModels")
        check_more_models.when(
            sfn.Condition.boolean_equals("$.body.is_complete", True),
            evaluator_task
        ).when(
            sfn.Condition.boolean_equals("$.body.is_complete", False),
            executor_task
        ).otherwise(evaluator_task)

        # Check if should rebuild
        check_rebuild = sfn.Choice(self, "CheckShouldRebuild")
        check_rebuild.when(
            sfn.Condition.string_equals("$.body.current_model_status", "failed"),
            sfn.Choice(self, "CheckRetries")
                .when(
                    sfn.Condition.number_less_than("$.body.current_model_attempts", 3),
                    rebuilder_task
                )
                .otherwise(advance_model)
        ).when(
            sfn.Condition.string_equals("$.body.current_model_status", "completed"),
            advance_model
        ).otherwise(advance_model)

        # Connect the workflow
        check_test_results.afterwards().next(check_rebuild)
        check_rebuild.afterwards().next(check_more_models)

        definition = (
            assessment_task
            .next(planner_task)
            .next(check_models)
        )

        executor_task.next(tester_task)
        tester_task.next(check_test_results)
        rebuilder_task.next(tester_task)
        advance_model.next(check_more_models)
        evaluator_task.next(success)

        # Create State Machine
        state_machine = sfn.StateMachine(
            self, "MigrationWorkflow",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.hours(2),
            tracing_enabled=True,
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self, "StateMachineLogs",
                    retention=logs.RetentionDays.ONE_WEEK
                ),
                level=sfn.LogLevel.ALL
            )
        )

        # Store references
        self.state_bucket = state_bucket
        self.state_machine = state_machine
        self.anthropic_secret = anthropic_secret
