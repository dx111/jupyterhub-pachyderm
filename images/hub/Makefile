VERSION = $(shell cat ../../jupyterhub_version.txt)

.PHONY: docker-build

docker-build:
	docker build --build-arg VERSION=$(VERSION) --tag ysimonson/jupyterhub-pachyderm-hub:$(VERSION) .
	docker push ysimonson/jupyterhub-pachyderm-hub:$(VERSION)
