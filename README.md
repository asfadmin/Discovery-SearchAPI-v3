# SearchAPI v3 Minimal Example

## Deploy with SAM (Recommended)

The core [SAM](https://github.com/aws/serverless-application-model) commands I have setup in the makefile. You can run:

```bash
make sam-validate       # Validate the stack
make sam-build          # Pull everything together it needs to deploy
make sam-package        # Push it up to an S3 bucket
make sam-deploy         # Setup the cloudformation stack
make sam-all            # Does everything above ^^^ in order
make sam-local-invoke   # Setup a lambda-like container for local testing
```

To get off the ground, I have one stack hard-coded that the above commands use/modify. If we need more granule control sooner, let me know and I can prioritize it more.

## Deploy with Cloudformation Directly

Quick setup:

```bash
# Setup a NEW virtual-env:
virtual-env --python=python3 ~/SearchAPIv3-env
source ~/SearchAPIv3-env/bin/activate
# Probably a more minimal package set exists, but for now grab everything:
python3 -m pip install fastapi[all] uvicorn mangum
# Build the container and push it to AWS:
cd SearchAPI-v3
make build
# Create the stack:
make deploy
```

Lambda:
    You can now test the lambda by going to the lambda function, test tab, then selecting "cloudfront-modify-querystring" for the template. The basic function returns whatever is in the url for a response, the default test should return `"body": "{\"result\":\"test\"}"` somewhere inside the json block. (since it hit `/test?otherparams=foo`).

## Getting Started Guides

Deploying [FastAPI](https://fastapi.tiangolo.com/) in AWS Lambda (Starting Guides):

- <https://dimmaski.com/fastapi-aws-sam/>
- <https://iwpnd.pw/articles/2020-01/deploy-fastapi-to-aws-lambda>

Installing [SAM](https://github.com/aws/serverless-application-model):

- <https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html>

Getting incite into how the API is doing:

- <https://www.eliasbrange.dev/posts/observability-with-fastapi-aws-lambda-powertools/>

## ToDo - future us problems

- Restructure repo, so that:
  - SAM-lambda.yml is in the root for deployments
  - SearchAPI python package is inside some sort of "upload" dir. We want to upload it and requirements.txt, without uploading the entire repo along-side it.
- Fix indent from 4 to 2 on SAM-lambda.yml
