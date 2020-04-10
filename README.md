# iter8-trend
This is an optional component to [Iter8](http://github.com/iter8-tools) and cannot run standalone. It should be installed either as part of Iter8 installation process or separately after Iter8 is installed.

## Getting started

### Run iter8-trend
```
kubectl apply -f https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/install/kubernetes/iter8-trend.yaml
```

### Visualize trend
```
export DASHBOARD_DEFN=https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/iter8-trend.json
curl -s https://raw.githubusercontent.com/iter8-tools/iter8-trend/master/grafana/install.sh \
| /bin/bash -
```

## For developers

For developers who like to hack the code and/or build your own image from the code, follow these [instructions](docs/devs.md)
