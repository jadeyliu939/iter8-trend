#!/usr/bin/env bash

# Build the image only when this is triggered by a "Branch build", i.e., PR merge
if [[ "$TRAVIS_PULL_REQUEST" == "false" ]]; then
  echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin;
  export IMG="iter8/iter8-trend:$TRAVIS_BRANCH";
  echo "Building PR Docker image = $IMG";
  make docker-build;
  make docker-push;
  LATEST="iter8/iter8-trend:latest";
  docker tag $IMG $LATEST;
  export IMG=$LATEST;
  make docker-push;
fi
