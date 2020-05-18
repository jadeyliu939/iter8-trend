#!/bin/sh

# Install Iter8
kubectl apply -f https://github.com/iter8-tools/iter8-analytics/releases/latest/download/iter8-analytics.yaml -f https://github.com/iter8-tools/iter8-controller/releases/latest/download/iter8-controller.yaml

# Install Iter8-trend
kubectl apply -f install/kubernetes/iter8-trend.yaml

# Check if Iter8 pods are all up and running. However, sometimes
# `kubectl apply` doesn't register for `kubectl wait` before, so
# adding 1 sec wait time for the operation to fully register
sleep 1
kubectl wait --for=condition=Ready pods --all -n iter8 --timeout=180s
# kubectl -n iter8 describe pod iter8-trend
# kubectl -n iter8 logs `kubectl -n iter8 get pods | grep iter8-trend | awk {'print $1'}`
kubectl -n iter8 get pods

