#!/bin/sh

echo "===================================="
echo "Start iter8-trend end-to-end testing"
echo "===================================="

echo "===================================="
echo "Create bookinfo-iter8 namespace"
echo "===================================="
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/namespace.yaml

echo "===================================="
echo "Enable Istio for bookinfo-iter8 ns"
echo "===================================="
kubectl label namespace bookinfo-iter8 istio-injection=enabled

echo "===================================="
echo "Create bookinfo-iter8 app"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/bookinfo-tutorial.yaml
kubectl wait --for=condition=Ready pods --all -n bookinfo-iter8 --timeout=180s
kubectl get pods,services -n bookinfo-iter8

echo "===================================="
echo "Create bookinfo-iter8 gateway"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/bookinfo-gateway.yaml
kubectl get gateway -n bookinfo-iter8
kubectl get vs -n bookinfo-iter8

echo "===================================="
echo "Generate workload"
echo "===================================="
IP=kubectl -n bookinfo-iter8 get services | grep productpage | awk '{print $3}'
watch -n 0.1 'curl -H "Host: bookinfo.sample.dev" -Is "http://${GATEWAY_URL}/productpage"'&

echo "===================================="
echo "Create Iter8 Experiment"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/canary_reviews-v2_to_reviews-v3.yaml
kubectl get experiments -n bookinfo-iter8

echo "===================================="
echo "Deploy canary version"
echo "===================================="
kubectl apply -n bookinfo-iter8 -f https://raw.githubusercontent.com/iter8-tools/iter8-controller/master/doc/tutorials/istio/bookinfo/reviews-v3.yaml
kubectl get experiments -n bookinfo-iter8

