#!/bin/bash

set -ex

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
