#!/bin/bash

# Pushes our jupyterhub-pachyderm images, built locally, to a minikube
# instance

set -ex

./etc/start_minikube.sh

pushd images/hub
    make docker-build
popd

pushd images/user
    make docker-build
popd
