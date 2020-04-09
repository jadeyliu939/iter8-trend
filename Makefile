IMG ?= haih/iter8-trend:latest

docker-build:
	docker build . -t ${IMG}

docker-push:
	docker push ${IMG}
