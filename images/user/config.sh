#!/bin/bash
echo "{\"pachd_address\": \"$PACHD_SERVICE_HOST:$PACHD_SERVICE_PORT\"}" | pachctl config set context in-cluster
pachctl config set active-context in-cluster
echo $1 | pachctl auth use-auth-token
