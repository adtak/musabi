#!/bin/bash
set -e

if [ $# -ne 2 ]; then
  echo "AWS_ACCOUNT_ID or FUNC_NAME not found."
  exit 1
fi

AWS_ACCOUNT_ID="$1"
FUNC_NAME="$2"

aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com"

IMAGE_TAG="musabi-${FUNC_NAME}"
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/musabi-${FUNC_NAME}"

docker buildx build --platform linux/amd64 --provenance=false --target "${FUNC_NAME}" -t "${IMAGE_TAG}:latest" -f docker/Dockerfile .
docker tag "${IMAGE_TAG}:latest" "${ECR_REPO_URI}:latest"
docker push "${ECR_REPO_URI}:latest"

exit 0