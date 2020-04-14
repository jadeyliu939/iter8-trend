## Prometheus
This section describes how to configure your Prometheus instance to scrape Iter8-trend data.

### Istio

If you are running Istio in your cluster, it already has its own Prometheus
instance. This section describes how to configure Prometheus instance that came
with Istio to collect Iter8-trend data.

1. This Prometheus instance uses a configuration file instantiated from a
Kubernetes configmap. We need to add a new scrape target in the configuration
file. This can be achieved by editing the configmap.
```
kubectl -n istio-system edit configmap prometheus
```
in the list of jobs, copy and paste the following to this list
```
    - job_name: 'iter8_trend'
      static_configs:
      - targets: ['iter8-trend.iter8:8888']
```

2. The Prometheus instance in Istio is configured to only retain 6 hours of data
(Prometheus's default is 15 days). As we are interested in long term trends, we
need to retain data for longer period of time. A caveat is with longer retention
period, Prometheus instance would require more resources to run, which is beyond
the scope of the instructions here. If developers/product managers are
interested in retaining 1 week of data, he can edit the Prometheus deployment:
```
kubectl -n istio-system edit deployment prometheus
```
and modify the retention period parameter as follows:
```
      containers:
      - args:
        - --storage.tsdb.retention=1w
```
These actions will trigger a new Prometheus pod to be deployed, which will pick
up the changes we made in the configmap, thus will start scraping Iter8-trend
data immediately.
