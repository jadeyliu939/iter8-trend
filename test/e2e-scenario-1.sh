#!/bin/sh

# Exit on error
set -e

echo "*** Start iter8-trend end-to-end testing ***"

echo ""
echo "===================================="
echo "Scenario #1"
echo "===================================="

echo ""
echo "===================================="
echo "Create bookinfo-iter8 namespace"
echo "===================================="
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/namespace.yaml

echo ""
echo "===================================="
echo "Create bookinfo-iter8 app"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/bookinfo-tutorial.yaml
sleep 1
kubectl wait --for=condition=Ready pods --all -n bookinfo-iter8 --timeout=300s
kubectl get pods,services -n bookinfo-iter8

echo ""
echo "===================================="
echo "Create bookinfo-iter8 gateway and vs"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/bookinfo-gateway.yaml
kubectl get gateway -n bookinfo-iter8
kubectl get vs -n bookinfo-iter8

echo ""
echo "===================================="
echo "Generate workload"
echo "===================================="
# We are using nodeport of the Istio ingress gateway to access bookinfo app
IP='127.0.0.1'
PORT=`kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}'`
# Following uses the K8s service IP/port to access bookinfo app
#IP=`kubectl -n bookinfo-iter8 get services | grep productpage | awk '{print $3}'`
#PORT=`kubectl -n bookinfo-iter8 get services | grep productpage | awk '{print $5}' | awk -F/ '{print $1}'`
echo "Bookinfo is accessed at: $IP:$PORT"
curl -H "Host: bookinfo.sample.dev" -Is "http://$IP:$PORT/productpage"
watch -n 0.1 "curl -H \"Host: bookinfo.sample.dev\" -Is \"http://$IP:$PORT/productpage\"" >/dev/null 2>&1 &

echo ""
echo "===================================="
echo "Create Iter8 Experiment"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/canary_reviews-v2_to_reviews-v3.yaml
kubectl get experiments -n bookinfo-iter8

echo ""
echo "===================================="
echo "Deploy canary version"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/reviews-v3.yaml
sleep 1
kubectl wait --for=condition=ExperimentCompleted -n bookinfo-iter8 experiments.iter8.tools reviews-v3-rollout --timeout=300s
kubectl get experiments -n bookinfo-iter8

echo ""
echo "===================================="
echo "Test results"
echo "===================================="
kubectl -n bookinfo-iter8 get experiments.iter8.tools reviews-v3-rollout -o yaml
conclusion=`kubectl -n bookinfo-iter8 get experiments.iter8.tools reviews-v3-rollout -o=jsonpath='{.status.assessment.conclusions[0]}'`
if [ "$conclusion" != "All success criteria were  met" ]; then
  echo "Experiment failed unexpectedly!"
  exit 1
fi
echo "Experiment succeeded!"
