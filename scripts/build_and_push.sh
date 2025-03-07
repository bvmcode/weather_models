#!/bin/bash
set -e
cd ./models
account_id=$(aws sts get-caller-identity --query "Account" --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $account_id.dkr.ecr.us-east-1.amazonaws.com
aws ecr create-repository --repository-name weather_models --region us-east-1
docker buildx build --platform linux/amd64 -t $account_id.dkr.ecr.us-east-1.amazonaws.com/weather_models:latest .
docker push $account_id.dkr.ecr.us-east-1.amazonaws.com/weather_models:latest