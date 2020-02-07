PACHYDERM_VERSION = $(shell jq -r .pachyderm ../../version.json)
VERSION = $(shell jq -r .jupyterhub_pachyderm ../../version.json)

.PHONY: docker-build

docker-build:
	docker build --build-arg PACHYDERM_VERSION=$(PACHYDERM_VERSION) --tag pachyderm/jupyterhub-pachyderm-user:$(VERSION) .
	docker push pachyderm/jupyterhub-pachyderm-user:$(VERSION)
