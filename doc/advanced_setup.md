# Advanced Setup Guide

If `init.py` doesn't offer the level customization you need for your JupyterHub deployment, manually install it by following the [zero to JupyterHub guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html). It should be installed on the same cluster as Pachyderm. You'll need to change some of the values of your Helm `config.yaml` depending on whether auth is enabled on your Pachyderm cluster.

## Auth Enabled

If auth is enabled on your Pachyderm cluster and you want to use Pachyderm auth in JupyterHub, ensure `config.yaml` has something like this:

```yaml
hub:
  image:
    name: pachyderm/jupyterhub-pachyderm-hub
    tag: "0.8.2"
singleuser:
  image:
    name: pachyderm/jupyterhub-pachyderm-user
    tag: "0.8.2"
auth:
  state:
    enabled: true
    cryptoKey: "{some random string}"
  type: custom
  custom:
    className: pachyderm_authenticator.PachydermAuthenticator
    config:
      pach_auth_token: "{pachyderm admin auth token}"
      pach_tls_certs: "{pachyderm TLS certificates}"
      global_password: "{some random string}"
```

## Auth Disabled

If auth is not enabled on your Pachyderm cluster, or you don't want to use Pachyderm auth in JupyterHub, you only need to override the singleuser image, like so:

```yaml
singleuser:
  image:
    name: pachyderm/jupyterhub-pachyderm-user
    tag: "0.8.2"
```
