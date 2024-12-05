from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_ec2 as ec2
)
from constructs import Construct


class SearchAPIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_id = self.node.try_get_context('vpc_id')
        subnet_ids = self.node.try_get_context('subnet_ids').split(',')
        security_group = self.node.try_get_context('security_group')

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

        search_api_lambda = lambda_.DockerImageFunction(
            self,
            "SearchAPIFunction",
            code=lambda_.DockerImageCode.from_image_asset(
                directory='..'
                ),

            vpc=vpc,
            vpc_subnets=subnet_selection,
            security_groups=[security_group],
        )

        api = apigateway.LambdaRestApi(
            self,
            "search-api-gateway",
            handler=search_api_lambda,
            endpoint_configuration=apigateway.EndpointConfiguration(
                # https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.EndpointConfiguration.html
                types=[apigateway.EndpointType.PRIVATE]
            )
        )
