FROM ubuntu:24.04 AS uta

# set python version and define arguments
ARG python_version="3.12"

# add PostgreSQL apt repository for postgresql-client-17
RUN apt-get update && apt-get install -y curl ca-certificates \
 && install -d /usr/share/postgresql-common/pgdg \
 && curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
 && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt noble-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
 && apt-get clean

# list and install dependencies
ARG dependencies="python${python_version} python3-dev python3-pip rsync git postgresql-client-17 tabix curl"

RUN apt-get update && apt-get install -y $dependencies && apt-get clean

# required on Ubuntu 24.04+ to allow pip to install packages system-wide in containers
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# install pysam, copy code, and run pip install
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip install --upgrade setuptools
RUN pip install pysam

WORKDIR /opt/repos/uta/
COPY pyproject.toml ./
COPY README.md ./
COPY etc ./etc
COPY misc ./misc
COPY sbin ./sbin
COPY src ./src
RUN pip install -e .[dev]


# UTA test image
FROM uta AS uta-test
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install postgresql
COPY tests ./tests
RUN pip install -e .[test]
RUN useradd uta-tester
RUN chown -R uta-tester .
USER uta-tester
