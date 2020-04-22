# Advanced Setup Guide

If `pachctl deploy jupyterhub` does not offer the level customization you need for your JupyterHub deployment, you can manually install it by following the [zero to JupyterHub guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html). It should be installed on the same cluster as Pachyderm. 

Create a Helm `config.yaml` by running `pachctl deploy jupyterhub --dry-run`, it should output something like this:

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

Modify it with whatever customizations you wish, then save it to `config.yaml`.

1) If you're doing a new installation of JupyterHub, run `helm install jhub jupyterhub/jupyterhub --version=0.8.2 -f config.yaml`.
2) If you want to just change the config in an existing JupyterHub installation, run `helm upgrade jhub --reuse-values -f config.yaml`.
