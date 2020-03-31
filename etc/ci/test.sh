#!/bin/bash

set -ex

# Enable enterprise & auth
pachctl enterprise activate "${PACH_ENTERPRISE_CODE}"
echo admin | pachctl auth activate
pachctl auth whoami

# Deploy jupyterhub with native
${GOPATH}/bin/pachctl deploy jupyterhub

# Re-deploy with init
./init.py
