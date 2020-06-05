#!/usr/bin/env bash

# Exit on error
set -e

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"
source "$DIR/../iter8-controller/test/e2e/library.sh"

# Build a new Iter8-trend image based on the new code
header "build iter8-trend"
IMG=iter8-trend:test make docker-build

# Install Helm (from bleeding edge)
header "install helm"
curl -fsSL https://get.helm.sh/helm-v2.16.7-linux-amd64.tar.gz | tar xvzf - && sudo mv linux-amd64/helm /usr/local/bin

# Create new Helm template based on the new image
helm template install/kubernetes/helm/iter8-trend/ --name iter8-trend \
--set image.repository=iter8-trend \
--set image.tag=test \
--set image.pullPolicy=IfNotPresent \
> install/kubernetes/iter8-trend.yaml

cat install/kubernetes/iter8-trend.yaml

# Install Iter8-trend
header "install iter8-trend"
kubectl apply -f install/kubernetes/iter8-trend.yaml

# Check if Iter8 pods are all up and running. However, sometimes
# `kubectl apply` doesn't register for `kubectl wait` before, so
# adding 1 sec wait time for the operation to fully register
sleep 1
kubectl wait --for=condition=Ready pods --all -n iter8 --timeout=600s
# kubectl -n iter8 describe pod iter8-trend
# kubectl -n iter8 logs `kubectl -n iter8 get pods | grep iter8-trend | awk {'print $1'}`
kubectl -n iter8 get pods

