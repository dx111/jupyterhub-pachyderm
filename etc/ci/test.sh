#!/bin/bash

set -e

color_red='\033[0;31m'
color_none='\033[0m'

function print_section {
    echo -e "${color_red}${1}${color_none}"
}

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
    until timeout 1s ./etc/ci/check_ready.sh app=$1; do sleep 1; done
}

# Executes a test run
function test_run {
    wait_for jupyterhub
    # TODO: run through testing the login process via selenium/firefox
}

case "${VARIANT}" in
    native)
        image_version=$(jq -r .jupyterhub_pachyderm < version.json)

        print_section "Deploy pachyderm"
        deploy_pachyderm

        print_section "Deploy jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
        test_run

        print_section "Upgrade jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
        test_run

        print_section "Undeploy"
        echo yes | ${GOPATH}/bin/pachctl undeploy --jupyterhub --metadata

        print_section "Reset minikube"
        minikube delete
        sudo rm -rf /var/pachyderm
        ./etc/ci/start_minikube.sh

        print_section "Re-deploy pachyderm"
        deploy_pachyderm

        print_section "Re-deploy jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${image_version}"
        test_run
        ;;
    python)
        print_section "Deploy pachyderm"
        deploy_pachyderm

        print_section "Deploy jupyterhub"
        python3.7 init.py
        test_run

        print_section "Upgrade jupyterhub"
        python3.7 init.py
        test_run

        print_section "Undeploy"
        ./delete.sh

        print_section "Reset minikube and hostpaths"
        minikube delete
        sudo rm -rf /var/pachyderm
        ./etc/ci/start_minikube.sh

        print_section "Re-deploy pachyderm"
        deploy_pachyderm

        print_section "Re-deploy jupyterhub"
        python3.7 init.py
        test_run
        ;;
    existing)
        print_section "Create a base deployment of jupyterhub"
        python3 ./etc/ci/existing_config.py base > /tmp/base-config.yaml
        helm upgrade --install jhub jupyterhub/jupyterhub --version 0.8.2 --values /tmp/base-config.yaml
        wait_for jupyterhub

        print_section "Patch in the user image"
        python3 ./etc/ci/existing_config.py patch > /tmp/patch-config.yaml
        helm upgrade jhub jupyterhub/jupyterhub --version 0.8.2 --values /tmp/patch-config.yaml
        test_run

        print_section "Undeploy"
        ./delete.sh
        ;;
    *)
        echo "Unknown testing variant"
        exit 1
        ;;
esac
