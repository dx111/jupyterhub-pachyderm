#!/bin/bash

set -e

source ./etc/test_utils.sh

./etc/start_minikube.sh

# Make an initial deployment of pachyderm
print_section "Deploy pachyderm"
deploy_pachyderm

# Deploy jupyterhub
print_section "Deploy jupyterhub"
python3.7 init.py --use-version=local
test_run_with_auth

# Re-run jupyterhub deployment, should act as an upgrade and not error
# out
print_section "Upgrade jupyterhub"
python3.7 init.py --use-version=local
test_run_with_auth

# Undeploy jupyterhub
print_section "Undeploy"
./delete.sh

# Reset minikube fully and re-run the deployment/test cycle. This
# ensures that jupyterhub doesn't mistakenly pull in its old PV.
reset_minikube
print_section "Re-deploy pachyderm"
deploy_pachyderm
print_section "Re-deploy jupyterhub"
python3.7 init.py --use-version=local
test_run_with_auth

reset_minikube