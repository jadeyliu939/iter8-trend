# Iter8-trend 
This is an optional component to [Iter8](http://github.com/iter8-tools) and
cannot run standalone. It should be installed either as part of Iter8
installation process or separately after Iter8 is installed.

## Getting started

### Run Iter8-trend
```
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/v0.2/install/kubernetes/iter8-trend.yaml
```

### Visualize trend
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
curl -Ls https://raw.githubusercontent.com/iter8-tools/iter8-trend/v0.2/grafana/install.sh \
| DASHBOARD_DEFN=https://raw.githubusercontent.com/iter8-tools/iter8-trend/v0.2/grafana/iter8-trend.json /bin/bash -
```

### Uninstall Iter8-trend
```
kubectl delete -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/v0.2/install/kubernetes/iter8-trend.yaml
```

## For developers

For developers who like to hack the code and/or build your own image from the code, follow these [instructions](docs/devs.md)
