#!/usr/bin/env bash

# Build the image only when this is triggered by a "Branch build", i.e., PR
# merge. This is checked in .travis.yml
echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin;
export IMG="iter8/iter8-trend:$TRAVIS_BRANCH";
echo "Building PR Docker image = $IMG";
make docker-build;
make docker-push;
