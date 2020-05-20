#!/bin/sh

# Exit on error
set -e

# This scenario reuses the Istio Gateway and Virtual Service created in scenario 1

echo ""
echo "===================================="
echo "Scenario #5"
echo "===================================="

echo ""
echo "===================================="
echo "Create Iter8 Experiment"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/canary_productpage-v1_to_productpage-v2.yaml
kubectl get experiments -n bookinfo-iter8

echo ""
echo "===================================="
echo "Deploy canary version"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/productpage-v2.yaml
sleep 1
kubectl wait --for=condition=ExperimentCompleted -n bookinfo-iter8 experiments.iter8.tools productpage-v2-rollout --timeout=300s
kubectl get experiments -n bookinfo-iter8
kubectl get vs bookinfo -n bookinfo-iter8 -o yaml

echo ""
echo "===================================="
echo "Test results"
echo "===================================="
kubectl -n bookinfo-iter8 get experiments.iter8.tools productpage-v2-rollout -o yaml
conclusion=`kubectl -n bookinfo-iter8 get experiments.iter8.tools productpage-v2-rollout -o=jsonpath='{.status.assessment.conclusions[0]}'`
if [ "$conclusion" != "All success criteria were  met" ]; then
  echo "Experiment failed unexpectedly!"
  exit 1
fi
echo "Experiment succeeded as expected!"
