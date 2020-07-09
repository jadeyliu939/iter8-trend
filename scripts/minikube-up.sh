#!/usr/bin/env bash
 
KUBECONFIG=$HOME/.kube/config
: "${KUBE_VERSION:=v1.18.3}"
: "${ISTIO_VERSION:=1.6.3}"

show_help() {
  echo "Usage:"
  echo "$0 # use defaults (\$KUBE_VERSION=$KUBE_VERSION,\$ISTIO_VERSION=$ISTIO_VERSION)"
  echo "KUBE_VERSION=v1.17.1 $0 # use a different Kubernetes version"
  echo "ISTIO_VERSION=1.5.4 $0 # use a different Istio version"
  echo "KUBE_VERSION=v1.17.1 ISTIO_VERSION=1.5.4 $0 # use different Kubernetes and Istio versions"
}

install() {
  if [ -z `which virtualbox` ]; then
    brew cask install virtualbox
  else
    echo "virtualbox already installed"
  fi
  
  if [ -z `which minikube` ]; then
    brew install minikube
  else
    echo "minikube already installed"
  fi
  
  # Create kube and minikube configuration directories if they don't exist
  mkdir -p $HOME/.kube $HOME/.minikube
  touch $KUBECONFIG
  
  minikube start --profile=minikube --vm-driver=virtualbox --kubernetes-version=$KUBE_VERSION
  
  # Use /tmp so not to polute the current directory
  if [ ! -d /tmp/istio-${ISTIO_VERSION} ]; then
    ( cd /tmp && curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh - )
  fi
  /tmp/istio-${ISTIO_VERSION}/bin/istioctl version
  /tmp/istio-${ISTIO_VERSION}/bin/istioctl manifest apply --set profile=demo
  sleep 1
  kubectl wait --for=condition=Ready pods --all -n istio-system --timeout=540s
  kubectl -n istio-system get pods
}

if [ ! -z "$1" ] && [ "$1" = "--help" ]; then
  show_help
else
  install
fi

