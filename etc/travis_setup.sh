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

image_version=$(jq -r .jupyterhub_pachyderm < version.json)
./etc/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-hub:${image_version}
./etc/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-user:${image_version}
