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
