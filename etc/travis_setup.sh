#!/bin/bash

# Pushes our jupyterhub-pachyderm images, built locally, to a minikube
# instance

set -ex

./etc/start_minikube.sh

pushd images/hub
    VERSION=local make docker-build
popd

pushd images/user
    VERSION=local make docker-build
popd
