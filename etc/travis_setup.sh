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

hub_image_version=$(jq -r .hub_image < version.json)
./etc/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-hub:${hub_image_version}
user_image_version=$(jq -r .user_image < version.json)
./etc/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-user:${user_image_version}
