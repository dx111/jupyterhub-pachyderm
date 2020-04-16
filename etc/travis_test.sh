#!/bin/bash

set -e

# Use virtualenv
source ~/cached-deps/venv/bin/activate

case "${VARIANT}" in
    native)
        ./etc/test_native.sh
        ;;
    python)
        ./etc/test_python.sh
        ;;
    existing)
        ./etc/test_existing.sh
        ;;
    *)
        echo "Unknown testing variant"
        exit 1
        ;;
esac
