JUPYTERHUB_VERSION = $(shell cat ../../jupyterhub_version.txt)
PACHYDERM_VERSION = $(shell cat ../../pachyderm_version.txt)

.PHONY: docker-build

docker-build:
	docker build --build-arg PACHYDERM_VERSION=$(PACHYDERM_VERSION) --tag pachyderm/jupyterhub-pachyderm-user:$(JUPYTERHUB_VERSION) .
	docker push pachyderm/jupyterhub-pachyderm-user:$(JUPYTERHUB_VERSION)
