# JupyterHub/Pachyderm Integration Guide

This guide provides information and scripts for getting JupyterHub integrated with Pachyderm on the same kubernetes cluster. When auth is enabled on your Pachyderm cluster, JupyterHub will use it for auth. Python notebooks will also have built-in access to [Pachyderm's python client library](https://github.com/pachyderm/python-pachyderm).

## Getting Started

1) [Deploy pachyderm](https://docs.pachyderm.com/latest/getting_started/local_installation/)
2) [Install helm](https://helm.sh/docs/using_helm/#installing-helm)
3) Run `./init.py`, which will deploy JupyterHub on the kubernetes cluster to work with Pachyderm. There are various options for debugging and configuring the deployment -- see `./init.py --help` for details.

After `init.py` completes, JupyterHub should be accesible within a couple of minutes. It should be reachable on port 80 of your cluster's hostname. To authenticate on JupyterHub:

- If auth is enabled on the Pachyderm cluster, use a github or OTP auth token for your password. Your JupyterHub username will be the same as your Pachyderm username.
- If auth is not enabled, `init.py` will have printed a global password for you to use to authenticate. Your JupyterHub username will be whatever you set when logging in.

## Advanced Configuration

Our `init.py` only provides basic configuration changes, but JupyterHub has a lot of knobs. See their [customization guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html#customization-guide) for details.

## Troubleshooting

### Cannot reach JupyterHub

If `init.py` finished successfully but you're having trouble getting to JupyterHub, ensure you've followed the cloud-specific instructions in [JupyterHub's setup guides](https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html).

### Cannot authenticate

If you cannot authenticate even though you're passing the correct credentials, check the pod logs for hub. You'll likely see an error caused by a misconfiguration. Misconfigurations can happen from either passing in incorrect values to `init.py`, or if the cluster has changed since JupyterHub was last deployed (e.g. if auth was enabled, or if the Pachyderm auth token used by JupyterHub has expired) -- in either case, re-deploying can fix the issue.
