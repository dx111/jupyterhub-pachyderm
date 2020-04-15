#!/bin/bash

set -ex

if [ "$TRAVIS" = "true" ]; then
    # Repeatedly restart minikube until it comes up. This corrects for an issue in
    # Travis, where minikube will get stuck on startup and never recover
    while true; do
        sudo env "PATH=$PATH" "CHANGE_MINIKUBE_NONE_USER=true" minikube start -vm-driver=none
        HEALTHY=false
        # Try to connect for one minute
        for _ in $(seq 12); do
            if {
                kubectl version 2>/dev/null >/dev/null
            }; then
                HEALTHY=true
                break
            fi
            sleep 5
        done
        if [ "${HEALTHY}" = "true" ]; then break; fi

        # Give up--kubernetes isn't coming up
        minikube delete
        sleep 10 # Wait for minikube to go completely down
    done
else
    minikube start
fi
