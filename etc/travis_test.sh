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

# Executes a test run
function test_run {
    wait_for jupyterhub
    url=$(minikube service proxy-public --url | head -n 1)
    python3 ./etc/test.py "${url}" "${1-}" "${2-$(pachctl auth get-otp)}" --headless
}

# Make an initial deployment of pachyderm
print_section "Deploy pachyderm"
deploy_pachyderm

case "${VARIANT}" in
    native)
        hub_image_version=$(jq -r .hub_image < version.json)
        user_image_version=$(jq -r .user_image < version.json)

        # Deploy jupyterhub
        print_section "Deploy jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${user_image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${hub_image_version}"
        test_run

        # Re-run jupyterhub deployment, should act as an upgrade and not error
        # out
        print_section "Upgrade jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${user_image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${hub_image_version}"
        test_run

        # Undeploy everything, including jupyterhub
        print_section "Undeploy"
        echo yes | ${GOPATH}/bin/pachctl undeploy --jupyterhub --metadata

        # Reset minikube fully and re-run the deployment/test cycle. This
        # ensures that jupyterhub doesn't mistakenly pull in its old PV.
        print_section "Reset minikube"
        minikube delete
        sudo rm -rf /var/pachyderm # delete the pachyderm hostpath
        ./etc/start_minikube.sh
        print_section "Re-deploy pachyderm"
        deploy_pachyderm
        print_section "Re-deploy jupyterhub"
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image "pachyderm/jupyterhub-pachyderm-user:${user_image_version}" \
            --hub-image "pachyderm/jupyterhub-pachyderm-hub:${hub_image_version}"
        test_run
        ;;
    python)
        # Deploy jupyterhub
        print_section "Deploy jupyterhub"
        python3.7 init.py --legacy-ui
        test_run

        # Re-run jupyterhub deployment, should act as an upgrade and not error
        # out
        print_section "Upgrade jupyterhub"
        python3.7 init.py --legacy-ui
        test_run

        # Undeploy jupyterhub
        print_section "Undeploy"
        ./delete.sh

        # Reset minikube fully and re-run the deployment/test cycle. This
        # ensures that jupyterhub doesn't mistakenly pull in its old PV.
        print_section "Reset minikube and hostpaths"
        minikube delete
        sudo rm -rf /var/pachyderm # delete the pachyderm hostpath
        ./etc/start_minikube.sh
        print_section "Re-deploy pachyderm"
        deploy_pachyderm
        print_section "Re-deploy jupyterhub"
        python3.7 init.py --legacy-ui
        test_run
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
        test_run jovyan jupyter
        ;;
    *)
        echo "Unknown testing variant"
        exit 1
        ;;
esac
