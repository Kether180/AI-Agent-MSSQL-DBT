#!/usr/bin/env python3
"""
AWS CDK App Entry Point

Deploy with:
    cdk deploy --app "python aws/app.py"
"""

import aws_cdk as cdk
from cdk_stack import MigrationWorkflowStack


app = cdk.App()

MigrationWorkflowStack(
    app, "MssqlDbtMigrationStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1"
    ),
    description="MSSQL to dbt Migration Workflow with LangGraph and Step Functions"
)

app.synth()
