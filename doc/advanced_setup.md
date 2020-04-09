# Advanced Setup Guide

If `init.py` does not offer the level customization you need for your JupyterHub deployment, you can manually install it by following the [zero to JupyterHub guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html). It should be installed on the same cluster as Pachyderm. 

Create a Helm `config.yaml` by running `./init.py --dry-run`, it should output something like this:

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

Modify it with whatever customizations you wish, then use `helm install` or `helm upgrade` with that config to install JupyterHub.
