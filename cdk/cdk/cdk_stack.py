import json
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_logs as logs,
)
from constructs import Construct


class SearchAPIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, staging: bool = False, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        try:
            vpc_id = self.node.try_get_context('vpc_id')
            subnet_ids = self.node.try_get_context('subnet_ids').split(',')
            security_group = self.node.try_get_context('security_group')
            if not vpc_id:
                raise AttributeError()

        except AttributeError:
            lambda_vpc_kwargs = {}
            apigateway_kwargs = {}
        else:
            vpc = ec2.Vpc.from_lookup(self, "EDCVPC", vpc_id=vpc_id)
            subnet_selection = ec2.SubnetSelection(
                subnet_filters=[
                    ec2.SubnetFilter.by_ids(
                        subnet_ids=subnet_ids
                    )
                ]
            )
            security_group = ec2.SecurityGroup.from_security_group_id(
                self,
                'EDCSecurityGroup',
                security_group
            )
            lambda_vpc_kwargs = {
                'vpc': vpc,
                'vpc_subnets': subnet_selection,
                'security_groups': [security_group],
            }

            apigateway_kwargs = {
                'endpoint_configuration': apigateway.EndpointConfiguration(
                    # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.EndpointConfiguration.html
                    types=[apigateway.EndpointType.PRIVATE]
                ),
            }

        lambda_id = f'SearchAPI-V3{"-Staging" if staging else ""}-Lambda-Function'
        search_api_lambda = lambda_.DockerImageFunction(
            self,
            id=lambda_id,
            timeout=Duration.seconds(30),
            memory_size=5308,
            code=lambda_.DockerImageCode.from_image_asset(
                directory='..'
                ),
            **lambda_vpc_kwargs,
        )
        
        api_id = f'SearchAPI-V3{"-Staging" if staging else ""}-RestAPI'
        api = apigateway.LambdaRestApi(
            self,   
            id=api_id,
            handler=search_api_lambda,
            proxy=True,
            binary_media_types=['multipart/form-data', 'application/octet-stream'],
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS, allow_methods=apigateway.Cors.ALL_METHODS
            ),
            # deploy_options=apigateway.StageOptions(
            #     access_log_destination=apigateway.LogGroupLogDestination(
            #         logs.LogGroup(
            #             self,
            #             f'{api_id}-LogGroup',
            #             retention=logs.RetentionDays.THREE_MONTHS,
            #         )
            #     ), # type: ignore
            #     access_log_format=apigateway.AccessLogFormat.custom(
            #         json.dumps(
            #             {
            #                 'sourceIp': '$context.identity.sourceIp',
            #                 'httpMethod': '$context.httpMethod',
            #                 'path': '$context.path',
            #                 'status': '$context.status',
            #                 'responseLength': '$context.responseLength',
            #                 'responseLatency': '$context.responseLatency',
            #                 'requestTime': '$context.requestTime',
            #                 'protocol': '$context.protocol',
            #                 'userAgent': '$context.identity.userAgent',
            #                 'requestId': '$context.requestId',
            #             }
            #         )
            #     ),
            # ),
            **apigateway_kwargs,
            # endpoint_configuration=apigateway.EndpointConfiguration(
            #     # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.EndpointConfiguration.html
            #     types=[apigateway.EndpointType.PRIVATE]
            # )
        )
