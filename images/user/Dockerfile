FROM jupyter/minimal-notebook:45f07a14b422
ARG PACHCTL_VERSION
USER root

RUN apt-get update && apt-get -y install curl
RUN curl -f -o pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${PACHCTL_VERSION}/pachctl_${PACHCTL_VERSION}_amd64.deb
RUN dpkg -i pachctl.deb

ADD config.sh /app/config.sh
RUN chmod +x /app/config.sh

USER $NB_UID

RUN pip install --upgrade pip
RUN pip install python_pachyderm
