#!/bin/bash

set -e

source ./etc/test_utils.sh

reset_minikube

# Make an initial deployment of pachyderm
print_section "Deploy pachyderm"
deploy_pachyderm

# Deploy jupyterhub
print_section "Deploy jupyterhub"
${GOPATH}/bin/pachctl deploy jupyterhub \
    --user-image "pachyderm/jupyterhub-pachyderm-user:local" \
    --hub-image "pachyderm/jupyterhub-pachyderm-hub:local"
test_run_with_auth

# Re-run jupyterhub deployment, should act as an upgrade and not error
# out
print_section "Upgrade jupyterhub"
${GOPATH}/bin/pachctl deploy jupyterhub \
    --user-image "pachyderm/jupyterhub-pachyderm-user:local" \
    --hub-image "pachyderm/jupyterhub-pachyderm-hub:local"
test_run_with_auth

# Undeploy everything, including jupyterhub
print_section "Undeploy"
echo yes | ${GOPATH}/bin/pachctl undeploy --jupyterhub --metadata

# Reset minikube fully and re-run the deployment/test cycle. This
# ensures that jupyterhub doesn't mistakenly pull in its old PV.
reset_minikube
print_section "Re-deploy pachyderm"
deploy_pachyderm
print_section "Re-deploy jupyterhub"
${GOPATH}/bin/pachctl deploy jupyterhub \
    --user-image "pachyderm/jupyterhub-pachyderm-user:local" \
    --hub-image "pachyderm/jupyterhub-pachyderm-hub:local"
test_run_with_auth

reset_minikube