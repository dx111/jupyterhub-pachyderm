ARG PACHYDERM_VERSION
FROM jupyter/minimal-notebook:45f07a14b422
RUN curl -o /tmp/pachctl.deb -L https://github.com/pachyderm/pachyderm/releases/download/v${PACHYDERM_VERSION}/pachctl_${PACHYDERM_VERSION}_amd64.deb && sudo dpkg -i /tmp/pachctl.deb
RUN pip install --no-cache-dir python-pachyderm
