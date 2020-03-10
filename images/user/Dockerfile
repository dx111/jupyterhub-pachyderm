FROM jupyter/minimal-notebook:45f07a14b422
ARG PACHCTL_VERSION
USER root

RUN apt-get update && apt-get -y install curl
RUN curl -f -o pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${PACHCTL_VERSION}/pachctl_${PACHCTL_VERSION}_amd64.deb
RUN dpkg -i pachctl.deb

WORKDIR /app
COPY config.sh .
RUN chmod +x config.sh
COPY pachyderm-widgets pachyderm-widgets

WORKDIR /app/pachyderm-widgets
RUN python setup.py clean build install

USER $NB_UID
WORKDIR /home/jovyan
RUN pip install python-pachyderm
