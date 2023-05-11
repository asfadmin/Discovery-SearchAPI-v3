import argparse
import requests
import json
import boto3
import uuid
from datetime import datetime, timedelta

cfn_client = boto3.client('cloudformation')
lambda_client = boto3.client('lambda')

def get_api_url_from_stack(stack_name: str) -> str:
    """
    Given a stack name, returns the "SearchApiUrl" output
    Throws on any error.
    """
    stack = cfn_client.describe_stacks(StackName=stack_name)
    outputs = stack["Stacks"][0]["Outputs"]
    api_url = None
    # AWS returns key and value separately, so you have to look
    # through the entire output list to find your match:
    for output in outputs:
        if output["OutputKey"] == "SearchApiUrl":
            api_url = output["OutputValue"]
            break
    assert api_url is not None, f"ERROR: 'SearchApiUrl' not found in stack '{stack_name}' outputs."
    return api_url

def health_check(stack_name: str) -> dict:
    """
    Throws if "api_url" is not available.

    Returns Health endpoint response if success.
    """
    api_url = get_api_url_from_stack(stack_name)
    r = requests.get(api_url, timeout=35)
    r.raise_for_status()
    # Make sure it's a json response:
    api_json = json.loads(r.content)
    return api_json

def reset_lambda(stack_name: str) -> dict:
    """
    Makes the next request trigger a cold-start.
    By updating ENV VAR, lambda has to re-deploy.

    Returns lambda information.
    """
    # From stack name, get the lambda function
    lambda_api: dict = cfn_client.describe_stack_resource(
        StackName=stack_name,
        LogicalResourceId='SearchApiFunction'
    )
    function_name = lambda_api["StackResourceDetail"]["PhysicalResourceId"]

    # Force lambda to update, so it invalidates all active/running lambda's
    lambda_info = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment={
            'Variables': {
                'ForceColdStart': str(uuid.uuid4())[:8]
            }
        }
    )
    # Wait for lambda to finish updating:
    waiter = lambda_client.get_waiter('function_updated_v2')
    waiter.wait(FunctionName=function_name)

    return lambda_info

def time_query(stack_name: str, endpoint: str="/", **query_strings) -> timedelta:
    """
    Does a single query, and returns how long it took to run.
    """
    api_url = get_api_url_from_stack(stack_name)
    # Make sure only the endpoint has the '/' before joining together
    if api_url.endswith("/"):
        api_url = api_url[:-1]
    if not endpoint.startswith("/"):
        endpoint = "/"+endpoint
    # Combine all the fragments:
    full_query = api_url+endpoint
    if query_strings:
        # Convert dict into: [('Hello', 10), ('World', 20)] format.
        query_strings = list(query_strings.items())
        # Convert into: ['Hello=10', 'World=20'] format.
        query_strings = [f"{item[0]}={item[1]}" for item in query_strings]
        full_query = full_query + "?" + "&".join(query_strings)

    print(f"Running {full_query=}")
    start = datetime.now()
    r = requests.get(full_query, timeout=35)
    end = datetime.now()

    r.raise_for_status()
    total_time = end - start
    print(f"Took {total_time} to run.")
    return total_time

def hammer_api(stack_name: str, count: int=10, should_cold_start: bool=False, **time_query_params) -> list:
    """
    Does the same query 'count' number of times.

    All of "time_query_params", just gets passed along to the "time_query" method, so we don't have
    to maintain params in two areas.

    Returns the average time, along with a list of all the times. (average time, [time1, time2, ... ])
    """
    # If it shouldn't cold start, make sure the container is warm:
    if not should_cold_start:
        print("Running health check to warm up API")
        health_check(stack_name)
    query_times = []
    for _ in range(count):
        # if it SHOULD cold start, force it too before each request:
        if should_cold_start:
            reset_lambda(stack_name)
        # Finally run the request:
        time = time_query(stack_name, **time_query_params)
        query_times.append(time)
    # giving datetime.timedelta(0) as the start value makes sum work on tds
    average_query_time = sum(query_times, timedelta(0)) / len(query_times)
    print(f"Average Time: {average_query_time}, Number Queries: {len(query_times)}")
    return average_query_time, query_times


if __name__ == "__main__":
    # health_check("SearchAPI-v3-docker")
    # reset_lambda("SearchAPI-v3-docker")
    # time_query("SearchAPI-v3-vanilla", endpoint="/services/search/param", maxResults=5, platform="S1")
    hammer_api("SearchAPI-v3-vanilla", count=1, should_cold_start=False, endpoint="/services/search/param", maxResults=5, platform="S1")