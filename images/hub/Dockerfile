ARG JUPYTERHUB_VERSION
FROM jupyterhub/k8s-hub:$JUPYTERHUB_VERSION

USER root

RUN pip3 install --upgrade pip

COPY authenticator /tmp/authenticator
WORKDIR /tmp/authenticator
RUN pip3 install python-pachyderm
RUN pip3 install .

USER ${NB_USER}
WORKDIR /srv/jupyterhub
