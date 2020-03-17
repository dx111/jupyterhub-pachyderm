JUPYTERHUB_VERSION = $(shell jq -r .jupyterhub ../../version.json)
VERSION = $(shell jq -r .hub_image ../../version.json)

.PHONY: docker-build docker-push

docker-build:
	docker build --build-arg JUPYTERHUB_VERSION=$(JUPYTERHUB_VERSION) --tag pachyderm/jupyterhub-pachyderm-hub:$(VERSION) .

docker-push: docker-build
	docker push pachyderm/jupyterhub-pachyderm-hub:$(VERSION)
