#!/usr/bin/env python3

# test utility script for generating helm configs that simulate an existing
# jupyterhub deployment

import sys
import json

BASE_CONFIG = """
proxy:
  secretToken: "7509f6a7cc1da6167b98af5c0bbea97a"
"""

PATCH_CONFIG = """
singleuser:
  image:
    name: pachyderm/jupyterhub-pachyderm-user
    tag: "{version}"
"""

if __name__ == "__main__":
    # get the version
    with open("version.json", "r") as f:
        j = json.load(f)
        version = j["jupyterhub_pachyderm"]

    action = sys.argv[1]
    config = BASE_CONFIG

    if action == "base":
        # nothing to do
        pass
    elif action == "patch":
        config += PATCH_CONFIG.format(version=version)
    else:
        raise Exception("unknown action: {}".format(action))

    print(config)
