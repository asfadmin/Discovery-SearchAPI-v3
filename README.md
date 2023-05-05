# SearchAPI-v3

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders.

- SearchAPI - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code.
- template.yaml - A template that defines the application's AWS resources.

The application uses several AWS resources, including Lambda functions and an API Gateway API. These resources are defined in the `template.yaml` file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

## Default Parameters

I added the parameters for deploying to `samconfig.toml` to have sensible default params specific to this project. Thus SAM may not behave the same as on other projects!

## Deploy the sample application

To use the SAM CLI, you need the following tools.

- SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3 installed](https://www.python.org/downloads/)
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

To build and deploy your application for the first time, run the following in your shell:

### For Python-based Lambda

```bash
export AWS_PROFILE=<your-profile>
# Validate will fail until they add python3.10
# to their whitelist. Everything still works
# after this though.
sam validate --template-file template-python.yaml
sam build --template-file template-python.yaml
sam package
sam deploy /
    --stack-name SearchAPI-v3-SAM-python
```

### For Docker-based Lambda

```bash
export AWS_PROFILE=<your-profile>
# Validate will fail until they add python3.10
# to their whitelist. Everything still works
# after this though.
sam validate --template-file template-docker.yaml
sam build --template-file template-docker.yaml
sam package --image-repository "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/searchapi"
sam deploy \ 
    --stack-name SearchAPI-v3-SAM-docker \ 
    --image-repository "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/searchapi"
```

## Use the SAM CLI to build and test locally

Build your application with the `sam build ...` command above.

The SAM CLI installs dependencies defined in `SearchAPI/requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

Test a single function by invoking it directly with a test event. An event is a JSON document that represents the input that the function receives from the event source. Test events are included in the `events` folder in this project.

Run functions locally and invoke them with the `sam local invoke` command.

```bash
# THIS WON'T WORK until we add API Gateway events to events/*
# for now, use `sam local start-api` in the next part instead.
sam local invoke SearchApiFunction --event events/event.json
```

The SAM CLI can also emulate your application's API. Use the `sam local start-api` to run the API locally on port 3000.

```bash
sam local start-api
curl http://localhost:3000/
```

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called `sam logs`. `sam logs` lets you fetch logs generated by your deployed Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam logs -n SearchApiFunction --stack-name SearchAPI-v3-SAM --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Tests

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
pip install -r tests/requirements.txt --user
# unit test
python -m pytest tests/unit -v
# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
AWS_SAM_STACK_NAME=<stack-name> python -m pytest tests/integration -v
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name SearchAPI-v3-SAM
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)
