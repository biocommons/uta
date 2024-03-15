#!/bin/bash

set -e

# Input variables
LOCAL_NCBI_DIR=$(pwd)/ncbi
PREVIOUS_UTA_VERSION=uta_20210129b

# 1. Download files for SeqRepo and UTA updates
# Input: N/A
# Output: LOCAL_NCBI_DIR populated with downloaded files
mkdir -p $LOCAL_NCBI_DIR
docker build --file Dockerfile.download --tag ncbi:latest --progress plain .
docker run -it --mount type=bind,source=$LOCAL_NCBI_DIR,target=/data/ncbi ncbi:latest

# 2. Prepare SeqRepo
# Input: TBD
# Output: TBD

# 3. Prepare UTA
docker build --file ../misc/docker/uta.dockerfile --tag uta:$PREVIOUS_UTA_VERSION --build-arg uta_version=$PREVIOUS_UTA_VERSION ../misc/docker

# 4. Update UTA and SeqRepo
# Input: LOCAL_NCBI_DIR populated with downloaded files
# Input: PREVIOUS_UTA_VERSION
# Output: Updated SeqRepo (updated in place)
# Output: Updated UTA as a database dump
docker build --file ../Dockerfile --tag uta-update:latest ..
previous_uta_version=$PREVIOUS_UTA_VERSION docker compose -f docker-compose.uta.yml run --rm uta-update
docker compose -f docker-compose.uta.yml down

# 5. Publish UTA and SeqRepo
