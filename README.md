# Iter8-trend
This is an optional component to [Iter8](http://github.com/iter8-tools) and
cannot run standalone. It should be installed either as part of Iter8
installation process or separately after Iter8 is installed.

## Getting started

Watch the following short video to get started:

[![Short Video](https://img.youtube.com/vi/FOtyqJPMj14/hqdefault.jpg)](https://youtu.be/FOtyqJPMj14)

### Install
```
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

### Visualization
Iter8-trend implements a Prometheus scrape target, so summarized metric data can
be collected by Prometheus and visualized in Grafana. To enable Prometheus to
scrape Iter8-trend, you need to add a new scrape target to Prometheus
configuration, e.g., in Istio, you do the following:

```
kubectl -n istio-system edit configmap prometheus
```

In the list of jobs, copy and paste the following at the bottom of the job list:

```
    - job_name: 'iter8_trend'
      static_configs:
      - targets: ['iter8-trend.iter8:8888']
```

and then restart the Prometheus pod for the change to take effect:

```
kubectl -n istio-system delete pod prometheus-xxx-yyy
```

Then, we use `port-forward` to make Grafana available on `localhost:3000`:
```
kubectl -n istio-system port-forward $(kubectl -n istio-system get pod -l app=grafana -o jsonpath='{.items[0].metadata.name}') 3000:3000
```

Finally, we import Iter8-trend dashboard in Grafana.
```
export DASHBOARD_DEFN=https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/iter8-trend.json
curl -Ls https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/install.sh \
| /bin/bash -
```

### Uninstall
```
kubectl delete -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

## For Developers

For developers who like to hack the code and/or build your own image from the code, follow these [instructions](docs/devs.md)
