JUPYTERHUB_VERSION = $(shell jq -r .jupyterhub ../version.json)
VERSION ?= $(shell jq -r .ide ../version.json)

.PHONY: docker-build docker-push

docker-build:
	docker build --build-arg JUPYTERHUB_VERSION=$(JUPYTERHUB_VERSION) --tag pachyderm/ide-hub:$(VERSION) .

docker-push: docker-build
	docker push pachyderm/ide-hub:$(VERSION)
