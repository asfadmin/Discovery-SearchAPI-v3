from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_iam as iam,
)
from constructs import Construct

class SearchAPIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        search_api_lambda = lambda_.DockerImageFunction(
            self,
            "SearchAPIFunction",
            code=lambda_.DockerImageCode.from_image_asset(
                directory='..'
                )
        )

        api = apigateway.LambdaRestApi(
            self,
            "search-api-gateway",
            handler=search_api_lambda
        )
