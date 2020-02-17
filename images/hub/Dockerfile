ARG JUPYTERHUB_VERSION
FROM jupyterhub/k8s-hub:$JUPYTERHUB_VERSION

USER root
COPY authenticator /tmp/authenticator
WORKDIR /tmp/authenticator
RUN pip3 install git+https://github.com/pachyderm/python-pachyderm.git@use-pachd-peer-service
RUN pip3 install .

USER ${NB_USER}
WORKDIR /srv/jupyterhub
