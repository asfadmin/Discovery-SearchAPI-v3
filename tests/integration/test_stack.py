import boto3

cf_client = boto3.client('cloudformation', region_name='us-west-2')
cf_response = cf_client.describe_stacks(StackName='SearchAPI-V3-Stack')
rest_api_endpoint = cf_response['Stacks'][0]['Outputs'][0]['OutputValue']