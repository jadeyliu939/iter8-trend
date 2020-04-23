# Iter8-trend
This is an optional component to [Iter8](http://github.com/iter8-tools) and
cannot run standalone. It should be installed either as part of Iter8
installation process or separately after Iter8 is installed.

## Getting started

### Run Iter8-trend
```
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

### Visualize trend
Iter8-trend implements a Prometheus scrape target, so its data can be collected
by Prometheus and visualized in Grafana. To enable your Prometheus to scrape
Iter8-trend, follow these [steps](docs/prometheus.md). Once this is completed,
follow these instructions:

First, we use `port-forward` to make Grafana available on `localhost:3000`:
```
kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=grafana -o jsonpath='{.items[0].metadata.name}') 3000:3000
```

Then, we import Iter8-trend dashboard in Grafana.
```
export DASHBOARD_DEFN=https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/iter8-trend.json
curl -s https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/install.sh \
| /bin/bash -
```

### Uninstall Iter8-trend
```
kubectl delete -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

## For developers

For developers who like to hack the code and/or build your own image from the code, follow these [instructions](docs/devs.md)
