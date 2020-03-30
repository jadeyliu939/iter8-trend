#!/bin/sh

IMAGE=haih/iter8-trend
TAG=latest

docker build -t $IMAGE:$TAG .
docker push $IMAGE:$TAG
