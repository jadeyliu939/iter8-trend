# iter8-trend
Collects and visualize long-term canary trends

## Getting started

### Getting the code
```
git clone http://github.com/huang195/iter8-trend
cd iter8-trend/
```

### Build image
```
make docker-build
```

### Push image
```
make docker-push
```

### Run iter8-trend
#### In Kubernetes pod
```
kubectl -n iter8 apply -f install/kubernetes/iter8-trend.yml
```

#### As standalone process
```
./watcher.py
```

### Visualize
Import `grafana/iter8-trend.json` into the Grafana dashboard
