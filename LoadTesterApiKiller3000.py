import argparse
import requests
import json
import boto3
import copy
import uuid
from datetime import datetime, timedelta

####################
## CORE FUNCTIONS ##
####################
# (Keep scrolling for load testing methods)

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
    print("Refreshing Lambda to trigger Cold Start")
    # From stack name, get the lambda function
    lambda_api: dict = cfn_client.describe_stack_resource(
        StackName=stack_name,
        LogicalResourceId='SearchApiFunction'
    )
    function_name = lambda_api["StackResourceDetail"]["PhysicalResourceId"]

    # Force lambda to update, so it invalidates all active/running lambda's
    # (Just make some environment variable a random string)
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

#########################
## Load Tester Methods ##
#########################

def hammer_api(stack_name: str, count: int=10, should_cold_start: bool=False, **time_query_params) -> (timedelta, list):
    """
    Does the SAME query 'count' number of times.

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
        # if it SHOULD cold start, force it to before each request:
        if should_cold_start:
            reset_lambda(stack_name)
        # Finally run the request:
        time = time_query(stack_name, **time_query_params)
        query_times.append(time)
    # Start with datetime.timedelta(0) instead of default "int(0)":
    average_query_time = sum(query_times, start=timedelta(0)) / len(query_times)
    print(f"Average Time: {average_query_time}, Number Queries: {len(query_times)}")
    return average_query_time, query_times

def complex_query(stack_name: str, query_dict: dict, should_cold_start: bool=False) -> (timedelta, list):
    # This needs to be in scope for the recursive method,
    # it saves the output.
    query_list = []
    def recursive_query_list(query_left: dict, current_query: list) -> None:
        # If nothing left todo, you're a recursive leaf. Save and return.
        if not query_left:
            query_list.append(current_query)
            return
        # Grab a random item, and recurse through it's value_list:
        query_left_copy = copy.copy(query_left)
        first_item_key = next(iter(query_left_copy))
        first_item_val = query_left_copy[first_item_key]
        del query_left_copy[first_item_key]
        for item in first_item_val:
            recursive_query_list(query_left_copy, current_query + [(first_item_key, item)])
    # Back to complex_query method. Make each value in dict a list if it's not already.
    # (makes it easier to recurse through).
    for key, val in query_dict.items():
        if not isinstance(val, list):
            query_dict[key] = [val]
    # Make a list of possible queries, iterating over the dict of possibilities:
    recursive_query_list(query_dict, [])
    total_time = timedelta(0)
    # If it shouldn't cold start, make sure the container is warm:
    if not should_cold_start:
        print("Running health check to warm up API")
        health_check(stack_name)
    for q in query_list:
        q = dict(q)
        # if it SHOULD cold start, force it to before each request:
        if should_cold_start:
            reset_lambda(stack_name)
        time = time_query(stack_name, **q)
        total_time += time
    print(f"Total time is: {total_time}. Number of Queries: {len(query_list)}")
    return total_time, query_list


if __name__ == "__main__":
    # health_check("SearchAPI-v3-docker")
    # reset_lambda("SearchAPI-v3-docker")
    # time_query("SearchAPI-v3-vanilla", endpoint="/services/search/param", maxResults=5, platform="S1")
    _, query_time_list = hammer_api("SearchAPI-v3-docker", count=20, should_cold_start=True, endpoint="/services/search/param", maxResults=5, platform="S1")
    print(sum(query_time_list, start=timedelta(0)))
    # query = {
    #     "endpoint": "/services/search/param",
    #     "maxResults": [5,8,2],
    #     "platform": ["S1", "ALOS"]
    # }
    # complex_query("SearchAPI-v3-vanilla", query, should_cold_start=False)
