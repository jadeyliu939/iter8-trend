## For developers

For developers who like to hack the code and/or build your own image from the code, follow these instructions

### Getting the code
```
git clone http://github.com/iter8-tools/iter8-trend
```

### Build image
While in `iter8-trend` directory:
```
make docker-build
```

### Push image
While in `iter8-trend` directory:
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
./iter8-trend.py
```
