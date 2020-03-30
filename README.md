# iter8-trend
Collects and visualize long-term canary trends

## Getting started

### Getting the code
```
git clone http://github.com/huang195/iter8-trend
cd iter8-trend/
```

### Building image
```
./build.sh
```

### Run
```
kubectl -n iter8 apply -f install/deployment.yml
```

### Visualize
Import `grafana/iter8-trend.json` into the Grafana dashboard
