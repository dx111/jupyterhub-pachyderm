# JupyterHub/Pachyderm Integration Guide

This repo walks you through getting JupyterHub integrated with Pachyderm on the same kubernetes cluster.

## Getting Started

1) [Deploy pachyderm](https://docs.pachyderm.com/latest/getting_started/local_installation/)
1) [Install helm](https://helm.sh/docs/using_helm/#installing-helm)
3) Run `./init.py`, which will deploy JupyterHub on the kubernetes cluster to work with Pachyderm. There are various options for debugging and configuring the deployment -- see `./init.py --help` for details.

## Advanced Configuration

Our `init.py` only provides basic configuration changes, but JupyterHub has a lot of knobs. See their [customization guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/index.html#customization-guide) for details.
