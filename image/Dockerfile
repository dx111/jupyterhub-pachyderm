FROM jupyterhub/k8s-hub:0.8.2

USER root
COPY authenticator /tmp/authenticator
WORKDIR /tmp/authenticator
RUN python3 setup.py clean build install

USER ${NB_USER}
WORKDIR /srv/jupyterhub
