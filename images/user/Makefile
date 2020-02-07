VERSION = $(shell cat ../../jupyterhub_version.txt)

.PHONY: docker-build

docker-build:
	docker build --tag pachyderm/jupyterhub-pachyderm-user:$(VERSION) .
	docker push pachyderm/jupyterhub-pachyderm-user:$(VERSION)
