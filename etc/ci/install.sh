#!/bin/bash

set -ex

# Install base deps
sudo apt-get update
sudo apt-get install -y -qq \
    jq \
    python3 \
    python3-pip \
    python3-setuptools \
    pkg-config

# Install aws CLI (for TLS test)
pip3 install --upgrade --user wheel
pip3 install --upgrade --user awscli

# Install pachctl
curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v$(PACHYDERM_VERSION)/pachctl_$(PACHYDERM_VERSION)_amd64.deb  && \
sudo dpkg -i /tmp/pachctl.deb

# Install kubectl
# To get the latest kubectl version:
# curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt
if [ ! -f ~/cached-deps/kubectl ] ; then
    KUBECTL_VERSION=v1.13.0
    curl -L -o kubectl https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl && \
        chmod +x ./kubectl && \
        mv ./kubectl ~/cached-deps/kubectl
fi

# Install minikube
# To get the latest minikube version:
# curl https://api.github.com/repos/kubernetes/minikube/releases | jq -r .[].tag_name | sort | tail -n1
if [ ! -f ~/cached-deps/minikube ] ; then
    MINIKUBE_VERSION=v0.31.0
    curl -L -o minikube https://storage.googleapis.com/minikube/releases/${MINIKUBE_VERSION}/minikube-linux-amd64 && \
        chmod +x ./minikube && \
        mv ./minikube ~/cached-deps/minikube
fi
