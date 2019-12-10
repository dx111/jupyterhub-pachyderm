VERSION = $(shell cat ../../jupyterhub_version.txt)

.PHONY: docker-build

docker-build:
	docker build --tag ysimonson/jupyterhub-pachyderm-user:$(VERSION) .
	docker push ysimonson/jupyterhub-pachyderm-user:$(VERSION)
