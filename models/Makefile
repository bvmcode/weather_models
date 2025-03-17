AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text)
AWS_KEY := $(shell aws configure get default.aws_access_key_id)
AWS_SECRET_KEY := $(shell aws configure get default.aws_secret_access_key)

build:
	docker buildx build -t $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest .

create_repo:
	aws ecr create-repository --repository-name weather_models --region us-east-1

auth:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com

push:
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest

run:
	docker run \
	 -e AWS_DEFAULT_REGION=us-east-1 \
	 -e AWS_ACCESS_KEY_ID=$(AWS_KEY) \
	 -e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_KEY) \
	 -e MODEL_RUN="00" \
	 -e MODEL_RUN_DATE="20250312"\
	 -e MODEL_FORECAST_HOUR="000" \
	 $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/weather_models:latest

build_and_push: build auth create_repo push

delete_repo:
	aws ecr delete-repository --repository-name "weather_models" --region "us-east-1" --force

destroy: auth delete_repo