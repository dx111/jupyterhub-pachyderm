# JupyterHub/Pachyderm Integration Guide

This guide provides information and scripts for getting JupyterHub integrated with Pachyderm on the same kubernetes cluster. When auth is enabled on your Pachyderm cluster, JupyterHub will use it for auth. Python notebooks will also have built-in access to [Pachyderm's python client library](https://github.com/pachyderm/python-pachyderm).

To deploy JupyterHub:

1) [Deploy pachyderm](https://docs.pachyderm.com/latest/getting_started/local_installation/).
2) [Install helm](https://helm.sh/docs/using_helm/#installing-helm).
3) Run `./init.py`, which will deploy JupyterHub on the kubernetes cluster to work with Pachyderm. There are various options for debugging and configuring the deployment -- see `./init.py --help` for details.

JupyterHub should now be reachable on port 80 of your cluster's hostname. If you navigate to it, you may get a `Service Unavailable` error for a couple of minutes while JupyterHub finishes spinning up.

To authenticate on JupyterHub:

- If auth is enabled on the Pachyderm cluster, use a github or OTP auth token for your password. Your JupyterHub username will be the same as your Pachyderm username.
- If auth is not enabled, `init.py` will have printed a global password for you to use to authenticate. Your JupyterHub username will be whatever you set when logging in.

Once you're logged in, you should be able to connect to the Pachyderm cluster from within a JupyterHub notebook; e.g., if Pachyderm auth is enabled, try this:

```python
import python_pachyderm
client = python_pachyderm.Client.new_in_cluster()
print(client.who_am_i())
```

Notice that, without configuration:

1) `python_pachyderm` is already installed.
2) The username for `who_am_i()` is the same as your JupyterHub login username.

## Advanced Configuration

Our `init.py` only provides basic configuration changes, but JupyterHub has a lot of knobs. See their [customization guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html#customization-guide) for details.

## Troubleshooting

### Cannot reach JupyterHub

If `init.py` finished successfully but you're having trouble getting to JupyterHub, ensure you've followed the cloud-specific instructions in [JupyterHub's setup guides](https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html).

### Cannot authenticate to JupyterHub

If you cannot authenticate even though you're passing the correct credentials, check the pod logs for hub. You'll likely see an error caused by a misconfiguration. Misconfigurations can happen from either passing in incorrect values to `init.py`, or if the cluster has changed since JupyterHub was last deployed (e.g. if auth was enabled, or if the Pachyderm auth token used by JupyterHub has expired) -- in either case, re-deploying can fix the issue.

### Cannot connect to Pachyderm in Jupyter notebooks

In Jupyter notebooks, make sure you're using `python_pachyderm.Client.new_in_cluster()` to create a client -- this will ensure the client is automatically configured to work with the Pachyderm cluster, which should be running in the same Kubernetes cluster as JupyterHub.

### Cannot authenticate to Pachyderm in Jupyter notebooks

When you create a `python_pachyderm.Client` in a Jupyter notebook, it should automatically be setup to use an auth token tied to the logged-in JupyterHub user. If you're able to connect but not authenticate:

- If you're passing in an `auth_token` to the `Client`, make sure it's valid.
- If you aren't passing in an `auth_token`, try logging out, deleting the JupyterHub user pod (it should look something like `pod/jupyter-github-3aysimonson`), and logging back in. It's possible that the auth state has been corrupted or lost.
