#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.cdk_stack import SearchAPIStack


app = cdk.App()

staging = False
suffix = ''
api_stage = app.node.try_get_context('api_stage')

if api_stage.endswith('staging'):
    staging = True
    suffix = '-Staging'

SearchAPIStack(app, f"SearchAPIStack{suffix}",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    staging=staging,
    api_stage=api_stage,
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION')
    ),
    description=f'SearchAPI V3 CDK Lambda Stack{" (staging)" if staging else ""}',
    stack_name=f'SearchAPI-V3-Stack{suffix}',
    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
