PACHCTL_VERSION = $(shell jq -r .pachctl ../version.json)
VERSION ?= $(shell jq -r .jupyterhub_pachyderm ../version.json)
.PHONY: docker-build docker-push

docker-build:
	docker build --build-arg PACHCTL_VERSION=$(PACHCTL_VERSION) --tag pachyderm/jupyterhub-pachyderm-user:$(VERSION) .

docker-push: docker-build
	docker push pachyderm/jupyterhub-pachyderm-user:$(VERSION)
