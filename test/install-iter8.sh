#!/usr/bin/env bash

# Exit on error
set -e

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"
source "$DIR/../iter8-controller/test/e2e/library.sh"

# Install Iter8
header "Install iter8"
curl -L -s https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/install/install.sh | /bin/bash -

# Check if Iter8 pods are all up and running. However, sometimes
# `kubectl apply` doesn't register for `kubectl wait` before, so
# adding 1 sec wait time for the operation to fully register
sleep 1
kubectl wait --for=condition=Ready pods --all -n iter8 --timeout=600s
kubectl -n iter8 get pods
