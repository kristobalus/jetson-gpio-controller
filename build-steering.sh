#!/bin/bash

# Read the version from package.json
BRANCH=$(git branch --show-current)
VERSION="1.1.1"
IMAGE=${IMAGE:-"ghcr.io/flux-agi/flux-cart-control-steering"}
echo "building image $IMAGE:$VERSION using buildx..."

# docker buildx create --use --name buildx_instance --driver docker-container --bootstrap

# Check if the buildx instance already exists
if docker buildx inspect buildx_instance > /dev/null 2>&1; then
    echo "buildx instance 'buildx_instance' already exists. Using the existing instance."
    docker buildx use buildx_instance
else
    echo "Creating a new buildx instance 'buildx_instance'..."
    docker buildx create --use --name buildx_instance --driver docker-container --bootstrap
fi

docker buildx build -f ./steering/Dockerfile \
		--progress=plain \
		--build-arg VERSION="$VERSION" \
		--label "build-tag=build-artifact" \
		--platform linux/arm64/v8,linux/amd64 \
		-t "$IMAGE:$VERSION" \
		-t "$IMAGE:latest" \
		--push . || { echo "failed to build docker image"; exit 1; }

docker image prune -f --filter label=build-tag=build-artifact
