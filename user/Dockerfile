FROM jupyter/minimal-notebook:45f07a14b422
ARG PACHCTL_VERSION
USER root

RUN apt-get update && apt-get -y install curl
RUN curl -f -o pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${PACHCTL_VERSION}/pachctl_${PACHCTL_VERSION}_amd64.deb
RUN dpkg -i pachctl.deb

USER $NB_UID
RUN pip install --upgrade pip
USER root

WORKDIR /app
COPY config.sh .
RUN chmod +x config.sh
COPY pachyderm_extensions pachyderm_extensions

WORKDIR /app/pachyderm_extensions
RUN pip install .
RUN jupyter lab build

USER $NB_UID
WORKDIR /home/jovyan
RUN pip install python-pachyderm
