ARG JUPYTERHUB_VERSION
FROM jupyterhub/k8s-hub:$JUPYTERHUB_VERSION

USER root

RUN pip3 install --upgrade pip
# workaround for https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/1444
RUN PYCURL_SSL_LIBRARY=openssl pip3 install --upgrade --no-cache-dir jupyterhub-kubespawner==0.10.1

COPY authenticator /app/authenticator
COPY templates /app/templates
WORKDIR /app/authenticator
RUN pip3 install python-pachyderm
RUN pip3 install .

USER ${NB_USER}
WORKDIR /srv/jupyterhub
