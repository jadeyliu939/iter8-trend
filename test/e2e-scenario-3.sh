#!/bin/sh

# Exit on error
set -e

echo ""
echo "===================================="
echo "Scenario #3"
echo "===================================="

echo ""
echo "===================================="
echo "Create Iter8 Experiment"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/canary_reviews-v3_to_reviews-v5.yaml
kubectl get experiments -n bookinfo-iter8

echo ""
echo "===================================="
echo "Deploy canary version"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/reviews-v5.yaml
sleep 1
kubectl wait --for=condition=ExperimentCompleted -n bookinfo-iter8 experiments.iter8.tools reviews-v5-rollout --timeout=300s
kubectl get experiments -n bookinfo-iter8

echo ""
echo "===================================="
echo "Test results"
echo "===================================="
kubectl -n bookinfo-iter8 get experiments.iter8.tools reviews-v5-rollout -o yaml
conclusion=`kubectl -n bookinfo-iter8 get experiments.iter8.tools reviews-v5-rollout -o=jsonpath='{.status.assessment.conclusions[0]}'`
if [ "$conclusion" != "All success criteria were not met" ]; then
  echo "Experiment succeded unexpectedly!"
  exit 1
fi
echo "Experiment failed as expected"
