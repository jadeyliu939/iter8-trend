# Minikube-based development environment

## Start

```
# ./minikube-up.sh
```

## Stop

```
# ./minikube-down.sh
```

## Access

To access a pod running inside of Minikube, e.g., 

```
# kubectl -n iter8 get services
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
iter8-analytics    ClusterIP   10.97.190.235   <none>        8080/TCP   17d
iter8-controller   ClusterIP   10.106.201.75   <none>        443/TCP    17d
iter8-trend        ClusterIP   10.104.66.57    <none>        8888/TCP   17d
```

Start port forwarding
```
# kubectl port-forward -n iter8 deployment/iter8-trend 8888:8888
```

In a different terminal
```
# curl localhost:8888/metrics
```

This should allow one to access the `iter8-trend` pod via port `8888`.
