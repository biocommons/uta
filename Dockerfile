FROM ubuntu:22.04

# set python version and define arguments
ARG python_version="3.10"

# list and install dependencies
ARG dependencies="python${python_version} python3-dev python3-pip rsync git postgresql-client-14"

RUN apt-get update && apt-get install -y $dependencies && apt-get clean

# install pysam, copy code, and run pip install
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN python -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install pysam

ENV APP_HOME="/opt/repos/uta/"

RUN mkdir -p ${APP_HOME}

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

RUN pip install -e .[dev]
