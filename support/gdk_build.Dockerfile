# region Final
FROM ubuntu:jammy

RUN apt-get update -y && \
    apt-get install -y gettext-base build-essential python3-pip

COPY ./component/requirements.txt /tmp/requirements.txt

RUN mkdir -p /asset/component && \
    pip install --target=/asset/component -r /tmp/requirements.txt

COPY ./component /asset/component
COPY ./runtime_scripts /asset/runtime_scripts
# endregion Final
