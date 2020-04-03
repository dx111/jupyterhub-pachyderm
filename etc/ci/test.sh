#!/bin/bash

set -ex

function wait_for_jupyterhub {
    until timeout 1s ./etc/ci/check_ready.sh app=jupyterhub; do sleep 1; done
}

function test_run {
    wait_for_jupyterhub
    # TODO: run through testing the login process via selenium/firefox
}

pushd images/hub
    make docker-build
popd

pushd images/user
    make docker-build
popd

image_version=$(jq -r .jupyterhub_pachyderm < version.json)
./etc/ci/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-hub:${image_version}
./etc/ci/push-to-minikube.sh pachyderm/jupyterhub-pachyderm-user:${image_version}

case "${VARIANT}" in
    native)
        # Install pachctl with native support
        # TODO:remove once native jupyterhub deployments are stable
        pushd ~
            git clone --single-branch --branch native-jupyterhub --depth 1 https://github.com/pachyderm/pachyderm.git
            pushd pachyderm
                make install
            popd
        popd

        # Deploy
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image pachyderm/jupyterhub-pachyderm-user:${image_version} \
            --hub-image pachyderm/jupyterhub-pachyderm-hub:${image_version}

        test_run

        # Re-deploy
        ${GOPATH}/bin/pachctl deploy jupyterhub \
            --user-image pachyderm/jupyterhub-pachyderm-user:${image_version} \
            --hub-image pachyderm/jupyterhub-pachyderm-hub:${image_version}

        test_run

        # Undeploy
        echo yes | ${GOPATH}/bin/pachctl undeploy --jupyterhub
        ;;
    python)
        # Deploy
        python3.7 init.py
        test_run

        # Re-deploy
        python3.7 init.py
        test_run

        # Undeploy
        ./delete.sh
        ;;
    existing)
        # Create a base deploy
        python3 ./etc/ci/existing_config.py base \
            | helm upgrade --install jhub jupyterhub/jupyterhub --version 0.8.2 --values -
        wait_for_jupyterhub

        # Patch in the user image
        python3 ./etc/ci/existing_config.py patch \
            | helm upgrade jhub jupyterhub/jupyterhub --version 0.8.2 --values -
        wait_for_jupyterhub

        # Undeploy
        ./delete.sh
        ;;
    *)
        echo "Unknown testing variant"
        exit 1
        ;;
esac
