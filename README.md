# iter8-trend
This is an optional component to [Iter8](http://github.com/iter8-tools) and cannot run standalone. It should be installed either as part of Iter8 installation process or separately after Iter8 is installed.

## Getting started

### Run iter8-trend
```
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

### Visualize trend
Iter8-trend implements a Prometheus scrape target, so its data can be collected by Prometheus and visualized in Grafana. To enable your Prometheus to scrape Iter8-trend, follow these [steps](docs/prometheus.md). Once this is completed, follow these instructions to import Iter8-trend dashboard in Grafana:

```
export DASHBOARD_DEFN=https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/iter8-trend.json
curl -s https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/install.sh \
| /bin/bash -
```

## For developers

For developers who like to hack the code and/or build your own image from the code, follow these [instructions](docs/devs.md)
