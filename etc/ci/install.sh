#!/bin/bash

set -ex

# Install base deps
sudo apt-get update
sudo apt-get install -y -qq jq

# Install pachctl
pachyderm_version=$(jq -r .pachctl < version.json)
curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${pachyderm_version}/pachctl_${pachyderm_version}_amd64.deb  && \
sudo dpkg -i /tmp/pachctl.deb

# Install kubectl
# To get the latest kubectl version:
# curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt
if [ ! -f ~/cached-deps/kubectl ] ; then
    kubectl_version=v1.13.0
    curl -L -o kubectl https://storage.googleapis.com/kubernetes-release/release/${kubectl_version}/bin/linux/amd64/kubectl && \
        chmod +x ./kubectl && \
        mv ./kubectl ~/cached-deps/kubectl
fi

# Install minikube
# To get the latest minikube version:
# curl https://api.github.com/repos/kubernetes/minikube/releases | jq -r .[].tag_name | sort | tail -n1
if [ ! -f ~/cached-deps/minikube ] ; then
    minikube_version=v0.31.0
    curl -L -o minikube https://storage.googleapis.com/minikube/releases/${minikube_version}/minikube-linux-amd64 && \
        chmod +x ./minikube && \
        mv ./minikube ~/cached-deps/minikube
fi
