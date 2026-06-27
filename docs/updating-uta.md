# UTA update procedure

This is the maintainer runbook for building a new UTA/SeqRepo release. It is not
needed to install or use UTA — for that, see the [main README](../README.md).

Requires docker.

## 0. Setup

Make directories:
```
mkdir -p $(pwd)/ncbi-data
mkdir -p $(pwd)/output/artifacts
mkdir -p $(pwd)/output/logs
```

Set variables:
```
export UTA_ETL_OLD_UTA_IMAGE_TAG=uta_20240512
export UTA_ETL_OLD_UTA_VERSION=$UTA_ETL_OLD_UTA_IMAGE_TAG
export UTA_ETL_NEW_UTA_VERSION=uta_20241220
export UTA_ETL_NCBI_DIR=./ncbi-data
export UTA_ETL_WORK_DIR=./output/artifacts
export UTA_ETL_LOG_DIR=./output/logs
```

Provide the previous release's database snapshot. The `uta` service (which
`uta-load` depends on) bind-mounts the prior UTA snapshot, so the file must
exist before you run `uta-load`. Download `${UTA_ETL_OLD_UTA_IMAGE_TAG}.pgd.gz`
from [dl.biocommons.org](https://dl.biocommons.org/uta/) and place it in the
work directory:
```
# expected path: ./output/artifacts/${UTA_ETL_OLD_UTA_IMAGE_TAG}.pgd.gz
```
Note: this path is currently hardcoded to `./output/artifacts/` in
`docker-compose.yml`, so `UTA_ETL_WORK_DIR` cannot be relocated without also
editing that file.

Build the UTA image:
```
docker build --target uta -t uta-update .
```

## 1. Download SeqRepo data
```
docker compose run seqrepo-pull
```

Note: pulling data takes ~30 minutes and requires ~13 GB.
Note: a container called seqrepo will be left behind.

## 2. Extract and transform data from NCBI

Download files from NCBI, extract into intermediate files, and load the nuclear
transcripts into UTA and SeqRepo:
```
docker compose run ncbi-download
docker compose run uta-extract
docker compose run seqrepo-load
docker compose run uta-load
```

Note: `uta-load` depends on the `uta` service, which bind-mounts
`./output/artifacts/${UTA_ETL_OLD_UTA_IMAGE_TAG}.pgd.gz`. Ensure that snapshot
file is in place (see §0 Setup) or the step will fail to start.

UTA has updated and the database has been dumped into a pgd file in `UTA_ETL_WORK_DIR`. SeqRepo has been updated in place.

Loading mitochondrial or manual-splign transcripts is **not** part of the
standard release process. If you need either, see
[Non-standard steps](#non-standard-steps) below and run them after this section
and before §3 (Export SeqRepo).

## 3. Export SeqRepo

The steps above leave the updated SeqRepo data inside the `uta_seqrepo-volume`
Docker volume, not on the host. At this point the volume holds the previous
SeqRepo version plus a writable `master` directory that accumulated the new
sequences. To produce a distributable release you must snapshot `master` into a
new dated version and copy it out of the volume, preserving hard links so that
versions share storage instead of being duplicated.

The commands below mount the SeqRepo volume at its default location
(`/usr/local/share/seqrepo`) and bind `./output/seqrepo` on the host as the copy
destination. Create that directory first if it does not exist:
```
mkdir -p $(pwd)/output/seqrepo
```

### 3A. Create a new snapshot

Start a container with the SeqRepo volume mounted and snapshot `master` into a
new version. By convention the snapshot name is the new UTA version's release
date in `YYYY-MM-DD` form (e.g. `uta_20241220` -> `2024-12-20`):
```
docker run -it --rm --name uta-build \
  --volume $(pwd):/opt/repos/uta \
  --volume uta_seqrepo-volume:/usr/local/share/seqrepo \
  --volume $(pwd)/output/seqrepo:/seqrepo_data \
  --network=host uta-update:latest

# inside the container:
seqrepo snapshot --destination-name "2024-12-20"
```

### 3B. Copy SeqRepo out of the Docker volume

The snapshot still lives inside the volume. Copy it out to the host destination
(`/seqrepo_data`, bound to `./output/seqrepo`). Use `rsync -H` so hard links
between versions are preserved.

The files inside the volume are owned by the container's user. If your target
environment expects specific ownership or permissions, set them before copying.
The `useradd`/`groupadd`/`chown` lines below are an illustrative example —
replace the uid, gid, and names with values appropriate for your systems, or
omit these lines entirely if the defaults are acceptable:
```
docker run -it --rm --name uta-build \
  --volume $(pwd):/opt/repos/uta \
  --volume uta_seqrepo-volume:/usr/local/share/seqrepo \
  --volume $(pwd)/output/seqrepo:/seqrepo_data \
  --network=host uta-update:latest

# inside the container:
# (optional) align ownership/permissions with your destination environment
useradd -u 1000 seqrepo_user
groupadd -g 1000 seqrepo_group
cd /usr/local/share/seqrepo
chown -R seqrepo_user:seqrepo_group *
find . -type d -exec chmod 755 {} +

# copy out of the volume, preserving hard links (-H)
cd /usr/local/share
rsync -avzPH seqrepo/ /seqrepo_data/
```

The exported SeqRepo release now lives in `./output/seqrepo` on the host.

### 3C. Publish to a SeqRepo location using hard links

When placing the new version alongside existing versions at a destination, use
`rsync --link-dest` pointing at the *previous* version so that unchanged
sequence files are hard-linked rather than duplicated. The trailing slashes are
significant:
```
cd output/seqrepo
# --link-dest is the previous version, given relative to the destination
rsync -aP --link-dest=../2024-05-23/ 2024-12-20/ <destination>/seqrepo/2024-12-20/
```

## Non-standard steps

The steps below are **not** part of the standard nuclear-transcript release
process. When one is needed, run it after §2 (Extract and transform) and before
§3 (Export SeqRepo) — each loads additional sequences into SeqRepo and dumps a
new UTA pgd file, so it must complete before the SeqRepo snapshot is taken.

### Mitochondrial transcripts

Mitochondrial transcripts were loaded as a one-time process for the May 2025
release. This is documented for reference and is not expected to be part of
routine updates.
```
docker compose -f docker-compose.yml -f misc/mito-transcripts/docker-compose-mito-extract.yml run mito-extract
docker compose run seqrepo-load
docker compose run uta-load
```

### Manual splign transcripts

This is a special case for loading user-provided transcript alignments instead
of the standard NCBI-derived ones. The workflow expects an input `txdata.yaml`
file and splign alignments. Define their location with the
`UTA_SPLIGN_MANUAL_DIR` environment variable. These paths must exist:
- `$UTA_SPLIGN_MANUAL_DIR/splign-manual/txdata.yaml`
- `$UTA_SPLIGN_MANUAL_DIR/splign-manual/alignments/*.splign`

[txdata.yaml](../loading/data/splign-manual/txdata.yaml) defines the transcripts and their metadata. The [alignments dir](../loading/data/splign-manual/alignments) contains the splign alignments.
To run the workflow:
```
export UTA_SPLIGN_MANUAL_DIR=$(pwd)/loading/data/splign-manual/
docker compose -f docker-compose.yml -f misc/splign-manual/docker-compose-splign-manual.yml run splign-manual
```
