FROM ubuntu:22.04 as uta

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

WORKDIR /opt/repos/uta/
COPY pyproject.toml ./
COPY etc ./etc
COPY sbin ./sbin
COPY src ./src
RUN pip install -e .[dev]


# UTA test image
FROM uta as uta-test
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install postgresql
COPY tests ./tests
RUN pip install -e .[test]
RUN useradd uta-tester
RUN chown -R uta-tester .
USER uta-tester
