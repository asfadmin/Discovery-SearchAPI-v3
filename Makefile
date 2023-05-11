SHELL := /bin/bash # Use bash syntax

## Make sure any required env-var's are set (i.e with guard-STACK_NAME)
guard-%:
	@ if [ "${${*}}" = "" ]; then \
        echo "ERROR: Required environment variable is $* not set!"; \
        exit 1; \
    fi

deploy-vanilla:
	export STACK_NAME="SearchAPI-v3-vanilla" && \
	export TAG="vanilla" && \
	export AWS_ECR="$$(aws sts get-caller-identity --query 'Account' --output text).dkr.ecr.us-east-1.amazonaws.com/searchapi-v3" && \
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$${AWS_ECR}" && \
	docker build --pull -t "$${AWS_ECR}:$${TAG}" . && \
	docker push "$${AWS_ECR}:$${TAG}" && \
	aws cloudformation deploy \
		--template template-vanilla.yaml \
		--stack-name $${STACK_NAME} \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			ContainerTag=$${TAG} \
			Maturity=prod && \
	export FUNCTION=$$( \
		aws cloudformation describe-stacks \
			--stack-name $${STACK_NAME} \
			--query "Stacks[?StackName=='$${STACK_NAME}'][].Outputs[?OutputKey=='LambdaFunction'].OutputValue" \
			--output=text \
	) && \
	aws lambda update-function-code \
		--function-name "$${FUNCTION}" \
		--image-uri "$${AWS_ECR}:$${TAG}" \
		--no-cli-pager && \
	echo "Waiting for update to finish...." && \
	aws lambda wait function-updated \
		--function-name "$${FUNCTION}" && \
	echo "Updating lambda function DONE."

deploy-python:
	export STACK_NAME="SearchAPI-v3-python" && \
	export TAG="$${TAG//[^[:alnum:]]/-}" && \
	sam build --template-file template-python.yaml && \
	sam package && \
	sam deploy \
		--stack-name "$${STACK_NAME}"

deploy-docker:
	export STACK_NAME="SearchAPI-v3-docker" && \
	export TAG="$${TAG//[^[:alnum:]]/-}" && \
	export AWS_ECR="$$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/searchapi-v3" && \
	sam build --template-file template-docker.yaml && \
	sam package --image-repository "$${AWS_ECR}" && \
	sam deploy \
		--stack-name "$${STACK_NAME}" \
		--image-repository "$${AWS_ECR}"
