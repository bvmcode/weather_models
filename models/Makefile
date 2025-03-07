AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)

build:
	docker buildx build -t $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest .

create_repo:
	aws ecr create-repository --repository-name weather_models --region us-east-1

auth:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com

push:
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest

envs:
	eval $(aws configure export-credentials --format env)

run:
	docker run \
	 -e AWS_DEFAULT_REGION=us-east-1 \
	 -e AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	 -e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
	 $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest

local_run: envs run

build_and_push: build auth push