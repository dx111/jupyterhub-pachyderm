#!/bin/bash

set -ex

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
 NATIVE)
    # Install pachctl with native support
    # TODO:remove once native jupyterhub deployments are stable
    pushd ~
      git clone --single-branch --branch native-jupyterhub --depth 1 https://github.com/pachyderm/pachyderm.git
      pushd pachyderm
        make install
      popd
    popd

    # Deploy with pachctl
    ${GOPATH}/bin/pachctl deploy jupyterhub
    ;;
 INIT)
    # Deploy with init.py
    ./init.py
    ;;
 *)
    echo "Unknown testing variant"
    exit 1
    ;;
esac

until timeout 1s ./etc/ci/check_ready.sh app=jupyterhub; do sleep 1; done

# TODO: run through testing the login process via selenium/firefox
