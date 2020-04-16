#!/bin/bash

set -e

source ./etc/test_utils.sh

reset_minikube

# Make an initial deployment of pachyderm
print_section "Deploy pachyderm"
deploy_pachyderm

# Create a vanilla jupyterhub deployment, which employs the default
# (non-pachyderm) login mechanism
print_section "Create a base deployment of jupyterhub"
helm upgrade --install jhub jupyterhub/jupyterhub --version 0.8.2 --values ./etc/config/test_base.yaml
wait_for jupyterhub

# Patch in our custom user image
print_section "Patch in the user image"
python3 ./etc/existing_config.py patch > /tmp/patch-config.yaml
helm upgrade jhub --reuse-values -f ./etc/config/test_patch.yaml

wait_for jupyterhub
url=$(minikube service proxy-public --url | head -n 1)
python3 ./etc/test_e2e.py "${url}" "jovyan" "jupyter" --headless --no-auth-check

reset_minikube