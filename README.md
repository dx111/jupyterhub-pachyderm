# JupyterHub/Pachyderm Integration

This repo contains everything necessary for getting JupyterHub running and well-integrated with [Pachyderm](https://github.com/pachyderm/pachyderm). With this, you can get JupyterHub running on the same Kubernetes cluster as Pachyderm, as well as:

- Seamless authentication with Pachyderm: you login to JupyterHub with your Pachyderm credentials.
- Built-in support for Pachyderm interactivity in Python notebooks via our official Python client library, [python-pachyderm](https://github.com/pachyderm/python-pachyderm/).
- Built-in support for `pachctl`, available in the JupyterHub terminal.

Note that this is an Pachyderm enterprise-only feature, and will not work otherwise.

## Supported Platforms

Tested on these platforms:

* GKE (kubernetes 1.13)
* EKS (kubernetes 1.13)
* Docker for mac (kubernetes 1.14)

This is currently known not to work on kubernetes 1.16-based environments (including minikube.)

## Deploying JupyterHub

### Prerequisites

1) [Deploy pachyderm](https://docs.pachyderm.com/latest/getting_started/local_installation/).
2) [Install helm 3](https://helm.sh/docs/using_helm/#installing-helm).

### Install

We provide a helper script (`init.py`) for easing JupyterHub deployments. It sets reasonable defaults for JupyterHub, and has a few options for debugging and configuration (see `./init.py --help` for details.)

1) Run `./init.py`.
2) If there's a firewall between you and the kubernetes cluster, make sure to punch a hole so you can connect to port 80 on it. [See cloud-specific instructions here.](https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html)

If you need to customize your JupyterHub deployment more than what `init.py` offers, see our [advanced setup guide.](doc/advanced_setup.md)

## Using JupyterHub

Once deployed, navigate to your JupyterHub instance:

- By default, it should be reachable on port 80 of your cluster's hostname.
- On minikube, navigate to one of the URLs printed out when you run `minikube service proxy-public --url`.

You should reach a login page; if you don't, see the troubleshooting section below. Now login by using your pachyderm github or OTP auth token for your password. Your JupyterHub username will be the same as your Pachyderm username.

Once you're logged in, you should be able to connect to the Pachyderm cluster from within a JupyterHub notebook; e.g., if Pachyderm auth is enabled, try this:

```python
import python_pachyderm
client = python_pachyderm.Client.new_in_cluster()
print(client.who_am_i())
```

Notice that, without configuration:

1) `python_pachyderm` is already installed.
2) The username for `who_am_i()` is the same as your JupyterHub login username.

For a more advanced example, see our [opencv walkthrough](doc/opencv.md).

## Troubleshooting

### Cannot reach JupyterHub

If `init.py` finished successfully but you're having trouble getting to JupyterHub, ensure you've followed the cloud-specific instructions in [JupyterHub's setup guides](https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html).

### Getting "Service Unavailable" errors when connecting

It may take a couple of minutes for JupyterHub to get fully up and running. Keep an eye on `kubectl` logs for errors in the hub pod.

### Cannot authenticate to JupyterHub

If you cannot authenticate even though you're passing the correct credentials, check the pod logs for hub. You'll likely see an error caused by a misconfiguration. Misconfigurations can happen from either passing in incorrect values to `init.py`, or if the cluster has changed since JupyterHub was last deployed (e.g. if auth was enabled, or if the Pachyderm auth token used by JupyterHub has expired) -- in either case, re-deploying can fix the issue.

### Cannot connect to Pachyderm in Jupyter notebooks

In Jupyter notebooks, make sure you're using `python_pachyderm.Client.new_in_cluster()` to create a client -- this will ensure the client is automatically configured to work with the Pachyderm cluster, which should be running in the same Kubernetes cluster as JupyterHub.

### Cannot authenticate to Pachyderm in Jupyter notebooks

When you create a `python_pachyderm.Client` in a Jupyter notebook, it should automatically be setup to use an auth token tied to the logged-in JupyterHub user. If you're able to connect but not authenticate:

- If you're passing in an `auth_token` to the `Client`, make sure it's valid.
- If you aren't passing in an `auth_token`, try logging out, deleting the JupyterHub user pod (it should look something like `pod/jupyter-github-3aysimonson`), and logging back in. It's possible that the auth state has been corrupted or lost.
