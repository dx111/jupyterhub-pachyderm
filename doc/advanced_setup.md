# Advanced Setup Guide

If `pachctl deploy ide` does not offer the level customization you need, you can manually install it by following the [zero to JupyterHub guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html). It should be installed on the same cluster as Pachyderm.

Create a Helm `config.yaml` by running `pachctl deploy ide --dry-run`, it should output something like this:

```yaml
hub:
  image:
    name: "pachyderm/ide-hub"
    tag: "1.0.0"
singleuser:
  image:
    name: "pachyderm/ide-user"
    tag: "1.0.0"
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

Modify it with whatever customizations you wish, then save it to `config.yaml` and run `helm upgrade --install pachyderm-ide jupyterhub/jupyterhub --version=0.8.2 -f config.yaml`.
