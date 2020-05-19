#!/bin/sh

# Exit on error
set -e

# Build a new Iter8-trend image based on the new code
IMG=iter8-trend:test make docker-build

# Install Helm (from bleeding edge)
curl -fsSL https://get.helm.sh/helm-v2.16.7-linux-amd64.tar.gz | tar xvzf - && sudo mv linux-amd64/helm /usr/local/bin

# Create new Helm template based on the new image
helm template install/kubernetes/helm/iter8-trend/ --name iter8-trend \
--set image.repository=iter8-trend \
--set image.tag=test \
--set image.pullPolicy=IfNotPresent \
> install/kubernetes/iter8-trend.yaml

cat install/kubernetes/iter8-trend.yaml

# Install Iter8-trend
kubectl apply -f install/kubernetes/iter8-trend.yaml

# Check if Iter8 pods are all up and running. However, sometimes
# `kubectl apply` doesn't register for `kubectl wait` before, so
# adding 1 sec wait time for the operation to fully register
sleep 1
kubectl wait --for=condition=Ready pods --all -n iter8 --timeout=300s
# kubectl -n iter8 describe pod iter8-trend
# kubectl -n iter8 logs `kubectl -n iter8 get pods | grep iter8-trend | awk {'print $1'}`
kubectl -n iter8 get pods

