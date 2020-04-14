PACHCTL_VERSION = $(shell jq -r .pachctl ../../version.json)
VERSION = $(shell jq -r .user_image ../../version.json)

.PHONY: docker-build docker-push dev-build server

docker-build:
	docker build --build-arg PACHCTL_VERSION=$(PACHCTL_VERSION) --tag pachyderm/jupyterhub-pachyderm-user:$(VERSION) .

docker-push: docker-build
	docker push pachyderm/jupyterhub-pachyderm-user:$(VERSION)

dev-build:
	jlpm watch

dev-server:
	jupyter lab --watch
