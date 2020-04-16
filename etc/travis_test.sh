#!/bin/bash

set -e

color_red='\033[0;31m'
color_none='\033[0m'

function print_section {
    echo -e "${color_red}${1}${color_none}"
}

# Use virtualenv
source ~/cached-deps/venv/bin/activate

# Deploys pachyderm and activates enterprise+auth
function deploy_pachyderm {
    /usr/bin/pachctl deploy local -d
    wait_for pachd
    /usr/bin/pachctl version

    /usr/bin/pachctl enterprise activate "${PACH_ENTERPRISE_CODE}"
    echo admin | /usr/bin/pachctl auth activate
    /usr/bin/pachctl auth whoami
}

# Waits for a given app to be ready
function wait_for {
    until timeout 1s ./etc/check_ready.sh app=$1; do sleep 1; done
}

# Executes a test run with pachyderm auth
function test_run_with_auth {
    wait_for jupyterhub
    url=$(minikube service proxy-public --url | head -n 1)
    python3 ./etc/test_e2e.py "${url}" "github:admin" "$(pachctl auth get-otp)" --headless
}

# Deletes and restarts minikube
function reset_minikube {
    minikube delete
    sudo rm -rf /var/pachyderm # delete the pachyderm hostpath
    ./etc/start_minikube.sh
}

# Make an initial deployment of pachyderm
print_section "Deploy pachyderm"
reset_minikube
deploy_pachyderm

case "${VARIANT}" in
    native)
        image_version=$(jq -r .jupyterhub_pachyderm < version.json)

        # Deploy jupyterhub
        print_section "Deploy jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
        test_run_with_auth

        # Re-run jupyterhub deployment, should act as an upgrade and not error
        # out
        print_section "Upgrade jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
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
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
        test_run_with_auth
        ;;
    python)
        # Deploy jupyterhub
        print_section "Deploy jupyterhub"
        python3.7 init.py
        test_run_with_auth

        # Re-run jupyterhub deployment, should act as an upgrade and not error
        # out
        print_section "Upgrade jupyterhub"
        python3.7 init.py
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
        python3.7 init.py
        test_run_with_auth
        ;;
    existing)
        # Create a vanilla jupyterhub deployment, which employs the default
        # (non-pachyderm) login mechanism
        print_section "Create a base deployment of jupyterhub"
        python3 ./etc/existing_config.py base > /tmp/base-config.yaml
        helm upgrade --install jhub jupyterhub/jupyterhub --version 0.8.2 --values /tmp/base-config.yaml
        wait_for jupyterhub

        # Patch in our custom user image
        print_section "Patch in the user image"
        python3 ./etc/existing_config.py patch > /tmp/patch-config.yaml
        helm upgrade jhub jupyterhub/jupyterhub --version 0.8.2 --values /tmp/patch-config.yaml

        wait_for jupyterhub
        url=$(minikube service proxy-public --url | head -n 1)
        python3 ./etc/test_e2e.py "${url}" "jovyan" "jupyter" --headless --no-auth-check
        ;;
    *)
        echo "Unknown testing variant"
        exit 1
        ;;
esac
