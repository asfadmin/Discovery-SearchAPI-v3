SHELL := /bin/bash # Use bash syntax

## Make sure any required env-var's are set (i.e with guard-STACK_NAME)
guard-%:
	@ if [ "${${*}}" = "" ]; then \
        echo "ERROR: Required environment variable is $* not set!"; \
        exit 1; \
    fi

docker-build:
	docker build --pull -t searchapi-v3 .

docker-run:
	docker run --net=host searchapi-v3

docker-push:
	export AWS_REGION=us-east-1 && \
	export DOCKER_URI="$$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$${AWS_REGION}.amazonaws.com/searchapi:v3-test" && \
	docker tag searchapi-v3 $${DOCKER_URI} && \
	aws ecr get-login-password --region $${AWS_REGION} | docker login --username AWS --password-stdin $${DOCKER_URI} && \
	docker push $${DOCKER_URI}


sam-validate:
	echo "STARTING sam-validate  ---------------" && \
	sam validate \
		--template-file cloudformation/SAM-lambda.yml \
		--debug \
		--lint

sam-build:
	echo "STARTING sam-build  ---------------" && \
	sam build \
		--template-file cloudformation/SAM-lambda.yml \
		--base-dir ./SearchAPI \
		--debug \
		--use-container

sam-package:
	echo "STARTING sam-package  ---------------" && \
	sam package \
		--template-file cloudformation/SAM-lambda.yml \
		--s3-bucket searchapi-v3-sam \
		--output-template-file sam-output.yml

sam-deploy:
	echo "STARTING sam-deploy  ---------------" && \
	sam deploy \
		--template-file sam-output.yml \
		--stack-name SearchAPI-v3-SAM \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \

sam-all: sam-validate sam-build sam-package sam-deploy

# Test a lambda request:
sam-local-invoke:
	sam local invoke \
		--template-file cloudformation/SAM-lambda.yml

# Test a beanstalk request:
sam-local-start-api:
	sam local start-api

aws-deploy:
	export AWS_REGION=us-east-1 && \
	export DOCKER_URI="$$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$${AWS_REGION}.amazonaws.com/searchapi:v3-test" && \
	aws cloudformation deploy \
		--stack-name "SearchAPI-v3-test" \
		--template-file cloudformation/cfn-stack.yml \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			Maturity="$${MATURITY}" \
			DockerUri="$${DOCKER_URI}"
